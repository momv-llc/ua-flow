"""Utility helpers for secure secret resolution.

These helpers allow the platform to source secrets either directly from
environment variables or from mounted files (e.g. Kubernetes secrets
projected to the filesystem).  This keeps runtime configuration flexible
without hardcoding secret providers in the application code.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Return a secret value from env vars or *_FILE fallbacks."""

    file_override = os.getenv(f"{key}_FILE")
    if file_override:
        path = Path(file_override)
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
    value = os.getenv(key, default)
    return value


__all__ = ["get_secret"]
