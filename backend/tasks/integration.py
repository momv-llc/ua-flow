"""Celery tasks for integration exchanges."""

from __future__ import annotations

from typing import Any, Dict

from celery.utils.log import get_task_logger

from backend.celery_app import celery_app
from backend.database import SessionLocal
from backend.models import IntegrationConnection
from backend.services.integration_runner import (
    IntegrationExecutionResult,
    IntegrationInactiveError,
    execute_sync,
)
from backend.services.integration_clients import IntegrationError

logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(IntegrationError,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_kwargs={"max_retries": 5},
    name="backend.tasks.integration.run_sync",
)
def run_integration_sync(self, connection_id: int, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = payload or {}
    logger.info("Processing integration sync", extra={"connection_id": connection_id})

    with SessionLocal() as session:
        connection = session.get(IntegrationConnection, connection_id)
        if not connection:
            raise ValueError(f"Integration connection {connection_id} not found")
        if not connection.is_active:
            raise IntegrationInactiveError("Integration connection is disabled")

        outcome: IntegrationExecutionResult = execute_sync(
            session,
            connection,
            payload,
            context="worker",
        )

        result = {
            "connection_id": connection_id,
            "log_id": outcome.log.id,
            "status_code": outcome.status_code,
            "response": outcome.body,
        }
        logger.info(
            "Integration sync completed",
            extra={"connection_id": connection_id, "log_id": outcome.log.id},
        )
        return result


def enqueue_integration_sync(connection_id: int, payload: Dict[str, Any] | None = None):
    """Schedule a Celery job and return the AsyncResult handle."""

    payload = payload or {}
    return run_integration_sync.delay(connection_id, payload)

