"""Service desk and support ticket APIs."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytz
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import audit_log, get_current_user, require_roles
from backend.models import SupportComment, SupportTicket, TicketPriority, TicketStatus, User
from backend.schemas import (
    TicketCommentCreate,
    TicketCommentOut,
    TicketCreate,
    TicketOut,
    TicketUpdate,
)


router = APIRouter()


SLA_WINDOWS = {
    TicketPriority.low: timedelta(hours=48),
    TicketPriority.normal: timedelta(hours=24),
    TicketPriority.high: timedelta(hours=8),
    TicketPriority.urgent: timedelta(hours=2),
}


def _assign_sla(priority: TicketPriority) -> datetime:
    return datetime.now(tz=pytz.UTC) + SLA_WINDOWS.get(priority, timedelta(hours=24))


@router.get("/", response_model=list[TicketOut])
def list_tickets(
    status: TicketStatus | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(SupportTicket)
    if user.role not in {"admin", "moderator"}:
        query = query.filter(
            (SupportTicket.requester_id == user.id) | (SupportTicket.assignee_id == user.id)
        )
    if status:
        query = query.filter(SupportTicket.status == status)
    return query.order_by(SupportTicket.created_at.desc()).all()


@router.post("/", response_model=TicketOut, status_code=201)
def create_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    ticket = SupportTicket(
        subject=payload.subject,
        body=payload.body,
        priority=payload.priority,
        channel=payload.channel,
        sla_due=_assign_sla(payload.priority),
        requester_id=user.id,
        updated_at=now,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    audit_log(user, "support.ticket_created", {"ticket_id": ticket.id}, db)
    return ticket


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ticket = db.get(SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if user.role not in {"admin", "moderator"} and user.id not in {ticket.requester_id, ticket.assignee_id}:
        raise HTTPException(status_code=403, detail="Forbidden")
    return ticket


@router.put("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket = db.get(SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if user.role not in {"admin", "moderator"} and ticket.requester_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(ticket, field, value)
    if "priority" in data:
        ticket.sla_due = _assign_sla(ticket.priority)
    if "status" in data and data["status"] in {TicketStatus.resolved, TicketStatus.closed}:
        ticket.resolved_at = datetime.utcnow()
    elif "status" in data and data["status"] in {TicketStatus.new, TicketStatus.in_progress, TicketStatus.waiting}:
        ticket.resolved_at = None
    ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    audit_log(user, "support.ticket_updated", {"ticket_id": ticket.id}, db)
    return ticket


@router.post("/{ticket_id}/assign/{assignee_id}", response_model=TicketOut)
def assign_ticket(
    ticket_id: int,
    assignee_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "moderator")),
):
    ticket = db.get(SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if not db.get(User, assignee_id):
        raise HTTPException(status_code=404, detail="Assignee not found")
    ticket.assignee_id = assignee_id
    ticket.status = TicketStatus.in_progress
    ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    audit_log(user, "support.ticket_assigned", {"ticket_id": ticket.id, "assignee_id": assignee_id}, db)
    return ticket


@router.post("/{ticket_id}/comments", response_model=TicketCommentOut, status_code=201)
def add_comment(
    ticket_id: int,
    payload: TicketCommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket = db.get(SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if user.role not in {"admin", "moderator"} and user.id not in {ticket.requester_id, ticket.assignee_id}:
        raise HTTPException(status_code=403, detail="Forbidden")

    comment = SupportComment(
        ticket_id=ticket.id,
        author_id=user.id,
        message=payload.message,
        via=payload.via,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    audit_log(
        user,
        "support.comment_added",
        {"ticket_id": ticket.id, "comment_id": comment.id},
        db,
    )
    return comment
