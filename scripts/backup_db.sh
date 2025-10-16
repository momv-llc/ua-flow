#!/usr/bin/env bash
set -euo pipefail

DATABASE_URL=${DATABASE_URL:-sqlite:///./uaflow.db}
BACKUP_DIR=${BACKUP_DIR:-backups}
MAX_BACKUPS=${MAX_BACKUPS:-5}

mkdir -p "$BACKUP_DIR"

if [[ "$DATABASE_URL" == sqlite* ]]; then
  python - "$DATABASE_URL" "$BACKUP_DIR" "$MAX_BACKUPS" <<'PY'
import shutil
import sys
from datetime import datetime
from pathlib import Path

url, backup_dir, max_backups = sys.argv[1:4]
path = url.replace("sqlite:///", "")
path = path.replace("sqlite://", "")
path = Path(path).expanduser()
if not path.exists():
    raise SystemExit(f"SQLite database not found at {path}")

backup_dir = Path(backup_dir)
backup_name = backup_dir / f"uaflow-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.db"
shutil.copy2(path, backup_name)
print(f"Created backup {backup_name}")

backups = sorted(backup_dir.glob("uaflow-*.db"))
for old in backups[:-int(max_backups)]:
    old.unlink()
    print(f"Removed old backup {old}")
PY
else
  echo "PostgreSQL backup detected. Refer to docs/devops/backup.md for pg_dump instructions." >&2
  exit 1
fi
