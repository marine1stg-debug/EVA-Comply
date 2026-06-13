#!/usr/bin/env bash
# Full backup of the EVA Comply database + uploaded files.
# Usage:  ./scripts/backup.sh            (writes to ./backups/)
# Requires the stack to be running (docker compose up -d).
set -euo pipefail

cd "$(dirname "$0")/.."
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="backups"
mkdir -p "$OUT"

DB_USER="${POSTGRES_USER:-eva_user}"
DB_NAME="${POSTGRES_DB:-eva_db}"

echo "→ Dumping database ($DB_NAME)…"
# Custom format (-Fc) → restore with pg_restore. Compressed.
docker compose exec -T db pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc > "$OUT/eva_db_${STAMP}.dump"

echo "→ Archiving uploaded files (evidence, videos, attachments)…"
# The uploads live in the api container at /app/uploads (uploads_data volume).
docker compose exec -T api sh -c 'cd /app && tar czf - uploads 2>/dev/null' > "$OUT/eva_uploads_${STAMP}.tar.gz" || \
  echo "  (uploads archive skipped — api not running or no uploads)"

echo "✓ Backup complete:"
echo "   $OUT/eva_db_${STAMP}.dump"
echo "   $OUT/eva_uploads_${STAMP}.tar.gz"
