"""
Entitlements - resolves a tenant's plan inclusions into enforceable limits.

Tenants with no plan (e.g. EVA internal / Super Admin) are treated as
unlimited so platform staff are never gated.
"""
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.models.user import User
from app.models.billing import BillingPlan, FEATURE_KEYS

def trial_state(tenant: Tenant, trial_days: int = 14, billing_mode: str = "no_card_trial") -> dict:
    """Resolve trial / lock status from subscription_status + created_at + platform mode."""
    status = tenant.subscription_status.value
    if status == "active":
        return {"status": status, "trialing": False, "days_left": None, "locked": False}
    if status in ("suspended", "cancelled", "past_due"):
        return {"status": status, "trialing": False, "days_left": 0, "locked": True}
    if status == "trialing":
        if billing_mode == "charge_immediately":
            # No trial in this mode - access requires completed payment.
            return {"status": status, "trialing": False, "days_left": 0, "locked": True}
        created = tenant.created_at or datetime.now(timezone.utc)
        elapsed = (datetime.now(timezone.utc) - created).days
        days_left = max(trial_days - elapsed, 0)
        return {"status": status, "trialing": True, "days_left": days_left, "locked": days_left <= 0}
    return {"status": status, "trialing": False, "days_left": None, "locked": False}


def effective_mode(tenant: Tenant, settings) -> str:
    """The tenant's own billing mode (from its signup promo code) if set,
    otherwise the platform default."""
    return (getattr(tenant, "billing_mode", None) or settings.billing_mode.value)


async def ensure_active(db: AsyncSession, current_user):
    """Block write actions when the tenant's trial has lapsed or it's unpaid."""
    from app.core.platform import get_settings
    t = (await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))).scalar_one()
    s = await get_settings(db)
    if trial_state(t, s.trial_days, effective_mode(t, s))["locked"]:
        raise HTTPException(status_code=402, detail="Your trial has ended - subscribe to continue.")

FEATURE_LABEL = {
    "reports": "report export", "import": "custom framework import",
    "msp_review": "MSP pre-review", "audit_logs": "audit logs", "api": "API access",
}


async def get_entitlements(db: AsyncSession, tenant: Tenant) -> dict:
    plan = None
    if tenant.plan_id:
        plan = (await db.execute(
            select(BillingPlan).where(BillingPlan.id == tenant.plan_id)
        )).scalar_one_or_none()

    if not plan:
        return {
            "plan": tenant.plan_name,
            "frameworks": "all",
            "features": {k: True for k in FEATURE_KEYS},
            "max_users": 0, "max_clients": 0, "unlimited": True,
        }

    inc = plan.inclusions or {}
    return {
        "plan": plan.name,
        "frameworks": inc.get("frameworks", "all"),
        "features": {k: bool((inc.get("features") or {}).get(k, False)) for k in FEATURE_KEYS},
        "max_users": int(inc.get("max_users", 0) or 0),
        "max_clients": int(inc.get("max_clients", 0) or 0),
        "unlimited": False,
    }


def has_feature(ent: dict, key: str) -> bool:
    return ent.get("unlimited") or bool(ent.get("features", {}).get(key))


def framework_allowed(ent: dict, framework_id) -> bool:
    fw = ent.get("frameworks", "all")
    return fw == "all" or str(framework_id) in {str(x) for x in fw}


def filter_frameworks(ent: dict, framework_ids: list) -> list:
    fw = ent.get("frameworks", "all")
    if fw == "all":
        return list(framework_ids)
    allowed = {str(x) for x in fw}
    return [f for f in framework_ids if str(f) in allowed]


async def ensure_feature(db: AsyncSession, current_user, key: str):
    """Raise 403 unless the caller's tenant plan includes the feature."""
    t = (await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))).scalar_one()
    ent = await get_entitlements(db, t)
    if not has_feature(ent, key):
        raise HTTPException(status_code=403, detail=f"Your plan does not include {FEATURE_LABEL.get(key, key)}. Upgrade to enable it.")


async def tenant_usage(db: AsyncSession, tenant: Tenant) -> dict:
    users = (await db.execute(
        select(func.count(User.id)).where(User.tenant_id == tenant.id)
    )).scalar_one()
    clients = (await db.execute(
        select(func.count(Tenant.id)).where(Tenant.parent_msp_id == tenant.id)
    )).scalar_one()
    return {"users": users, "clients": clients}
