# -*- coding: utf-8 -*-
"""Subscription agreement: present the right variant, record acceptance."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.models.agreement import AgreementAcceptance
from app.core.agreement_text import (
    AGREEMENT_VERSION, account_type_for, build_html,
)

router = APIRouter()


async def _tenant(db: AsyncSession, user: User):
    return (await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))).scalar_one_or_none()


@router.get("/me")
async def my_agreement(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """The agreement variant for the current user, plus whether they have already
    accepted the current version."""
    t = await _tenant(db, current_user)
    at = account_type_for(current_user, t)
    doc = build_html(at)
    accepted = (await db.execute(
        select(func.count(AgreementAcceptance.id)).where(
            AgreementAcceptance.user_id == current_user.id,
            AgreementAcceptance.version == AGREEMENT_VERSION,
        )
    )).scalar_one()
    return {**doc, "needs_acceptance": accepted == 0}


@router.post("/accept")
async def accept_agreement(request: Request, current_user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    t = await _tenant(db, current_user)
    at = account_type_for(current_user, t)
    # Already recorded for this version? Idempotent.
    existing = (await db.execute(
        select(AgreementAcceptance).where(
            AgreementAcceptance.user_id == current_user.id,
            AgreementAcceptance.version == AGREEMENT_VERSION,
        )
    )).scalar_one_or_none()
    if existing:
        return {"ok": True, "already": True, "version": AGREEMENT_VERSION}
    fwd = request.headers.get("x-forwarded-for", "")
    ip = (fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "")) or ""
    db.add(AgreementAcceptance(
        user_id=current_user.id, tenant_id=current_user.tenant_id, account_type=at,
        version=AGREEMENT_VERSION, user_name=current_user.display_name or "",
        user_role=getattr(current_user.role, "value", str(current_user.role)),
        org_name=(t.name if t else ""), ip_address=ip,
    ))
    await db.commit()
    return {"ok": True, "version": AGREEMENT_VERSION}


@router.get("/acceptances")
async def list_acceptances(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Consent audit trail (Super Admin)."""
    if current_user.role != UserRole.super_admin:
        return {"acceptances": []}
    rows = (await db.execute(
        select(AgreementAcceptance).order_by(AgreementAcceptance.created_at.desc()).limit(1000)
    )).scalars().all()
    return {"acceptances": [{
        "id": str(a.id), "user_name": a.user_name, "user_role": a.user_role,
        "org_name": a.org_name, "account_type": a.account_type, "version": a.version,
        "ip_address": a.ip_address,
        "accepted_at": a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else "-",
    } for a in rows]}
