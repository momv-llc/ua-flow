"""Business logic for time tracking, budgeting, and invoicing."""

from __future__ import annotations

from datetime import date
from typing import Dict, Optional

from sqlalchemy.orm import Session

from models import Invoice, InvoiceItem, UserRate, Worklog


def get_effective_user_rate(db: Session, user_id: int, target_date: date) -> Optional[UserRate]:
    """Return the rate active for a user on a given date."""

    query = (
        db.query(UserRate)
        .filter(UserRate.user_id == user_id)
        .filter(UserRate.valid_from <= target_date)
        .filter((UserRate.valid_to.is_(None)) | (UserRate.valid_to >= target_date))
        .order_by(UserRate.valid_from.desc())
    )
    return query.first()


def calculate_project_actuals(
    db: Session, project_id: int, from_date: Optional[date] = None, to_date: Optional[date] = None
) -> Dict[str, int]:
    """Aggregate hours and costs for a project between dates."""

    query = db.query(Worklog).filter(Worklog.project_id == project_id)
    if from_date:
        query = query.filter(Worklog.work_date >= from_date)
    if to_date:
        query = query.filter(Worklog.work_date <= to_date)

    hours_total = 0
    cost_total = 0
    for log in query.all():
        hours_total += log.spent_hours
        rate = get_effective_user_rate(db, log.user_id, log.work_date)
        if rate:
            cost_total += int((log.spent_hours / 60) * rate.hourly_rate)

    expenses_total = 0
    # ProjectExpense import inside function to avoid circular imports
    from models import ProjectExpense  # noqa: WPS433

    expense_query = db.query(ProjectExpense).filter(ProjectExpense.project_id == project_id)
    if from_date:
        expense_query = expense_query.filter(ProjectExpense.expense_date >= from_date)
    if to_date:
        expense_query = expense_query.filter(ProjectExpense.expense_date <= to_date)
    expenses_total = sum(exp.amount for exp in expense_query.all())

    return {
        "hours_total": hours_total,
        "cost_total": cost_total,
        "expenses_total": expenses_total,
        "total_with_expenses": cost_total + expenses_total,
    }


def recalculate_invoice_totals(invoice: Invoice, tax_percent: float | None) -> None:
    """Recompute invoice totals based on items and tax percent."""

    subtotal = sum(item.quantity * item.unit_price for item in invoice.items)
    invoice.subtotal = subtotal
    invoice.tax_amount = int(subtotal * (tax_percent or 0) / 100)
    invoice.total = invoice.subtotal + invoice.tax_amount

    for item in invoice.items:
        item.line_total = item.quantity * item.unit_price
