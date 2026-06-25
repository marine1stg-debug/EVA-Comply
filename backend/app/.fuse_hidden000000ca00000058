"""Provision any MISSING org-control rows for each client's assigned frameworks.

Fixes clients whose control provisioning was lost (e.g. after a framework
re-import) so they see every control of the frameworks they're subscribed to.

SAFE / ADDITIVE ONLY: this only CREATES missing org_control rows. It never
deletes org_controls, evidence items, expected-evidence, or anything a client
has collected. Existing rows (and their evidence) are left untouched.

Assigned frameworks per client = frameworks the client already has any
org-control in  ∪  frameworks listed in their billing settings.

DRY RUN by default — prints the diagnosis and exits. Add --yes to provision.

USAGE (inside the api container):
    docker compose exec api python -m app.sync_orgcontrols            # dry run
    docker compose exec api python -m app.sync_orgcontrols --yes
"""
import argparse
import asyncio

from sqlalchemy import select, func

from app.core.database import AsyncSessionLocal
from app.models import framework, evidence  # noqa: F401 — register mappers
from app.models.framework import Framework, Control
from app.models.evidence import OrgControl
from app.models.tenant import Tenant
from app.core.provisioning import assign_frameworks


async def run(commit: bool):
    async with AsyncSessionLocal() as db:
        print(f"Mode: {'COMMIT' if commit else 'DRY RUN'}\n")
        fw_name = {f.id: f.name for f in (await db.execute(select(Framework))).scalars().all()}
        fw_total = {fid: (await db.execute(
            select(func.count(Control.id)).where(Control.framework_id == fid)
        )).scalar_one() for fid in fw_name}

        tenants = (await db.execute(select(Tenant))).scalars().all()
        grand_created = 0
        for t in tenants:
            have = set((await db.execute(
                select(func.distinct(Control.framework_id))
                .join(OrgControl, OrgControl.control_id == Control.id)
                .where(OrgControl.org_id == t.id)
            )).scalars().all())
            have = {f for f in have if f}
            billing = set((t.settings or {}).get("framework_billing", {}).keys())
            import uuid as _uuid
            billing_ids = set()
            for b in billing:
                try:
                    billing_ids.add(_uuid.UUID(str(b)))
                except (ValueError, TypeError):
                    pass
            assigned = have | billing_ids
            if not assigned:
                continue

            lines = []
            missing_total = 0
            for fid in assigned:
                total = fw_total.get(fid, 0)
                prov = (await db.execute(
                    select(func.count(OrgControl.id))
                    .join(Control, Control.id == OrgControl.control_id)
                    .where(OrgControl.org_id == t.id, Control.framework_id == fid)
                )).scalar_one()
                miss = max(0, total - prov)
                missing_total += miss
                flag = "  ← will add" if miss else ""
                lines.append(f"    {fw_name.get(fid, fid)}: {prov}/{total} provisioned{(' (' + str(miss) + ' missing)' + flag) if miss else ''}")

            if missing_total == 0:
                continue
            print(f"{t.name} [{t.tenant_type.value if hasattr(t.tenant_type,'value') else t.tenant_type}]  ({missing_total} missing)")
            for ln in lines:
                print(ln)

            if commit:
                created = await assign_frameworks(db, t.id, [str(f) for f in assigned])
                grand_created += created
                print(f"    → created {created} org-control rows")

        if commit:
            await db.commit()
            print(f"\nCommitted. Total rows created: {grand_created}. Nothing was deleted.")
        else:
            print("\nDry run only — re-run with --yes to provision the missing rows. (Additive only — nothing is deleted.)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="create the missing rows")
    args = ap.parse_args()
    asyncio.run(run(args.yes))
