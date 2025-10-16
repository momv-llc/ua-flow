"""Celery tasks for analytics ETL orchestration."""

from __future__ import annotations

from backend.celery_app import celery_app
from backend.database import SessionLocal
from backend.services.analytics_pipeline import run_pipeline, WEEKS_DEFAULT


@celery_app.task(name="analytics.run_pipeline")
def run_analytics_pipeline(weeks: int = WEEKS_DEFAULT):
    """Execute the analytics ETL pipeline inside a worker process."""

    session = SessionLocal()
    try:
        return run_pipeline(session, weeks=weeks)
    finally:
        session.close()


__all__ = ["run_analytics_pipeline"]
