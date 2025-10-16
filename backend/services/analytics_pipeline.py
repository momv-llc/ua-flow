"""ETL helpers powering the analytics and BI experiences."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from backend.models import (
    AnalyticsSnapshot,
    Doc,
    IntegrationConnection,
    SupportTicket,
    Task,
    TaskStatus,
    TicketStatus,
    Team,
    Project,
)

WEEKS_DEFAULT = 6


def _iso_bucket(moment: datetime) -> str:
    iso_year, iso_week, _ = moment.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def _upsert_snapshot(db: Session, metric: str, bucket: str, payload: Dict[str, Any]) -> None:
    snapshot = (
        db.query(AnalyticsSnapshot)
        .filter(
            AnalyticsSnapshot.metric == metric,
            AnalyticsSnapshot.bucket == bucket,
        )
        .one_or_none()
    )
    now = datetime.utcnow()
    if snapshot:
        snapshot.payload = payload
        snapshot.collected_at = now
    else:
        snapshot = AnalyticsSnapshot(
            metric=metric,
            bucket=bucket,
            payload=payload,
            collected_at=now,
        )
        db.add(snapshot)


def _prune_metric(db: Session, metric: str, retain: int = 24) -> None:
    query = (
        db.query(AnalyticsSnapshot)
        .filter(AnalyticsSnapshot.metric == metric)
        .order_by(AnalyticsSnapshot.collected_at.desc())
    )
    for stale in query.offset(retain):
        db.delete(stale)


def compute_summary(db: Session) -> Dict[str, Dict[str, int]]:
    return {
        "core": {
            "teams": db.query(Team).count(),
            "projects": db.query(Project).count(),
            "tasks": db.query(Task).count(),
        },
        "docs": {
            "pages": db.query(Doc).count(),
        },
        "integration": {
            "active": db.query(IntegrationConnection).filter(IntegrationConnection.is_active.is_(True)).count(),
        },
        "support": {
            "open_tickets": db.query(SupportTicket).filter(SupportTicket.status != TicketStatus.closed).count(),
        },
    }


def compute_velocity(db: Session, weeks: int = WEEKS_DEFAULT) -> List[Dict[str, Any]]:
    cutoff = datetime.utcnow() - timedelta(weeks=weeks)
    planned: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"planned": 0, "completed": 0, "velocity": 0})

    for task in db.query(Task).filter(Task.created_at >= cutoff):
        bucket = _iso_bucket(task.created_at)
        planned[bucket]["planned"] += 1

    completed_tasks = (
        db.query(Task)
        .filter(
            Task.status == TaskStatus.done,
            Task.completed_at.isnot(None),
            Task.completed_at >= cutoff,
        )
        .all()
    )
    for task in completed_tasks:
        bucket = _iso_bucket(task.completed_at or task.created_at)
        planned[bucket]["completed"] += 1

    # Backfill tasks that are marked done but missing a completion timestamp.
    fallback_done = (
        db.query(Task)
        .filter(Task.status == TaskStatus.done, Task.completed_at.is_(None), Task.created_at >= cutoff)
        .all()
    )
    for task in fallback_done:
        bucket = _iso_bucket(task.created_at)
        planned[bucket]["completed"] += 1

    timeline = []
    for bucket, data in planned.items():
        completed = data["completed"]
        planned_total = data["planned"] or completed or 1
        velocity = round((completed / planned_total) * 100, 2)
        timeline.append({"week": bucket, "completed": completed, "planned": planned_total, "velocity": velocity})
    timeline.sort(key=lambda item: item["week"])
    return timeline


def compute_support(db: Session, weeks: int = WEEKS_DEFAULT) -> List[Dict[str, Any]]:
    cutoff = datetime.utcnow() - timedelta(weeks=weeks)
    incoming: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"incoming": 0, "resolved": 0, "avg_sla": 0.0})

    for ticket in db.query(SupportTicket).filter(SupportTicket.created_at >= cutoff):
        bucket = _iso_bucket(ticket.created_at)
        incoming[bucket]["incoming"] += 1

    resolved = (
        db.query(SupportTicket)
        .filter(
            SupportTicket.resolved_at.isnot(None),
            SupportTicket.resolved_at >= cutoff,
        )
        .all()
    )
    for ticket in resolved:
        bucket = _iso_bucket(ticket.resolved_at or ticket.updated_at or ticket.created_at)
        incoming[bucket]["resolved"] += 1
        delta = (ticket.resolved_at or ticket.updated_at or ticket.created_at) - ticket.created_at
        hours = round(delta.total_seconds() / 3600, 2)
        current = incoming[bucket]
        total_resolved = current.get("resolved", 0)
        if total_resolved:
            current["avg_sla"] = round(((current.get("avg_sla", 0) * (total_resolved - 1)) + hours) / total_resolved, 2)
        else:
            current["avg_sla"] = hours

    timeline = []
    for bucket, data in incoming.items():
        timeline.append(
            {
                "week": bucket,
                "incoming": data.get("incoming", 0),
                "resolved": data.get("resolved", 0),
                "avg_sla": round(data.get("avg_sla", 0.0), 2),
            }
        )
    timeline.sort(key=lambda item: item["week"])
    return timeline


def run_pipeline(db: Session, weeks: int = WEEKS_DEFAULT) -> Dict[str, Any]:
    summary = compute_summary(db)
    velocity = compute_velocity(db, weeks)
    support = compute_support(db, weeks)

    _upsert_snapshot(db, "summary", "latest", summary)
    for row in velocity:
        _upsert_snapshot(db, "velocity", row["week"], row)
    for row in support:
        _upsert_snapshot(db, "support", row["week"], row)

    _prune_metric(db, "velocity")
    _prune_metric(db, "support")

    db.commit()
    collected_at = datetime.utcnow().isoformat()
    return {"summary": summary, "velocity": velocity, "support": support, "collected_at": collected_at}


def load_summary(db: Session) -> Dict[str, Any]:
    snapshot = (
        db.query(AnalyticsSnapshot)
        .filter(AnalyticsSnapshot.metric == "summary", AnalyticsSnapshot.bucket == "latest")
        .one_or_none()
    )
    if snapshot is None:
        result = run_pipeline(db)
        summary = result["summary"]
        summary["collected_at"] = result["collected_at"]
        return summary
    data = dict(snapshot.payload)
    data["collected_at"] = snapshot.collected_at.isoformat()
    return data


def load_velocity(db: Session, weeks: int = WEEKS_DEFAULT) -> List[Dict[str, Any]]:
    cutoff_bucket = _iso_bucket(datetime.utcnow() - timedelta(weeks=weeks))
    rows = (
        db.query(AnalyticsSnapshot)
        .filter(AnalyticsSnapshot.metric == "velocity")
        .order_by(AnalyticsSnapshot.bucket.asc())
        .all()
    )
    timeline = [row.payload for row in rows if row.bucket >= cutoff_bucket]
    if not timeline:
        result = run_pipeline(db, weeks)
        return result["velocity"]
    return timeline


def load_support(db: Session, weeks: int = WEEKS_DEFAULT) -> List[Dict[str, Any]]:
    cutoff_bucket = _iso_bucket(datetime.utcnow() - timedelta(weeks=weeks))
    rows = (
        db.query(AnalyticsSnapshot)
        .filter(AnalyticsSnapshot.metric == "support")
        .order_by(AnalyticsSnapshot.bucket.asc())
        .all()
    )
    timeline = [row.payload for row in rows if row.bucket >= cutoff_bucket]
    if not timeline:
        result = run_pipeline(db, weeks)
        return result["support"]
    return timeline


def latest_collection_timestamp(db: Session) -> str | None:
    snapshot = (
        db.query(AnalyticsSnapshot)
        .order_by(AnalyticsSnapshot.collected_at.desc())
        .first()
    )
    return snapshot.collected_at.isoformat() if snapshot else None


__all__ = [
    "compute_summary",
    "compute_velocity",
    "compute_support",
    "run_pipeline",
    "load_summary",
    "load_velocity",
    "load_support",
    "latest_collection_timestamp",
]
