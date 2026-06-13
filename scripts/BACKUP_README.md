# Backup & restore

## Full backup (database + uploaded files)

```bash
cd eva-portal
chmod +x scripts/backup.sh scripts/restore.sh   # first time only
./scripts/backup.sh
```

Produces, in `eva-portal/backups/`:
- `eva_db_<timestamp>.dump` — the whole database (Postgres custom format).
- `eva_uploads_<timestamp>.tar.gz` — evidence, training videos, attachments.

Keep these somewhere safe (off the server). Schedule them with cron, e.g. daily:

```
0 2 * * *  cd /path/to/eva-portal && ./scripts/backup.sh >> backups/backup.log 2>&1
```

## Full restore

```bash
./scripts/restore.sh backups/eva_db_<timestamp>.dump backups/eva_uploads_<timestamp>.tar.gz
docker compose restart api worker
```

This **overwrites** the current database, so take a fresh backup first if needed.

## Single-client backup

Export one client's data as JSON from the app:
**Administration → Tenants → (a client) → Export** — downloads `client_<name>.json`
(tenant, users without secrets, controls, evidence metadata, support cases,
recommendations). Useful for audits, handover, or archiving a departing client.

> Per-client *restore* (re-importing that JSON into a new tenant) is a separate,
> carefully-tested feature on the roadmap; for now, full restore is via the script
> above.

## Upgrade safety

Schema changes ship as additive Alembic migrations (new columns are nullable or
carry server defaults), so upgrading preserves existing data. Always run a
`backup.sh` before `docker compose up --build` on a production environment.
