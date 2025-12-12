"""Endpoints for time tracking, budgeting, and invoicing."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, require_roles
from models import (
    Invoice,
    InvoiceItem,
    InvoiceStatus,
    Project,
    ProjectBudget,
    ProjectExpense,
    Task,
    User,
    UserRate,
    Worklog,
)
from schemas import (
    InvoiceCreate,
    InvoiceOut,
    ProjectBudgetOut,
    ProjectBudgetUpsert,
    ProjectExpenseCreate,
    ProjectExpenseOut,
    UserRateCreate,
    UserRateOut,
    WorklogCreate,
    WorklogOut,
)
from services.timebilling_service import calculate_project_actuals, recalculate_invoice_totals

router = APIRouter()


# ---------------------------------------------------------------------------
# Worklogs
# ---------------------------------------------------------------------------


@router.post("/worklogs", response_model=WorklogOut, status_code=201)
def create_worklog(
    payload: WorklogCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = db.get(Project, payload.project_id) if payload.project_id else None
    task = db.get(Task, payload.task_id) if payload.task_id else None
    worklog = Worklog(
        user_id=user.id,
        task_id=task.id if task else None,
        project_id=project.id if project else None,
        spent_hours=payload.spent_hours,
        work_date=payload.work_date,
        description=payload.description or "",
        created_by=user.id,
    )
    db.add(worklog)
    db.commit()
    db.refresh(worklog)
    return worklog


@router.get("/worklogs/my", response_model=List[WorklogOut])
def list_my_worklogs(
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    task_id: Optional[int] = None,
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Worklog).filter(Worklog.user_id == user.id)
    if from_date:
        query = query.filter(Worklog.work_date >= from_date)
    if to_date:
        query = query.filter(Worklog.work_date <= to_date)
    if task_id:
        query = query.filter(Worklog.task_id == task_id)
    if project_id:
        query = query.filter(Worklog.project_id == project_id)
    return query.order_by(Worklog.work_date.desc()).all()


@router.get("/worklogs/project/{project_id}", response_model=List[WorklogOut])
def project_worklogs(
    project_id: int,
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    task_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("manager", "admin")),
):
    query = db.query(Worklog).filter(Worklog.project_id == project_id)
    if from_date:
        query = query.filter(Worklog.work_date >= from_date)
    if to_date:
        query = query.filter(Worklog.work_date <= to_date)
    if task_id:
        query = query.filter(Worklog.task_id == task_id)
    return query.order_by(Worklog.work_date.desc()).all()


@router.delete("/worklogs/{worklog_id}", status_code=204)
def delete_worklog(
    worklog_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    worklog = db.get(Worklog, worklog_id)
    if not worklog:
        raise HTTPException(status_code=404, detail="Worklog not found")
    if worklog.user_id != user.id and user.role not in {"admin", "manager"}:
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(worklog)
    db.commit()
    return None


# ---------------------------------------------------------------------------
# Rates
# ---------------------------------------------------------------------------


@router.post("/rates", response_model=UserRateOut, status_code=201)
def create_rate(
    payload: UserRateCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    rate = UserRate(**payload.model_dump())
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


@router.get("/rates/user/{user_id}", response_model=List[UserRateOut])
def list_rates(user_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in {"admin", "manager"} and user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return (
        db.query(UserRate)
        .filter(UserRate.user_id == user_id)
        .order_by(UserRate.valid_from.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# Budgets & Expenses
# ---------------------------------------------------------------------------


@router.post("/budget", response_model=ProjectBudgetOut)
def upsert_budget(
    payload: ProjectBudgetUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("manager", "admin")),
):
    budget = db.query(ProjectBudget).filter(ProjectBudget.project_id == payload.project_id).first()
    if budget:
        for field, value in payload.model_dump().items():
            setattr(budget, field, value)
    else:
        budget = ProjectBudget(**payload.model_dump())
        db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.get("/budget/{project_id}")
def get_budget_summary(
    project_id: int,
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    budget = db.query(ProjectBudget).filter(ProjectBudget.project_id == project_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    actuals = calculate_project_actuals(db, project_id, from_date, to_date)
    return {"budget": budget, "actuals": actuals}


@router.post("/expenses", response_model=ProjectExpenseOut, status_code=201)
def create_expense(
    payload: ProjectExpenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("manager", "admin")),
):
    expense = ProjectExpense(**payload.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/expenses/{project_id}", response_model=List[ProjectExpenseOut])
def list_expenses(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in {"admin", "manager"}:
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    return (
        db.query(ProjectExpense)
        .filter(ProjectExpense.project_id == project_id)
        .order_by(ProjectExpense.expense_date.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------


def _generate_external_id(db: Session, now: datetime) -> str:
    prefix = now.strftime("INV-%Y%m")
    count = db.query(Invoice).filter(Invoice.external_id.like(f"{prefix}%")).count()
    return f"{prefix}-{count + 1:03d}"


@router.post("/invoices", response_model=InvoiceOut, status_code=201)
def create_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("manager", "admin")),
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Invoice must have items")
    now = datetime.utcnow()
    invoice = Invoice(
        project_id=payload.project_id,
        external_id=_generate_external_id(db, now),
        client_name=payload.client_name,
        client_details=payload.client_details or "",
        currency=payload.currency,
        issue_date=payload.issue_date,
        due_date=payload.due_date,
        created_by=user.id,
    )
    for item_data in payload.items:
        invoice.items.append(
            InvoiceItem(
                description=item_data.description,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                line_total=item_data.quantity * item_data.unit_price,
            )
        )
    recalculate_invoice_totals(invoice, payload.tax_percent)
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/invoices", response_model=List[InvoiceOut])
def list_invoices(
    project_id: Optional[int] = None,
    status: Optional[InvoiceStatus] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Invoice)
    if project_id:
        query = query.filter(Invoice.project_id == project_id)
    if status:
        query = query.filter(Invoice.status == status)
    if from_date:
        query = query.filter(Invoice.issue_date >= from_date)
    if to_date:
        query = query.filter(Invoice.issue_date <= to_date)
    return query.order_by(Invoice.issue_date.desc()).all()


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.post("/invoices/{invoice_id}/status", response_model=InvoiceOut)
def update_invoice_status(
    invoice_id: int,
    status: InvoiceStatus,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("manager", "admin")),
):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice.status = status
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/invoices/{invoice_id}/pdf")
def invoice_pdf_stub(invoice_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"invoice_id": invoice.id, "pdf_url": f"https://example.com/invoices/{invoice.external_id}.pdf"}
