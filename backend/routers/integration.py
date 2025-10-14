"""Integration hub endpoints for external connectors."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import audit_log, get_current_user, require_roles
from models import IntegrationConnection, IntegrationLog, IntegrationType, User
from schemas import IntegrationCreate, IntegrationLogOut, IntegrationOut, IntegrationUpdate


router = APIRouter()


@router.get("/", response_model=list[IntegrationOut])
def list_integrations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(IntegrationConnection)
    if user.role not in {"admin", "integrator"}:
        raise HTTPException(status_code=403, detail="Integrator role required")
    return query.all()


@router.post("/", response_model=IntegrationOut, status_code=201)
def create_integration(
    payload: IntegrationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "integrator")),
):
    conn = IntegrationConnection(
        name=payload.name,
        integration_type=payload.integration_type,
        settings=payload.settings,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    audit_log(user, "integration.created", {"connection_id": conn.id}, db)
    return conn


@router.put("/{connection_id}", response_model=IntegrationOut)
def update_integration(
    connection_id: int,
    payload: IntegrationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "integrator")),
):
    conn = db.get(IntegrationConnection, connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Integration not found")

    data = payload.model_dump(exclude_unset=True)
    if "is_active" in data:
        conn.is_active = 1 if data["is_active"] else 0
    if "name" in data:
        conn.name = data["name"]
    if "settings" in data:
        conn.settings = data["settings"]
    db.commit()
    db.refresh(conn)
    audit_log(user, "integration.updated", {"connection_id": conn.id}, db)
    return conn


@router.post("/{connection_id}/sync", response_model=IntegrationLogOut, status_code=201)
def trigger_sync(
    connection_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "integrator")),
):
    conn = db.get(IntegrationConnection, connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Integration not found")
    if not conn.is_active:
        raise HTTPException(status_code=400, detail="Integration disabled")

    # Simulate an exchange by storing the payload as JSON.
    serialized = json.dumps(payload, ensure_ascii=False)
    log = IntegrationLog(
        connection_id=conn.id,
        direction="outbound",
        status="success",
        payload=serialized[:2000],
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    audit_log(
        user,
        "integration.sync",
        {"connection_id": conn.id, "log_id": log.id},
        db,
    )
    return log


@router.get("/{connection_id}/logs", response_model=list[IntegrationLogOut])
def list_logs(
    connection_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "integrator")),
):
    conn = db.get(IntegrationConnection, connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Integration not found")
    return (
        db.query(IntegrationLog)
        .filter(IntegrationLog.connection_id == connection_id)
        .order_by(IntegrationLog.created_at.desc())
        .all()
    )
