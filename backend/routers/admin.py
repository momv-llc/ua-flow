"""Administrative and governance endpoints."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import audit_log, require_roles
from backend.models import AuditLog as AuditLogModel
from backend.models import Project, SupportTicket, SystemSetting, Task, TicketStatus, User
from backend.schemas import DashboardMetric, RoleUpdate, UserOut


router = APIRouter()


@router.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users/{user_id}/role", response_model=UserOut)
def set_user_role(
    user_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_roles("admin")),
):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.role = payload.role
    db.commit()
    db.refresh(target)
    audit_log(current, "admin.role_set", {"user_id": user_id, "role": payload.role}, db)
    return target


@router.get("/audit", response_model=list[dict])
def audit_trail(db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "moderator"))):
    logs = (
        db.query(AuditLogModel)
        .order_by(AuditLogModel.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": log.id,
            "actor_id": log.actor_id,
            "action": log.action,
            "metadata": log.metadata,
            "created_at": log.created_at,
        }
        for log in logs
    ]


@router.get("/metrics", response_model=list[DashboardMetric])
def metrics(db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "moderator"))):
    total_projects = db.query(Project).count()
    total_tasks = db.query(Task).count()
    open_tickets = db.query(SupportTicket).filter(SupportTicket.status != TicketStatus.resolved).count()
    admins = db.query(User).filter(User.role == "admin").count()
    return [
        DashboardMetric(name="Projects", value=total_projects),
        DashboardMetric(name="Tasks", value=total_tasks),
        DashboardMetric(name="Open Tickets", value=open_tickets),
        DashboardMetric(name="Admins", value=admins),
    ]


@router.get("/settings")
def get_settings(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    records = db.query(SystemSetting).all()
    return {record.key: record.value for record in records}


@router.post("/settings/{key}")
def set_setting(
    key: str,
    value: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    record = db.get(SystemSetting, key)
    if record:
        record.value = value
    else:
        record = SystemSetting(key=key, value=value)
        db.add(record)
    db.commit()
    audit_log(user, "admin.setting_updated", {"key": key}, db)
    return {"key": key, "value": value}
