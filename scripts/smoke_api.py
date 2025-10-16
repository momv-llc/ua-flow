"""Minimal end-to-end smoke checks for the UA FLOW API."""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

# Force a local SQLite database so the smoke test does not depend on external
# PostgreSQL services when executed in CI or developer machines.
os.environ.setdefault("DATABASE_URL", "sqlite:///./smoke_test.db")
os.environ.setdefault("CELERY_EAGER", "1")

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.database import Base, SessionLocal, engine  # noqa: E402  # pylint: disable=wrong-import-position
from backend.main import app  # noqa: E402  # pylint: disable=wrong-import-position


def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def ensure_docs_available(client: TestClient) -> None:
    response = client.get("/api/openapi.json")
    response.raise_for_status()


def run_auth_flow(client: TestClient) -> None:
    email = f"smoke-{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPass123!"

    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    register.raise_for_status()

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    login.raise_for_status()
    token = login.json()["access_token"]

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    me.raise_for_status()


def main() -> None:
    reset_database()
    client = TestClient(app)

    ensure_docs_available(client)
    run_auth_flow(client)

    SessionLocal().close()
    db_path = Path("smoke_test.db")
    if db_path.exists():
        db_path.unlink()

    print("UA FLOW API smoke test passed")


if __name__ == "__main__":
    main()
