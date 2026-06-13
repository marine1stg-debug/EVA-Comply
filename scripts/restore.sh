#!/usr/bin/env bash
# Restore a full backup produced by backup.sh.
# Usage:  ./scripts/restore.sh backups/eva_db_YYYYMMDD_HHMMSS.dump [backups/eva_uploads_*.tar.gz]
# WARNING: this OVERWRITES the current database. Stop the app first if possible.
set -euo pipefail

cd "$(dirname "$0")/.."
DUMP="${1:-}"
UPLOADS="${2:-}"
if [[ -z "$DUMP" || ! -f "$DUMP" ]]; then
  echo "Usage: $0 <db_dump_file> [uploads_tar_gz]"; exit 1
fi

DB_USER="${POSTGRES_USER:-eva_user}"
DB_NAME="${POSTGRES_DB:-eva_db}"

read -r -p "This will OVERWRITE database '$DB_NAME'. Continue? [y/N] " ok
[[ "$ok" == "y" || "$ok" == "Y" ]] || { echo "Aborted."; exit 1; }

echo "→ Restoring database from $DUMP…"
# --clean --if-exists drops existing objects first; restore into the db.
docker compose exec -T db pg_restore -U "$DB_USER" -d "$DB_NAME" --clean --if-exists --no-owner < "$DUMP"

if [[ -n "$UPLOADS" && -f "$UPLOADS" ]]; then
  echo "→ Restoring uploaded files from $UPLOADS…"
  docker compose exec -T api sh -c 'cd /app && tar xzf - ' < "$UPLOADS"
fi

echo "✓ Restore complete. Restart the stack: docker compose restart api worker"
