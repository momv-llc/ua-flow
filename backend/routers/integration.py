"""Integration hub endpoints for external connectors and marketplace."""

from __future__ import annotations

import json
import os
from hashlib import sha256
import hmac
from typing import Any, Dict, Iterable

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.celery_app import celery_app
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
    IntegrationSandboxExchange,
    IntegrationSandboxOut,
    IntegrationTaskStatus,
    IntegrationUpdate,
    MarketplaceAppOut,
    MarketplaceInstallOut,
)
from backend.services.integration_runner import (
    IntegrationInactiveError,
    execute_ping,
    execute_sync,
)
from backend.services.integration_clients import IntegrationError
from backend.services.integration_sandboxes import list_sandboxes, simulate_exchange
from backend.tasks.integration import enqueue_integration_sync


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
    return _serialize_connection(conn)


@router.put("/connections/{connection_id}", response_model=IntegrationOut)
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

    try:
        outcome = execute_ping(db, conn, context="api")
    except IntegrationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    audit_log(user, "integration.tested", {"connection_id": conn.id}, db)
    return IntegrationActionResult(status="ok", details={"response": outcome.body})


@router.post(
    "/connections/{connection_id}/sync",
    response_model=IntegrationActionResult,
    status_code=200,
)
def trigger_sync(
    connection_id: int,
    payload: Dict[str, Any],
    mode: str = Query("async", regex="^(async|sync)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "integrator")),
):
    conn = db.get(IntegrationConnection, connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Integration not found")
    if not conn.is_active:
        raise HTTPException(status_code=400, detail="Integration disabled")

    if mode == "sync":
        try:
            outcome = execute_sync(db, conn, payload or {}, context="api-sync")
        except IntegrationInactiveError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except IntegrationError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        audit_log(user, "integration.synced", {"connection_id": conn.id, "mode": "sync"}, db)
        return IntegrationActionResult(
            status="success",
            details={"status_code": outcome.status_code, "response": outcome.body},
        )

    job = enqueue_integration_sync(conn.id, payload or {})
    audit_log(
        user,
        "integration.synced",  # reuse event name for queue scheduling
        {"connection_id": conn.id, "mode": "async", "task_id": job.id},
        db,
    )

    if celery_app.conf.task_always_eager:
        result = job.get()
        return IntegrationActionResult(status="success", details={"task_id": job.id, "response": result})

    return IntegrationActionResult(status="queued", details={"task_id": job.id})


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


@router.get("/tasks/{task_id}", response_model=IntegrationTaskStatus)
def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    details: Dict[str, Any] | None = None
    error: str | None = None

    if result.successful():
        try:
            details = result.get()
        except Exception as exc:  # pragma: no cover - defensive
            error = str(exc)
    elif result.failed():
        error = str(result.result)

    return IntegrationTaskStatus(
        task_id=task_id,
        state=result.state,
        retries=getattr(result, "retries", 0) or 0,
        details=details,
        error=error,
    )


@router.get(
    "/sandboxes",
    response_model=list[IntegrationSandboxOut],
)
def list_sandbox_profiles(
    user: User = Depends(require_roles("admin", "integrator", "moderator")),
):
    return [
        IntegrationSandboxOut(
            slug=item.slug,
            title=item.title,
            description=item.description,
            request_example=item.request_example,
            response_example=item.response_example,
            notes=item.notes,
        )
        for item in list_sandboxes()
    ]


@router.post(
    "/sandboxes/{slug}",
    response_model=IntegrationSandboxExchange,
)
def run_sandbox(
    slug: str,
    payload: Dict[str, Any],
    user: User = Depends(require_roles("admin", "integrator", "moderator")),
):
    try:
        response = simulate_exchange(slug, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Sandbox not found") from exc
    return IntegrationSandboxExchange(**response)


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
