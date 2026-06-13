# -*- coding: utf-8 -*-
"""Delete superseded framework catalogs everywhere (framework + controls + all
dependent rows). Removes old versions left behind when a catalog was rebuilt:
  • CyberSecure Canada  — any version other than the current 'Baseline V1.2'
  • CIS Controls        — any version other than the current '8.1.2'

USAGE (inside the api container):
    docker compose exec api python -m app.cleanup_stale_catalogs            # dry run (counts only)
    docker compose exec api python -m app.cleanup_stale_catalogs --yes      # actually delete
"""
import argparse
import asyncio

from sqlalchemy import text
from app.core.database import AsyncSessionLocal

# Frameworks to purge: (name LIKE pattern, version to KEEP)
TARGETS = [
    ("CyberSecure Canada%", "Baseline V1.2"),
    ("CIS Controls%", "8.1.2"),
]

COND = " OR ".join([f"(f.name LIKE :p{i} AND f.version <> :v{i})" for i in range(len(TARGETS))])
PARAMS = {}
for i, (pat, keep) in enumerate(TARGETS):
    PARAMS[f"p{i}"] = pat
    PARAMS[f"v{i}"] = keep

FW_SUB = f"SELECT f.id FROM frameworks f WHERE {COND}"
CTRL_SUB = f"SELECT id FROM controls WHERE framework_id IN ({FW_SUB})"

DELETES = [
    # evidence items attached to org-controls or expected-evidence of those controls
    f"""DELETE FROM evidence_items WHERE
         org_control_id IN (SELECT id FROM org_controls WHERE control_id IN ({CTRL_SUB}))
         OR expected_evidence_id IN (SELECT id FROM expected_evidence WHERE control_id IN ({CTRL_SUB}))""",
    f"DELETE FROM control_events WHERE control_id IN ({CTRL_SUB})",
    f"DELETE FROM recommendations WHERE control_id IN ({CTRL_SUB})",
    f"DELETE FROM maturity_self_assessments WHERE control_id IN ({CTRL_SUB})",
    f"DELETE FROM expected_evidence WHERE control_id IN ({CTRL_SUB})",
    f"DELETE FROM org_controls WHERE control_id IN ({CTRL_SUB})",
    f"DELETE FROM maturity_assessments WHERE framework_id IN ({FW_SUB})",
    f"DELETE FROM maturity_snapshots WHERE framework_id IN ({FW_SUB})",
    f"DELETE FROM controls WHERE framework_id IN ({FW_SUB})",
    f"DELETE FROM frameworks f WHERE {COND}",
]


async def run(commit: bool):
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(text(
            f"SELECT f.name, f.version, "
            f"(SELECT count(*) FROM controls c WHERE c.framework_id = f.id) AS n "
            f"FROM frameworks f WHERE {COND} ORDER BY f.name, f.version"), PARAMS)).all()
        if not rows:
            print("Nothing to clean — no superseded CyberSecure/CIS frameworks found.")
            return
        print("Superseded frameworks found:")
        for name, version, n in rows:
            print(f"  • {name}  (version '{version}')  — {n} controls")
        if not commit:
            print("\nDRY RUN — nothing deleted. Re-run with --yes to delete the above everywhere.")
            return
        for sql in DELETES:
            res = await db.execute(text(sql), PARAMS)
            print(f"  deleted {res.rowcount:>5}  ::  {sql.split(' WHERE')[0].replace('DELETE FROM ', '')[:48]}")
        await db.commit()
        print("\nDone — superseded catalogs removed everywhere.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="actually delete (otherwise dry run)")
    args = ap.parse_args()
    asyncio.run(run(args.yes))
