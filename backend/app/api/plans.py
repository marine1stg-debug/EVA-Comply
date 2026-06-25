"""
Plans & Pricing API - Super Admin CRUD over configurable packages.
Inclusions drive entitlements (frameworks, feature modules, seat/client limits).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.models.billing import BillingPlan, PlanTier, FEATURE_KEYS

router = APIRouter()

DEFAULT_INCLUSIONS = {
    "frameworks": "all",
    "features": {k: False for k in FEATURE_KEYS},
    "max_users": 0,
    "max_clients": 0,
}


def _serialize(p: BillingPlan, tenants_count: int = 0) -> dict:
    inc = dict(DEFAULT_INCLUSIONS, **(p.inclusions or {}))
    inc["features"] = {**{k: False for k in FEATURE_KEYS}, **(inc.get("features") or {})}
    return {
        "id": str(p.id), "name": p.name, "tier": p.tier.value,
        "price_monthly": p.price_monthly, "wholesale_monthly": p.wholesale_monthly or 0,
        "yearly_discount_pct": p.yearly_discount_pct or 0,
        "is_active": p.is_active, "inclusions": inc, "tenants": tenants_count,
    }


async def _require_admin(user: User):
    if user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")


class PlanBody(BaseModel):
    name: str
    tier: str = "single_client"
    price_monthly: int = 0
    wholesale_monthly: int = 0
    yearly_discount_pct: int = 0
    is_active: bool = True
    inclusions: dict = {}


@router.get("/")
async def list_plans(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _require_admin(current_user)
    plans = (await db.execute(select(BillingPlan))).scalars().all()
    out = []
    for p in plans:
        n = (await db.execute(select(func.count(Tenant.id)).where(Tenant.plan_id == p.id))).scalar_one()
        out.append(_serialize(p, n))
    out.sort(key=lambda x: (x["tier"], x["price_monthly"]))
    return {"plans": out, "feature_keys": FEATURE_KEYS}


@router.get("/active")
async def active_plans(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    plans = (await db.execute(
        select(BillingPlan).where(BillingPlan.is_active == True)  # noqa: E712
    )).scalars().all()
    return {"plans": [_serialize(p) for p in plans]}


@router.post("/")
async def create_plan(body: PlanBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _require_admin(current_user)
    try:
        tier = PlanTier(body.tier)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tier")
    p = BillingPlan(
        name=body.name, tier=tier, price_monthly=body.price_monthly,
        wholesale_monthly=body.wholesale_monthly,
        yearly_discount_pct=max(0, min(100, body.yearly_discount_pct or 0)),
        is_active=body.is_active, inclusions=dict(DEFAULT_INCLUSIONS, **(body.inclusions or {})),
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return _serialize(p)


@router.put("/{plan_id}")
async def update_plan(plan_id: str, body: PlanBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _require_admin(current_user)
    try:
        pid = uuid.UUID(plan_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Plan not found")
    p = (await db.execute(select(BillingPlan).where(BillingPlan.id == pid))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Plan not found")
    try:
        p.tier = PlanTier(body.tier)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tier")
    p.name = body.name
    p.price_monthly = body.price_monthly
    p.wholesale_monthly = body.wholesale_monthly
    p.yearly_discount_pct = max(0, min(100, body.yearly_discount_pct or 0))
    p.is_active = body.is_active
    p.inclusions = dict(DEFAULT_INCLUSIONS, **(body.inclusions or {}))
    await db.commit()
    return _serialize(p)


@router.delete("/{plan_id}")
async def delete_plan(plan_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _require_admin(current_user)
    try:
        pid = uuid.UUID(plan_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Plan not found")
    in_use = (await db.execute(select(func.count(Tenant.id)).where(Tenant.plan_id == pid))).scalar_one()
    if in_use:
        raise HTTPException(status_code=400, detail=f"Plan is in use by {in_use} tenant(s); deactivate it instead")
    p = (await db.execute(select(BillingPlan).where(BillingPlan.id == pid))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Plan not found")
    await db.delete(p)
    await db.commit()
    return {"deleted": plan_id}
