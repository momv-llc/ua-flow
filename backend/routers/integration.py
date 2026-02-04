"""Integration hub endpoints for external connectors and marketplace."""
"""Integration hub endpoints for external connectors."""

from __future__ import annotations

import json
import os
from datetime import datetime
from hashlib import sha256
import hmac
from typing import Any, Dict, Iterable

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
        conn.is_active = bool(data["is_active"])
    if "name" in data:
        conn.name = data["name"]
    if "description" in data:
        conn.description = data["description"] or ""
    if "settings" in data:
        conn.settings = data["settings"] or {}
    db.add(conn)
    db.commit()
    db.refresh(conn)
    audit_log(user, "integration.updated", {"connection_id": conn.id}, db)
    return _serialize_connection(conn)


@router.post(
    "/connections/{connection_id}/test",
    response_model=IntegrationActionResult,
    status_code=200,
)
def test_integration(
    connection_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "integrator")),
):
    conn = db.get(IntegrationConnection, connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Integration not found")

    client = build_client(conn.integration_type, conn.settings)
    try:
        result = client.ping()
    except IntegrationError as exc:
        _record_log(db, conn, "error", {"action": "test", "error": str(exc)}, 0)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    _record_log(
        db,
        conn,
        "success",
        {"action": "test", "response": result.body},
        result.status_code,
    )
    audit_log(user, "integration.tested", {"connection_id": conn.id}, db)
    return IntegrationActionResult(status="ok", details={"response": result.body})


@router.post(
    "/connections/{connection_id}/sync",
    response_model=IntegrationActionResult,
    status_code=200,
)
def trigger_sync(
    connection_id: int,
    payload: Dict[str, Any],
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
    client = build_client(conn.integration_type, conn.settings)
    try:
        result = client.sync(payload or {})
    except IntegrationError as exc:
        _record_log(
            db,
            conn,
            "error",
            {"action": "sync", "payload": payload, "error": str(exc)},
            0,
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    _record_log(
        db,
        conn,
        "success",
        {"action": "sync", "payload": payload, "response": result.body},
        result.status_code,
    )
    audit_log(user, "integration.synced", {"connection_id": conn.id}, db)
    return IntegrationActionResult(
        status="success",
        details={"status_code": result.status_code, "response": result.body},
    )


@router.get(
    "/connections/{connection_id}/logs",
    response_model=list[IntegrationLogOut],
)
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
            .filter(IntegrationLog.connection_id == connection_id)
            .order_by(IntegrationLog.created_at.desc())
            .all()
    )


# ---------------------------------------------------------------------------
# Marketplace catalog
# ---------------------------------------------------------------------------


@router.get("/marketplace", response_model=list[MarketplaceAppOut])
def list_marketplace_apps(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "integrator", "moderator")),
):
    _ensure_marketplace_catalog(db)
    apps = db.query(MarketplaceApp).order_by(MarketplaceApp.name).all()
    installations = {
        inst.app_id: inst
        for inst in db.query(MarketplaceInstallation).order_by(MarketplaceInstallation.installed_at.desc())
    }
    return [_serialize_marketplace_app(app, installations.get(app.id)) for app in apps]


@router.post(
    "/marketplace/{app_id}/install",
    response_model=MarketplaceInstallOut,
    status_code=201,
)
def install_marketplace_app(
    app_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "integrator")),
):
    _ensure_marketplace_catalog(db)
    app = db.get(MarketplaceApp, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Marketplace application not found")

    installation = (
        db.query(MarketplaceInstallation)
        .filter(MarketplaceInstallation.app_id == app.id)
        .first()
    )
    if installation:
        return MarketplaceInstallOut(
            message="Application already installed",
            app=_serialize_marketplace_app(app, installation),
        )

    installation = MarketplaceInstallation(app_id=app.id, installed_by=user.id, settings={})
    db.add(installation)
    db.commit()
    db.refresh(installation)
    audit_log(user, "marketplace.install", {"app_id": app.id}, db)
    return MarketplaceInstallOut(
        message="Application installed",
        app=_serialize_marketplace_app(app, installation),
    )


# ---------------------------------------------------------------------------
# Webhook utilities
# ---------------------------------------------------------------------------


@router.post("/webhooks/preview")
def preview_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    signature = hmac.new(
        WEBHOOK_PREVIEW_SECRET.encode("utf-8"),
        serialized.encode("utf-8"),
        sha256,
    ).hexdigest()
    return {
        "payload": payload,
        "signature": signature,
        "headers": {
            "X-UA-Flow-Signature": signature,
            "Content-Type": "application/json",
        },
    }
