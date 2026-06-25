"""Merge duplicate OrgControl rows.

A client (org) should have at most ONE org_control row per control. A double
provisioning (e.g. the same framework assigned twice) can leave duplicates,
which makes `.scalar_one_or_none()` raise MultipleResultsFound and breaks the
control-detail / expected-evidence endpoints.

For each (org_id, control_id) group with >1 row this keeps the EARLIEST row
(by created_at) as the canonical one, repoints all EvidenceItem.org_control_id
references to it, then deletes the extra OrgControl rows. ExpectedEvidence is
keyed by (org_id, control_id) so it is unaffected.

DRY RUN by default - prints what it would do and exits. Add --yes to commit.

USAGE (inside the api container):
    docker compose exec api python -m app.dedupe_orgcontrols            # dry run
    docker compose exec api python -m app.dedupe_orgcontrols --yes
"""
import argparse
import asyncio
from collections import defaultdict

from sqlalchemy import select, update, delete

from app.core.database import AsyncSessionLocal
from app.models import framework, evidence  # noqa: F401 - register mappers
from app.models.evidence import OrgControl, EvidenceItem


async def run(commit: bool):
    async with AsyncSessionLocal() as db:
        print(f"Mode: {'COMMIT' if commit else 'DRY RUN'}\n")

        rows = (await db.execute(
            select(OrgControl).order_by(OrgControl.created_at.asc())
        )).scalars().all()

        groups: dict[tuple, list] = defaultdict(list)
        for oc in rows:
            groups[(oc.org_id, oc.control_id)].append(oc)

        dupes = {k: v for k, v in groups.items() if len(v) > 1}
        if not dupes:
            print("No duplicate OrgControl rows found. Nothing to do.")
            return

        total_extra = 0
        total_moved = 0
        for (org_id, control_id), ocs in dupes.items():
            keep = ocs[0]                      # earliest
            extras = ocs[1:]
            extra_ids = [o.id for o in extras]
            moved = (await db.execute(
                select(EvidenceItem.id).where(EvidenceItem.org_control_id.in_(extra_ids))
            )).scalars().all()
            total_extra += len(extras)
            total_moved += len(moved)
            print(f"org={org_id} control={control_id}: "
                  f"{len(ocs)} rows -> keep {keep.id}, drop {len(extras)} "
                  f"(repoint {len(moved)} evidence items)")

            if commit:
                if extra_ids:
                    await db.execute(
                        update(EvidenceItem)
                        .where(EvidenceItem.org_control_id.in_(extra_ids))
                        .values(org_control_id=keep.id)
                    )
                    await db.execute(
                        delete(OrgControl).where(OrgControl.id.in_(extra_ids))
                    )

        print(f"\nGroups with duplicates: {len(dupes)}")
        print(f"Extra OrgControl rows: {total_extra}")
        print(f"Evidence items repointed: {total_moved}")

        if commit:
            await db.commit()
            print("\nCommitted.")
        else:
            print("\nDry run only - re-run with --yes to apply.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="commit the merge")
    args = ap.parse_args()
    asyncio.run(run(args.yes))
