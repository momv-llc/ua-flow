"""Shared helpers for executing integration exchanges."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

from backend.models import IntegrationConnection, IntegrationLog
from backend.services.integration_clients import IntegrationError, build_client


class IntegrationInactiveError(RuntimeError):
    """Raised when an exchange is attempted on a disabled connection."""


@dataclass
class IntegrationExecutionResult:
    """Container describing the outcome of an integration exchange."""

    log: IntegrationLog
    status_code: int
    body: Any


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
    connection.last_sync_status = "Success" if status == "success" else f"Failed ({status})"
    db.add(log)
    db.add(connection)
    db.commit()
    db.refresh(log)
    db.refresh(connection)
    return log


def execute_sync(
    db: Session,
    connection: IntegrationConnection,
    payload: Dict[str, Any] | None,
    *,
    context: str,
) -> IntegrationExecutionResult:
    """Perform a sync exchange and persist a log entry."""

    if not connection.is_active:
        raise IntegrationInactiveError("Integration connection is disabled")

    client = build_client(connection.integration_type, connection.settings)
    payload = payload or {}

    try:
        result = client.sync(payload)
    except IntegrationError as exc:
        _record_log(
            db,
            connection,
            "error",
            {"action": "sync", "payload": payload, "context": context, "error": str(exc)},
            0,
        )
        raise

    log = _record_log(
        db,
        connection,
        "success",
        {"action": "sync", "payload": payload, "context": context, "response": result.body},
        result.status_code,
    )
    return IntegrationExecutionResult(log=log, status_code=result.status_code, body=result.body)


def execute_ping(
    db: Session,
    connection: IntegrationConnection,
    *,
    context: str,
) -> IntegrationExecutionResult:
    """Ping the remote endpoint and log the handshake."""

    client = build_client(connection.integration_type, connection.settings)

    try:
        result = client.ping()
    except IntegrationError as exc:
        _record_log(
            db,
            connection,
            "error",
            {"action": "test", "context": context, "error": str(exc)},
            0,
        )
        raise

    log = _record_log(
        db,
        connection,
        "success",
        {"action": "test", "context": context, "response": result.body},
        result.status_code,
    )
    return IntegrationExecutionResult(log=log, status_code=result.status_code, body=result.body)

