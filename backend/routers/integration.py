"""Integration hub endpoints for external connectors and marketplace."""

from __future__ import annotations

import json
import os
from datetime import datetime
from hashlib import sha256
import hmac
from typing import Any, Dict, Iterable

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import audit_log, get_current_user, require_roles
from backend.models import (
    IntegrationConnection,
    IntegrationLog,
    MarketplaceApp,
    MarketplaceInstallation,
    User,
)
from backend.schemas import (
    IntegrationActionResult,
    IntegrationCreate,
    IntegrationLogOut,
    IntegrationOut,
    IntegrationUpdate,
    MarketplaceAppOut,
    MarketplaceInstallOut,
)
from backend.services.integration_clients import IntegrationError, build_client


router = APIRouter()

DEFAULT_MARKETPLACE_APPS: Iterable[Dict[str, Any]] = (
    {
        "slug": "telegram-support",
        "name": "Telegram Support Bot",
        "description": "Оповещения о тикетах и чат с пользователями через Telegram.",
        "category": "communication",
        "website": "https://t.me/",
        "icon": "telegram",
    },
    {
        "slug": "diia-sign",
        "name": "Diia Sign",
        "description": "Интеграция с Дія для проверки и подписи документов.",
        "category": "compliance",
        "website": "https://diia.gov.ua/",
        "icon": "shield",
    },
    {
        "slug": "prozorro-tracker",
        "name": "Prozorro Tracker",
        "description": "Мониторинг закупок и объявлений из Prozorro.",
        "category": "analytics",
        "website": "https://prozorro.gov.ua/",
        "icon": "chart",
    },
)

WEBHOOK_PREVIEW_SECRET = os.getenv("UA_FLOW_WEBHOOK_SECRET", "ua-flow-preview")


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _serialize_connection(conn: IntegrationConnection) -> IntegrationOut:
    status = conn.last_sync_status or ("Active" if conn.is_active else "Disabled")
    payload = {
        "id": conn.id,
        "name": conn.name,
        "integration_type": conn.integration_type,
        "description": conn.description or "",
        "is_active": bool(conn.is_active),
        "status": status,
        "last_synced_at": conn.last_synced_at,
        "settings": conn.settings or {},
        "created_at": conn.created_at,
        "updated_at": conn.updated_at,
    }
    return IntegrationOut.model_validate(payload)


def _record_log(
    db: Session,
    connection: IntegrationConnection,
    status: str,
    payload: Dict[str, Any],
    response_code: int,
    direction: str = "outbound",
) -> IntegrationLog:
    serialized = json.dumps(payload, ensure_ascii=False)[:2000]
    log = IntegrationLog(
        connection_id=connection.id,
        direction=direction,
        status=status,
        payload=serialized,
        response_code=response_code,
    )
    connection.last_synced_at = datetime.utcnow()
    if status == "success":
        connection.last_sync_status = "Success"
    else:
        connection.last_sync_status = f"Failed ({status})"
    db.add(log)
    db.add(connection)
    db.commit()
    db.refresh(log)
    db.refresh(connection)
    return log


def _ensure_marketplace_catalog(db: Session) -> None:
    if db.query(MarketplaceApp).count():
        return
    for item in DEFAULT_MARKETPLACE_APPS:
        db.add(MarketplaceApp(**item))
    db.commit()


def _serialize_marketplace_app(
    app: MarketplaceApp, installation: MarketplaceInstallation | None
) -> MarketplaceAppOut:
    return MarketplaceAppOut(
        id=app.id,
        slug=app.slug,
        name=app.name,
        description=app.description,
        category=app.category,
        website=app.website or None,
        icon=app.icon or None,
        installed=bool(installation),
        installed_at=installation.installed_at if installation else None,
    )


# ---------------------------------------------------------------------------
# Integration connections
# ---------------------------------------------------------------------------


@router.get("/connections", response_model=list[IntegrationOut])
def list_integrations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role not in {"admin", "integrator"}:
        raise HTTPException(status_code=403, detail="Integrator role required")
    connections = db.query(IntegrationConnection).order_by(IntegrationConnection.name).all()
    return [_serialize_connection(conn) for conn in connections]


@router.post("/connections", response_model=IntegrationOut, status_code=201)
def create_integration(
    payload: IntegrationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "integrator")),
):
    conn = IntegrationConnection(
        name=payload.name,
        integration_type=payload.integration_type,
        description=payload.description or "",
        settings=payload.settings or {},
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
