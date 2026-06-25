"""
Flush demo / sample data from the EVA portal database.

The seed script populates the app with demo content so it's usable out of the
box. Once you're loading real framework catalogs and real tenants, run this to
clear the samples.

SCOPES (choose with --scope, default = content):

  content   Remove only sample CONTENT:
              • all evidence items
              • all org-control posture rows
              • all controls belonging to the seeded system frameworks
                (the 8 demo CMMC controls)
            Keeps: tenants, users, framework rows, billing plans, settings.
            Your imported catalogs (non-system frameworks) are untouched.

  demo      Everything in `content`, PLUS:
              • all users except the super admin (superadmin@eva.com)
              • all tenants except the EVA internal tenant
            Keeps: super-admin login, billing plans, platform settings.

  full      Wipe ALL tenants, users, frameworks, controls, posture, evidence,
            then re-create only the EVA tenant + super admin. Billing plans and
            platform settings are preserved (re-created if missing). Truly empty.

SAFETY: this is a DRY RUN by default - it prints what it would delete and exits.
Add --yes to actually commit the changes.

USAGE (from eva-portal/backend, with the app's env/DB reachable):
    python -m app.flush_demo                     # dry run, content scope
    python -m app.flush_demo --scope content --yes
    python -m app.flush_demo --scope demo --yes
    python -m app.flush_demo --scope full --yes
"""
import argparse
import asyncio

from sqlalchemy import select, delete, func

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password

# Import all models so the mapper registry is complete before we query.
from app.models import framework, evidence  # noqa: F401
from app.models.tenant import Tenant, TenantType, SubscriptionStatus
from app.models.user import User, UserRole
from app.models.framework import Framework, Control
from app.models.evidence import OrgControl, EvidenceItem
from app.models.billing import BillingPlan, PlanTier
from app.models.platform import PlatformSettings, BillingMode

SUPER_EMAIL = "superadmin@eva.com"


async def _count(db, model, *where):
    stmt = select(func.count()).select_from(model)
    for w in where:
        stmt = stmt.where(w)
    return (await db.execute(stmt)).scalar_one()


async def _system_fw_ids(db):
    return (await db.execute(
        select(Framework.id).where(Framework.is_system.is_(True))
    )).scalars().all()


async def preview(db, scope):
    sys_ids = await _system_fw_ids(db)
    sample_controls = (
        await _count(db, Control, Control.framework_id.in_(sys_ids)) if sys_ids else 0
    )
    lines = [
        f"  evidence items ............ {await _count(db, EvidenceItem)}",
        f"  org-control posture rows .. {await _count(db, OrgControl)}",
    ]
    if scope == "full":
        lines.append(f"  controls (ALL) ............ {await _count(db, Control)}")
        lines.append(f"  frameworks (ALL) .......... {await _count(db, Framework)}")
        lines.append(f"  users (ALL) ............... {await _count(db, User)}")
        lines.append(f"  tenants (ALL) ............. {await _count(db, Tenant)}")
        lines.append("  → then re-create EVA tenant + super admin")
    else:
        lines.append(f"  sample controls (system fw) {sample_controls}")
        if scope == "demo":
            lines.append(
                f"  users except super admin .. {await _count(db, User, User.email != SUPER_EMAIL)}"
            )
            lines.append(
                f"  tenants except EVA internal {await _count(db, Tenant, Tenant.tenant_type != TenantType.eva_internal)}"
            )
    return "\n".join(lines)


async def _ensure_plans_and_settings(db):
    if await _count(db, BillingPlan) == 0:
        db.add_all([
            BillingPlan(
                name="Professional", tier=PlanTier.single_client, price_monthly=499, is_active=True,
                inclusions={"frameworks": "all",
                            "features": {"reports": True, "import": False, "msp_review": False,
                                         "audit_logs": False, "api": False},
                            "max_users": 10, "max_clients": 0},
            ),
            BillingPlan(
                name="MSP Professional", tier=PlanTier.msp, price_monthly=1499, is_active=True,
                inclusions={"frameworks": "all",
                            "features": {"reports": True, "import": True, "msp_review": True,
                                         "audit_logs": True, "api": True},
                            "max_users": 25, "max_clients": 50},
            ),
        ])
    if await _count(db, PlatformSettings) == 0:
        db.add(PlatformSettings(billing_mode=BillingMode.no_card_trial, trial_days=14))


async def run(scope, commit):
    async with AsyncSessionLocal() as db:
        print(f"Scope: {scope}   Mode: {'COMMIT' if commit else 'DRY RUN'}\n")
        print("Will remove:")
        print(await preview(db, scope))

        if not commit:
            print("\nDry run only - re-run with --yes to apply.")
            return

        # Always clear posture + evidence (FK children first).
        await db.execute(delete(EvidenceItem))
        await db.execute(delete(OrgControl))

        if scope == "full":
            await db.execute(delete(Control))
            await db.execute(delete(Framework))
            await db.execute(delete(User))
            await db.execute(delete(Tenant))
            await db.flush()
            eva = Tenant(
                name="EVA Technologies", tenant_type=TenantType.eva_internal,
                subscription_status=SubscriptionStatus.active, plan_name="Professional",
            )
            db.add(eva)
            await db.flush()
            db.add(User(
                tenant_id=eva.id, email=SUPER_EMAIL,
                password_hash=hash_password("demo1234"),
                display_name="Alex Rivera", role=UserRole.super_admin,
            ))
            await _ensure_plans_and_settings(db)
        else:
            sys_ids = await _system_fw_ids(db)
            if sys_ids:
                await db.execute(delete(Control).where(Control.framework_id.in_(sys_ids)))
            if scope == "demo":
                await db.execute(delete(User).where(User.email != SUPER_EMAIL))
                await db.execute(
                    delete(Tenant).where(Tenant.tenant_type != TenantType.eva_internal)
                )

        await db.commit()
        print("\n✅ Flush complete.")


def main():
    ap = argparse.ArgumentParser(description="Flush demo/sample data from the EVA portal DB.")
    ap.add_argument("--scope", choices=["content", "demo", "full"], default="content")
    ap.add_argument("--yes", action="store_true", help="actually commit (otherwise dry run)")
    args = ap.parse_args()
    asyncio.run(run(args.scope, args.yes))


if __name__ == "__main__":
    main()
