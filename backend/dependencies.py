"""Shared FastAPI dependencies used across routers."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import AuditLog, User
from backend.security import decode_token


def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the user from a Bearer token."""

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1]
    try:
        data = decode_token(token)
    except Exception:  # pragma: no cover - token errors bubble to API
        raise HTTPException(status_code=401, detail="Invalid token") from None

    user = db.get(User, int(data.get("sub", 0)))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def require_roles(*allowed_roles: str):
    """Create a dependency that ensures the current user has one of the roles."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        if allowed_roles and user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return dependency


def audit_log(
    user: User,
    action: str,
    metadata: dict | None,
    db: Session,
) -> None:
    """Persist an audit record for the performed action."""

    record = AuditLog(actor_id=user.id if user else None, action=action, metadata=metadata or {})
    db.add(record)
    db.commit()
