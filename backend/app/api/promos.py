"""Promo code admin (EVA super admin) — create/list/update signup codes that
grant a billing mode (no-card trial / card trial / charge immediately)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.promo import PromoCode
from app.models.platform import BillingMode
from app.core.promo import is_usable, MODE_HINT

router = APIRouter()


def _serialize(p: PromoCode) -> dict:
    return {
        "id": str(p.id), "code": p.code, "billing_mode": p.billing_mode.value,
        "hint": MODE_HINT.get(p.billing_mode.value), "label": p.label,
        "is_active": p.is_active, "expires_at": p.expires_at.isoformat() if p.expires_at else None,
        "max_uses": p.max_uses, "uses": p.uses, "usable": is_usable(p),
    }


def _require_eva(user: User):
    if user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")


@router.get("/")
async def list_promos(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_eva(current_user)
    rows = (await db.execute(select(PromoCode).order_by(PromoCode.created_at.desc()))).scalars().all()
    return {"promos": [_serialize(p) for p in rows], "modes": [m.value for m in BillingMode]}


class PromoBody(BaseModel):
    code: str
    billing_mode: str
    label: Optional[str] = None
    max_uses: Optional[int] = None
    expires_at: Optional[str] = None


@router.post("/")
async def create_promo(body: PromoBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_eva(current_user)
    code = (body.code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="Code is required")
    try:
        mode = BillingMode(body.billing_mode)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid billing mode")
    dupe = (await db.execute(select(PromoCode).where(func.lower(PromoCode.code) == code.lower()))).scalar_one_or_none()
    if dupe:
        raise HTTPException(status_code=400, detail="That code already exists")
    exp = None
    if body.expires_at:
        try:
            exp = datetime.fromisoformat(body.expires_at)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expiry date")
    p = PromoCode(code=code, billing_mode=mode, label=body.label or None,
                  max_uses=body.max_uses, expires_at=exp, is_active=True, uses=0)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return _serialize(p)


class PromoUpdate(BaseModel):
    is_active: Optional[bool] = None
    label: Optional[str] = None
    max_uses: Optional[int] = None
    billing_mode: Optional[str] = None


@router.patch("/{promo_id}")
async def update_promo(promo_id: str, body: PromoUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_eva(current_user)
    try:
        pid = uuid.UUID(promo_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Promo not found")
    p = (await db.execute(select(PromoCode).where(PromoCode.id == pid))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Promo not found")
    if body.is_active is not None:
        p.is_active = body.is_active
    if body.label is not None:
        p.label = body.label or None
    if body.max_uses is not None:
        p.max_uses = body.max_uses if body.max_uses > 0 else None
    if body.billing_mode is not None:
        try:
            p.billing_mode = BillingMode(body.billing_mode)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid billing mode")
    await db.commit()
    await db.refresh(p)
    return _serialize(p)


@router.delete("/{promo_id}")
async def delete_promo(promo_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_eva(current_user)
    try:
        pid = uuid.UUID(promo_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Promo not found")
    p = (await db.execute(select(PromoCode).where(PromoCode.id == pid))).scalar_one_or_none()
    if p:
        await db.delete(p)
        await db.commit()
    return {"deleted": True}
