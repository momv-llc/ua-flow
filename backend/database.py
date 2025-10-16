"""Database configuration helpers for the UA FLOW backend."""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, sessionmaker


# Ensure values from a local .env file are available when running via uvicorn.
load_dotenv()


def _resolve_database_url() -> str:
    """Return the database URL with a safe fallback for local development."""

    url = os.getenv("DATABASE_URL")
    if url:
        return url
    # Default to a local SQLite database so new developers can boot the API
    # without provisioning Postgres right away.
    return "sqlite:///./uaflow.db"


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create (and memoize) the SQLAlchemy engine with backend-specific options."""

    url = _resolve_database_url()
    connect_args = {}
    engine_kwargs = {"pool_pre_ping": True}

    if url.startswith("sqlite"):
        # SQLite needs explicit thread handling for FastAPI's threaded server.
        connect_args = {"check_same_thread": False}
        # SQLite does not support connection pooling – drop pool arguments.
        engine_kwargs = {}

    engine = create_engine(url, connect_args=connect_args, **engine_kwargs)

    # Attempt a quick connection so deployment failures are raised early with
    # a descriptive message rather than bubbling up during the first request.
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except OperationalError as exc:  # pragma: no cover - requires broken DB
        raise RuntimeError(
            "Unable to connect to the configured database. "
            "Check DATABASE_URL credentials or availability."
        ) from exc

    return engine


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Import models so metadata is populated before create_all.
    from .models import (  # noqa: F401
        AuditLog,
        Doc,
        DocSignature,
        DocVersion,
        Epic,
        IntegrationConnection,
        IntegrationLog,
        MarketplaceApp,
        MarketplaceInstallation,
        Project,
        Sprint,
        SupportComment,
        SupportTicket,
        Task,
        TaskComment,
        Team,
        TeamMember,
        SystemSetting,
        TwoFactorSecret,
        User,
    )

    Base.metadata.create_all(bind=engine)
