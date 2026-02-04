"""Analytical endpoints powering dashboards."""

from __future__ import annotations

from collections import Counter
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, require_roles
from models import Project, SupportTicket, Task, TaskStatus, TicketStatus, User
from services.timebilling_service import calculate_project_actuals


router = APIRouter()


@router.get("/velocity")
def velocity(db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "moderator"))):
    tasks = db.query(Task).filter(Task.status == TaskStatus.done).all()
    by_project = Counter(task.project_id for task in tasks if task.project_id)
    return {str(project_id): count for project_id, count in by_project.items()}


@router.get("/tickets/heatmap")
def ticket_heatmap(db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "moderator"))):
    tickets = db.query(SupportTicket).all()
    heatmap = Counter((ticket.priority.value, ticket.status.value) for ticket in tickets)
    return {f"{priority}:{status}": count for (priority, status), count in heatmap.items()}


@router.get("/workload")
def workload(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned = db.query(Task).filter(Task.assignee_id == user.id, Task.status != TaskStatus.done).count()
    overdue = (
        db.query(Task)
        .filter(
            Task.assignee_id == user.id,
            Task.due_date.isnot(None),
            Task.due_date < date.today(),
            Task.status != TaskStatus.done,
        )
        .count()
    )
    return {"open": owned, "overdue": overdue}


@router.get("/timebilling/summary")
def timebilling_summary(
    project_id: int,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    actuals = calculate_project_actuals(db, project_id, from_date, to_date)
    return {
        "project_id": project_id,
        "actual_cost": actuals["cost_total"],
        "expenses_total": actuals["expenses_total"],
        "hours_total": actuals["hours_total"],
        "total_with_expenses": actuals["total_with_expenses"],
    }
