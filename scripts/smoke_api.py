"""Minimal end-to-end smoke checks for the UA FLOW API."""

from __future__ import annotations

import os
import sys
import uuid
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

# Force a local SQLite database so the smoke test does not depend on external
# PostgreSQL services when executed in CI or developer machines.
os.environ.setdefault("DATABASE_URL", "sqlite:///./smoke_test.db")
os.environ.setdefault("CELERY_EAGER", "1")

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.database import Base, SessionLocal, engine  # noqa: E402  # pylint: disable=wrong-import-position
from backend.models import (  # noqa: E402  # pylint: disable=wrong-import-position
    PaymentGateway,
    PaymentMethodType,
    PaymentPlan,
    PaymentPlanInterval,
)
import backend.models  # noqa: F401,E402  # pylint: disable=unused-import,wrong-import-position
from backend.main import app  # noqa: E402  # pylint: disable=wrong-import-position


def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def ensure_docs_available(client: TestClient) -> None:
    response = client.get("/api/openapi.json")
    response.raise_for_status()


def run_auth_flow(client: TestClient) -> tuple[str, int]:
    email = f"smoke-{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPass123!"

    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    register.raise_for_status()

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    login.raise_for_status()
    token = login.json()["access_token"]

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    me.raise_for_status()
    user_id = me.json()["id"]

    return token, user_id


def seed_billing_plan() -> int:
    with SessionLocal() as session:
        plan = PaymentPlan(
            name="UA FLOW Team",
            description="Місячна підписка для команди",
            price=Decimal("4999.00"),
            currency="UAH",
            interval=PaymentPlanInterval.monthly,
            trial_days=14,
            features=[
                "10 користувачів",
                "Інтеграції з 1С та Дією",
                "Сервіс-деск з SLA",
            ],
        )
        session.add(plan)
        session.commit()
        session.refresh(plan)
        return plan.id


def run_billing_flow(client: TestClient, token: str, plan_id: int) -> None:
    headers = {"Authorization": f"Bearer {token}"}

    method = client.post(
        "/api/v1/billing/methods",
        json={
            "method_type": PaymentMethodType.card.value,
            "gateway": PaymentGateway.liqpay.value,
            "label": "Test LiqPay",
            "details": {"card_number": "4242424242424242", "expires": "12/28"},
        },
        headers=headers,
    )
    method.raise_for_status()
    method_id = method.json()["id"]

    subscription = client.post(
        "/api/v1/billing/subscriptions",
        json={"plan_id": plan_id, "payment_method_id": method_id, "auto_renew": True},
        headers=headers,
    )
    subscription.raise_for_status()

    checkout = client.post(
        "/api/v1/billing/checkout",
        json={"plan_id": plan_id, "payment_method_id": method_id},
        headers=headers,
    )
    checkout.raise_for_status()


def main() -> None:
    reset_database()
    client = TestClient(app)

    ensure_docs_available(client)
    plan_id = seed_billing_plan()
    token, _ = run_auth_flow(client)
    run_billing_flow(client, token, plan_id)

    db_path = Path("smoke_test.db")
    if db_path.exists():
        db_path.unlink()

    print("UA FLOW API smoke test passed")


if __name__ == "__main__":
    main()
