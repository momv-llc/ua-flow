"""Analytical endpoints powering dashboards and BI tooling."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import get_current_user, require_roles
from backend.models import User
from backend.services.analytics_pipeline import (
    latest_collection_timestamp,
    load_support,
    load_summary,
    load_velocity,
    run_pipeline,
    WEEKS_DEFAULT,
)

router = APIRouter()


@router.get("/summary")
def analytics_summary(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return the latest aggregated snapshot for the analytics overview."""

    return load_summary(db)


@router.get("/overview", include_in_schema=False)
def analytics_summary_alias(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return analytics_summary(db, user)


@router.get("/velocity")
def analytics_velocity(
    weeks: int = Query(default=WEEKS_DEFAULT, ge=1, le=26),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return computed delivery velocity grouped by ISO week."""

    return load_velocity(db, weeks=weeks)


@router.get("/support")
def analytics_support(
    weeks: int = Query(default=WEEKS_DEFAULT, ge=1, le=26),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return support desk performance metrics grouped by ISO week."""

    return load_support(db, weeks=weeks)


@router.post("/etl/run")
def trigger_etl(
    weeks: int = Query(default=WEEKS_DEFAULT, ge=1, le=26),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "moderator")),
):
    """Execute the analytics ETL pipeline on demand."""

    return run_pipeline(db, weeks=weeks)


@router.get("/etl/status")
def etl_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Expose the timestamp of the latest ETL collection run."""

    return {"collected_at": latest_collection_timestamp(db)}


__all__ = [
    "analytics_summary",
    "analytics_velocity",
    "analytics_support",
    "trigger_etl",
    "etl_status",
]
