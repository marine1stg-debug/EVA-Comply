"""Delete ALL frameworks and their controls (plus dependent posture, evidence,
and expected-evidence rows) so you can import new catalogs into a clean slate.

Keeps tenants, users, billing plans, and platform settings. Stored evidence
FILES on disk are left in place (orphaned, harmless); only DB rows are removed.

DRY RUN by default — prints what it would delete and exits. Add --yes to commit.

USAGE (inside the api container):
    docker compose exec api python -m app.flush_frameworks            # dry run
    docker compose exec api python -m app.flush_frameworks --yes
"""
import argparse
import asyncio

from sqlalchemy import select, delete, func

from app.core.database import AsyncSessionLocal
from app.models import framework, evidence  # noqa: F401 — register mappers
from app.models.framework import Framework, Control
from app.models.evidence import OrgControl, EvidenceItem, ExpectedEvidence


async def _count(db, model):
    return (await db.execute(select(func.count()).select_from(model))).scalar_one()


async def run(commit: bool):
    async with AsyncSessionLocal() as db:
        print(f"Mode: {'COMMIT' if commit else 'DRY RUN'}\n")
        print("Will delete:")
        print(f"  evidence items ............ {await _count(db, EvidenceItem)}")
        print(f"  expected-evidence rows .... {await _count(db, ExpectedEvidence)}")
        print(f"  org-control posture rows .. {await _count(db, OrgControl)}")
        print(f"  controls .................. {await _count(db, Control)}")
        print(f"  frameworks ................ {await _count(db, Framework)}")

        if not commit:
            print("\nDry run only — re-run with --yes to apply.")
            return

        # FK-safe order: children first.
        await db.execute(delete(EvidenceItem))
        await db.execute(delete(ExpectedEvidence))
        await db.execute(delete(OrgControl))
        await db.execute(delete(Control))
        await db.execute(delete(Framework))
        await db.commit()
        print("\n✅ All frameworks and controls removed. Ready for fresh imports.")


def main():
    ap = argparse.ArgumentParser(description="Delete all frameworks/controls and dependent data.")
    ap.add_argument("--yes", action="store_true", help="actually commit (otherwise dry run)")
    asyncio.run(run(ap.parse_args().yes))


if __name__ == "__main__":
    main()
