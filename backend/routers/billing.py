"""Billing and subscription endpoints for UA FLOW."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import audit_log, get_current_user, require_roles
from backend.models import (
    PaymentGateway,
    PaymentMethod,
    PaymentMethodType,
    PaymentPlan,
    PaymentPlanInterval,
    PaymentTransaction,
    Subscription,
    SubscriptionStatus,
    TransactionStatus,
    User,
)
from backend.schemas import (
    CheckoutRequest,
    CheckoutResponse,
    PaymentMethodCreate,
    PaymentMethodOut,
    PaymentPlanCreate,
    PaymentPlanOut,
    PaymentTransactionOut,
    SubscriptionCreate,
    SubscriptionOut,
    TransactionStatusUpdate,
)


router = APIRouter()


def _calculate_period_end(start: datetime, interval: PaymentPlanInterval) -> datetime | None:
    """Return the billing period end date based on the plan interval."""

    if interval == PaymentPlanInterval.monthly:
        return start + timedelta(days=30)
    if interval == PaymentPlanInterval.quarterly:
        return start + timedelta(days=90)
    if interval == PaymentPlanInterval.yearly:
        return start + timedelta(days=365)
    return None


def _sanitize_details(method_type: PaymentMethodType, details: dict | None) -> dict:
    """Remove sensitive fields and enrich card metadata when possible."""

    details = dict(details or {})
    if method_type == PaymentMethodType.card:
        card_number = details.pop("card_number", "")
        if card_number:
            digits = "".join(ch for ch in str(card_number) if ch.isdigit())
            if digits:
                details["last4"] = digits[-4:]
        details.setdefault("brand", details.get("brand", "card"))
        details.setdefault("expires", details.get("expires", ""))
    return details


@router.get("/plans", response_model=list[PaymentPlanOut])
def list_plans(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(PaymentPlan).order_by(PaymentPlan.price)
    if not include_inactive or user.role not in {"admin", "moderator"}:
        query = query.filter(PaymentPlan.is_active.is_(True))
    return query.all()


@router.post("/plans", response_model=PaymentPlanOut)
def create_plan(
    payload: PaymentPlanCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    plan = PaymentPlan(**payload.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    audit_log(user, "billing.plan_created", {"plan_id": plan.id}, db)
    return plan


@router.put("/plans/{plan_id}", response_model=PaymentPlanOut)
def update_plan(
    plan_id: int,
    payload: PaymentPlanCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    plan = db.get(PaymentPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for field, value in payload.model_dump().items():
        setattr(plan, field, value)
    db.commit()
    db.refresh(plan)
    audit_log(user, "billing.plan_updated", {"plan_id": plan.id}, db)
    return plan


@router.get("/methods", response_model=list[PaymentMethodOut])
def list_methods(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(PaymentMethod)
        .filter(PaymentMethod.user_id == user.id)
        .order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc())
        .all()
    )


@router.post("/methods", response_model=PaymentMethodOut)
def create_method(
    payload: PaymentMethodCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sanitized = _sanitize_details(payload.method_type, payload.details)
    existing_default = (
        db.query(PaymentMethod)
        .filter(PaymentMethod.user_id == user.id, PaymentMethod.is_default.is_(True))
        .first()
    )
    method = PaymentMethod(
        user_id=user.id,
        method_type=payload.method_type,
        gateway=payload.gateway,
        label=payload.label,
        details=sanitized,
        is_default=existing_default is None,
    )
    db.add(method)
    db.commit()
    db.refresh(method)
    audit_log(user, "billing.method_added", {"method_id": method.id}, db)
    return method


@router.post("/methods/{method_id}/default", response_model=PaymentMethodOut)
def set_default_method(
    method_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    method = (
        db.query(PaymentMethod)
        .filter(PaymentMethod.id == method_id, PaymentMethod.user_id == user.id)
        .first()
    )
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")

    db.query(PaymentMethod).filter(PaymentMethod.user_id == user.id).update(
        {PaymentMethod.is_default: False}
    )
    method.is_default = True
    db.commit()
    db.refresh(method)
    audit_log(user, "billing.method_default", {"method_id": method.id}, db)
    return method


@router.delete("/methods/{method_id}", response_model=dict)
def delete_method(
    method_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    method = (
        db.query(PaymentMethod)
        .filter(PaymentMethod.id == method_id, PaymentMethod.user_id == user.id)
        .first()
    )
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")

    active = (
        db.query(Subscription)
        .filter(
            Subscription.payment_method_id == method.id,
            Subscription.status.in_([SubscriptionStatus.active, SubscriptionStatus.trialing]),
        )
        .count()
    )
    if active:
        raise HTTPException(status_code=400, detail="Cannot remove method with active subscriptions")

    db.delete(method)
    db.commit()
    audit_log(user, "billing.method_deleted", {"method_id": method_id}, db)
    return {"status": "deleted"}


@router.get("/subscriptions", response_model=list[SubscriptionOut])
def list_subscriptions(
    scope: str = "mine",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Subscription)
    if scope == "all" and user.role in {"admin", "moderator"}:
        pass
    else:
        query = query.filter(Subscription.user_id == user.id)
    return query.order_by(Subscription.created_at.desc()).all()


@router.post("/subscriptions", response_model=SubscriptionOut)
def create_subscription(
    payload: SubscriptionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    plan = db.get(PaymentPlan, payload.plan_id)
    if not plan or (not plan.is_active and user.role not in {"admin", "moderator"}):
        raise HTTPException(status_code=404, detail="Plan not available")

    method_id = payload.payment_method_id
    if method_id is None:
        default_method = (
            db.query(PaymentMethod)
            .filter(PaymentMethod.user_id == user.id, PaymentMethod.is_default.is_(True))
            .first()
        )
        method_id = default_method.id if default_method else None
    elif not (
        db.query(PaymentMethod)
        .filter(PaymentMethod.id == method_id, PaymentMethod.user_id == user.id)
        .first()
    ):
        raise HTTPException(status_code=400, detail="Payment method does not belong to user")

    now = datetime.utcnow()
    trial_ends = now + timedelta(days=plan.trial_days) if plan.trial_days else None
    period_end = _calculate_period_end(now, plan.interval)
    status = SubscriptionStatus.trialing if trial_ends else SubscriptionStatus.active

    subscription = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        payment_method_id=method_id,
        status=status,
        trial_ends_at=trial_ends,
        current_period_end=period_end,
        auto_renew=payload.auto_renew,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    audit_log(user, "billing.subscription_created", {"subscription_id": subscription.id}, db)
    return subscription


@router.post("/subscriptions/{subscription_id}/cancel", response_model=SubscriptionOut)
def cancel_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    subscription = (
        db.query(Subscription)
        .filter(Subscription.id == subscription_id)
        .first()
    )
    if not subscription or (subscription.user_id != user.id and user.role not in {"admin", "moderator"}):
        raise HTTPException(status_code=404, detail="Subscription not found")

    subscription.status = SubscriptionStatus.canceled
    subscription.auto_renew = False
    db.commit()
    db.refresh(subscription)
    audit_log(user, "billing.subscription_canceled", {"subscription_id": subscription.id}, db)
    return subscription


@router.get("/transactions", response_model=list[PaymentTransactionOut])
def list_transactions(
    scope: str = "mine",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(PaymentTransaction)
    if scope == "all" and user.role in {"admin", "moderator"}:
        pass
    else:
        query = query.filter(PaymentTransaction.user_id == user.id)
    return query.order_by(PaymentTransaction.created_at.desc()).limit(100).all()


@router.post("/checkout", response_model=CheckoutResponse)
def start_checkout(
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    plan = db.get(PaymentPlan, payload.plan_id)
    if not plan or (not plan.is_active and user.role not in {"admin", "moderator"}):
        raise HTTPException(status_code=404, detail="Plan not available")

    if payload.payment_method_id:
        method = (
            db.query(PaymentMethod)
            .filter(
                PaymentMethod.id == payload.payment_method_id,
                PaymentMethod.user_id == user.id,
            )
            .first()
        )
        if not method:
            raise HTTPException(status_code=400, detail="Payment method not available")
    else:
        method = (
            db.query(PaymentMethod)
            .filter(PaymentMethod.user_id == user.id)
            .order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc())
            .first()
        )

    gateway = payload.gateway or (method.gateway if method else PaymentGateway.invoice)
    amount = payload.amount_override if payload.amount_override is not None else plan.price
    currency = plan.currency

    reference = f"UA-{uuid4().hex[:10].upper()}"

    transaction = PaymentTransaction(
        reference=reference,
        user_id=user.id,
        plan_id=plan.id,
        subscription_id=None,
        gateway=gateway,
        amount=Decimal(str(amount)),
        currency=currency,
        status=TransactionStatus.pending,
        raw_response={
            "gateway": gateway.value,
            "mode": "sandbox",
            "details": method.details if method else {},
        },
    )

    payment_url: str | None = None
    if gateway in {PaymentGateway.liqpay, PaymentGateway.fondy, PaymentGateway.wayforpay, PaymentGateway.stripe}:
        payment_url = f"https://payments.ua-flow.example/{reference}"
    elif gateway in {PaymentGateway.bank, PaymentGateway.invoice}:
        transaction.raw_response["instructions"] = (
            "Счёт сформирован. Оплатите по реквизитам UA FLOW в течение 5 рабочих дней."
        )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    audit_log(user, "billing.checkout_started", {"reference": reference}, db)

    return CheckoutResponse(
        reference=transaction.reference,
        status=transaction.status,
        amount=transaction.amount,
        currency=transaction.currency,
        payment_url=payment_url,
    )


@router.post("/transactions/{transaction_id}/status", response_model=PaymentTransactionOut)
def update_transaction_status(
    transaction_id: int,
    payload: TransactionStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    transaction = db.get(PaymentTransaction, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    transaction.status = payload.status
    transaction.error_message = payload.error_message
    if payload.status in {TransactionStatus.succeeded, TransactionStatus.refunded}:
        transaction.processed_at = datetime.utcnow()
    db.commit()
    db.refresh(transaction)
    audit_log(user, "billing.transaction_status", {"transaction_id": transaction.id}, db)
    return transaction
