"""Celery application configuration for UA FLOW."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class CelerySettings(BaseSettings):
    """Runtime configuration pulled from environment variables."""

    broker_url: str = Field(default="redis://localhost:6379/0", alias="BROKER_URL")
    result_backend: str = Field(default="redis://localhost:6379/1", alias="RESULT_BACKEND")
    task_always_eager: bool = Field(default=True, alias="EAGER")
    timezone: str = Field(default="Europe/Kyiv")

    class Config:
        env_prefix = "CELERY_"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_celery_settings() -> CelerySettings:
    return CelerySettings()


settings = get_celery_settings()


from celery import Celery  # noqa: E402  # pylint: disable=wrong-import-position


celery_app = Celery("ua_flow")
celery_app.conf.update(
    broker_url=settings.broker_url,
    result_backend=settings.result_backend,
    task_default_queue="ua_flow.integrations",
    task_acks_late=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone=settings.timezone,
    enable_utc=True,
    task_always_eager=settings.task_always_eager,
    broker_connection_retry_on_startup=True,
    task_routes={
        "backend.tasks.integration.*": {"queue": "ua_flow.integrations"},
        "backend.tasks.analytics.*": {"queue": "ua_flow.analytics"},
    },
)

celery_app.autodiscover_tasks(["backend.tasks"])

