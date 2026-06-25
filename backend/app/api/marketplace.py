"""Service provider marketplace.

Skills are derived from control domains. EVA authorizes providers, sets a priority
weight and the skills they cover. Clients use "Get Help" on a control to see
matching providers (by the control's domain), ordered by weight.
"""
import re
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.email import send_email
from app.api.auth import get_current_user
from app.core.audit import record as audit_record
from app.models.user import User, UserRole
from app.models.framework import Control
from app.models.marketplace import ServiceProvider, MarketplaceSkill

router = APIRouter()
STATUSES = {"pending", "active", "suspended"}

# Canonical skill labels - merges spelling variants across frameworks
# (e.g. "Audit and accountability" / "Audit & Accountability" → one skill).
_CANON = {
    "access control": "Access Control",
    "awareness and training": "Awareness & Training",
    "audit and accountability": "Audit & Accountability",
    "configuration management": "Configuration Management",
    "identification and authentication": "Identification & Authentication",
    "incident response": "Incident Response",
    "maintenance": "Maintenance",
    "media protection": "Media Protection",
    "personnel security": "Personnel Security",
    "physical protection": "Physical Protection",
    "planning": "Planning",
    "risk assessment": "Risk Assessment",
    "security assessment": "Security Assessment & Monitoring",
    "security assessment and monitoring": "Security Assessment & Monitoring",
    "system and communications protection": "System & Communications Protection",
    "system and information integrity": "System & Information Integrity",
    "system and services acquisition": "System & Services Acquisition",
    "supply chain risk management": "Supply Chain Risk Management",
}


def canonical(domain: Optional[str]) -> str:
    key = re.sub(r"\s+", " ", (domain or "").strip().lower().replace("&", "and"))
    return _CANON.get(key, (domain or "").strip())


def _serialize(p: ServiceProvider) -> dict:
    return {
        "id": str(p.id), "name": p.name, "contact_name": p.contact_name,
        "contact_email": p.contact_email, "website": p.website,
        "skills": p.skills or [], "priority_weight": p.priority_weight,
        "status": p.status, "notes": p.notes or "",
    }


async def _skills(db: AsyncSession) -> list[str]:
    """Canonical control-domain skills + the editable custom skills, deduped."""
    rows = (await db.execute(
        select(Control.domain).where(Control.domain.isnot(None)).distinct()
    )).scalars().all()
    skills = {canonical(d) for d in rows if (d or "").strip()}
    custom = (await db.execute(select(MarketplaceSkill.name))).scalars().all()
    skills |= {(c or "").strip() for c in custom if (c or "").strip()}
    return sorted(skills)


@router.get("/skills")
async def list_skills(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """The skill taxonomy = distinct control domains across all frameworks."""
    return {"skills": await _skills(db)}


# Public skills list (no auth) so the provider self-registration page can load them.
@router.get("/public/skills")
async def public_skills(db: AsyncSession = Depends(get_db)):
    return {"skills": await _skills(db)}


class RegisterBody(BaseModel):
    name: str
    contact_name: str = ""
    contact_email: str
    website: str = ""
    skills: list[str] = []


@router.post("/register")
async def register_provider(body: RegisterBody, db: AsyncSession = Depends(get_db)):
    """Public - a provider applies to join. Created pending; EVA authorizes it."""
    if not body.name.strip() or not body.contact_email.strip():
        raise HTTPException(status_code=400, detail="Name and contact email are required")
    p = ServiceProvider(
        name=body.name.strip()[:200], contact_name=body.contact_name.strip()[:200],
        contact_email=body.contact_email.strip()[:255], website=body.website.strip()[:300],
        skills=[s for s in (body.skills or []) if s], status="pending",
    )
    db.add(p)
    await db.commit()
    recipients = (await db.execute(select(User.email).where(User.role == UserRole.super_admin))).scalars().all()
    send_email(list(recipients), "New service provider awaiting authorization",
               f"{p.name} applied to the marketplace and is awaiting authorization.")
    return {"ok": True}


def _require_admin(user: User):
    if user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")


@router.get("/providers")
async def list_providers(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(current_user)
    rows = (await db.execute(select(ServiceProvider).order_by(
        ServiceProvider.priority_weight.desc(), ServiceProvider.name))).scalars().all()
    return {"providers": [_serialize(p) for p in rows], "skills": await _skills(db)}


class ProviderBody(BaseModel):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    website: Optional[str] = None
    skills: Optional[list[str]] = None
    priority_weight: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


@router.post("/providers")
async def create_provider(body: ProviderBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(current_user)
    if not (body.name or "").strip():
        raise HTTPException(status_code=400, detail="Name is required")
    p = ServiceProvider(
        name=body.name.strip()[:200], contact_name=(body.contact_name or "").strip()[:200],
        contact_email=(body.contact_email or "").strip()[:255], website=(body.website or "").strip()[:300],
        skills=[s for s in (body.skills or []) if s], priority_weight=body.priority_weight or 0,
        status=body.status if body.status in STATUSES else "active", notes=body.notes,
    )
    db.add(p)
    await audit_record(db, current_user, "provider.created", target=p.name)
    await db.commit()
    await db.refresh(p)
    return _serialize(p)


async def _get(db, provider_id) -> ServiceProvider:
    try:
        pid = uuid.UUID(provider_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Provider not found")
    p = (await db.execute(select(ServiceProvider).where(ServiceProvider.id == pid))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Provider not found")
    return p


@router.put("/providers/{provider_id}")
async def update_provider(provider_id: str, body: ProviderBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(current_user)
    p = await _get(db, provider_id)
    if body.name is not None and body.name.strip():
        p.name = body.name.strip()[:200]
    if body.contact_name is not None:
        p.contact_name = body.contact_name.strip()[:200]
    if body.contact_email is not None:
        p.contact_email = body.contact_email.strip()[:255]
    if body.website is not None:
        p.website = body.website.strip()[:300]
    if body.skills is not None:
        p.skills = [s for s in body.skills if s]
    if body.priority_weight is not None:
        p.priority_weight = int(body.priority_weight)
    if body.status is not None and body.status in STATUSES:
        p.status = body.status
    if body.notes is not None:
        p.notes = body.notes
    await db.commit()
    return _serialize(p)


@router.post("/providers/{provider_id}/authorize")
async def authorize_provider(provider_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(current_user)
    p = await _get(db, provider_id)
    p.status = "active"
    await audit_record(db, current_user, "provider.authorized", target=p.name)
    await db.commit()
    return _serialize(p)


@router.delete("/providers/{provider_id}")
async def delete_provider(provider_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(current_user)
    p = await _get(db, provider_id)
    await audit_record(db, current_user, "provider.deleted", target=p.name)
    await db.delete(p)
    await db.commit()
    return {"deleted": provider_id}


@router.get("/custom-skills")
async def list_custom_skills(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(current_user)
    rows = (await db.execute(select(MarketplaceSkill).order_by(MarketplaceSkill.name))).scalars().all()
    return {"skills": [{"id": str(s.id), "name": s.name} for s in rows]}


class SkillBody(BaseModel):
    name: str


@router.post("/custom-skills")
async def add_custom_skill(body: SkillBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(current_user)
    name = (body.name or "").strip()[:120]
    if not name:
        raise HTTPException(status_code=400, detail="Skill name is required")
    exists = (await db.execute(select(MarketplaceSkill).where(func.lower(MarketplaceSkill.name) == name.lower()))).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="That skill already exists")
    s = MarketplaceSkill(name=name)
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return {"id": str(s.id), "name": s.name}


@router.delete("/custom-skills/{skill_id}")
async def delete_custom_skill(skill_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(current_user)
    try:
        sid = uuid.UUID(skill_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Skill not found")
    s = (await db.execute(select(MarketplaceSkill).where(MarketplaceSkill.id == sid))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Skill not found")
    await db.delete(s)
    await db.commit()
    return {"deleted": skill_id}


@router.get("/help")
async def get_help(control_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Suggest active providers who cover this control's domain, best first."""
    try:
        cid = uuid.UUID(control_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Control not found")
    control = (await db.execute(select(Control).where(Control.id == cid))).scalar_one_or_none()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    domain = canonical(control.domain)
    rows = (await db.execute(
        select(ServiceProvider).where(ServiceProvider.status == "active")
        .order_by(ServiceProvider.priority_weight.desc(), ServiceProvider.name)
    )).scalars().all()
    matches = [p for p in rows if domain and domain in {canonical(s) for s in (p.skills or [])}]
    # If none cover this exact domain, fall back to all active providers.
    use = matches or rows
    return {
        "domain": domain,
        "exact": bool(matches),
        "providers": [{
            "id": str(p.id), "name": p.name, "website": p.website,
            "contact_email": p.contact_email, "skills": p.skills or [],
        } for p in use[:10]],
    }
