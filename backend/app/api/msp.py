"""
MSP API - client management + portfolio overview.
Scope: MSP roles → client tenants under their MSP; super_admin → all clients.
Resale economics (eva_cost / margin) are derived for display from plan price.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.core.security import hash_password, random_password, create_invite_token
from app.core.provisioning import assign_frameworks
from app.core.entitlements import get_entitlements, tenant_usage, filter_frameworks, ensure_active
from app.core.audit import record as audit_record
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantType, SubscriptionStatus
from app.models.framework import Framework, Control
from app.models.evidence import OrgControl, OrgControlStatus, EvidenceItem, EvidenceStatus

router = APIRouter()

MSP_ROLES = {UserRole.msp_admin, UserRole.msp_analyst, UserRole.super_admin}
DONE = {OrgControlStatus.implemented, OrgControlStatus.verified}
PENDING_EV = {EvidenceStatus.client_submitted, EvidenceStatus.msp_pending, EvidenceStatus.eva_pending}
PLAN_MRR = {"Professional": 499, "MSP Professional": 1499}
PALETTE = ["#2563EB", "#7C3AED", "#0D9488", "#D97706", "#DC2626", "#0891B2", "#16A34A"]
EVA_COST_RATIO = 0.55  # platform cost as a fraction of the client fee (display only)


def _initials(name: str) -> str:
    p = [x for x in name.split() if x]
    return (p[0][0] + (p[1][0] if len(p) > 1 else "")).upper() if p else "?"


def _status(s: SubscriptionStatus) -> str:
    return {"active": "active", "trialing": "onboarding", "suspended": "suspended"}.get(s.value, s.value)


async def _client_tenants(db: AsyncSession, user: User):
    if user.role == UserRole.super_admin:
        rows = await db.execute(select(Tenant).where(Tenant.tenant_type == TenantType.single_client, Tenant.archived == False))  # noqa: E712
    elif user.role in (UserRole.msp_admin, UserRole.msp_analyst):
        rows = await db.execute(select(Tenant).where(Tenant.parent_msp_id == user.tenant_id, Tenant.archived == False))  # noqa: E712
    else:
        raise HTTPException(status_code=403, detail="MSP access required")
    return list(rows.scalars().all())


async def _client_summary(db: AsyncSession, t: Tenant, idx: int) -> dict:
    oc = (await db.execute(select(OrgControl.status).where(OrgControl.org_id == t.id))).scalars().all()
    total = len(oc)
    done = sum(1 for s in oc if s in DONE)
    compliance = round(done / total * 100) if total else 0
    pending = (await db.execute(
        select(func.count(EvidenceItem.id)).where(EvidenceItem.org_id == t.id, EvidenceItem.status.in_(PENDING_EV))
    )).scalar_one()
    fw_rows = await db.execute(
        select(func.distinct(Framework.name))
        .join(Control, Control.framework_id == Framework.id)
        .join(OrgControl, OrgControl.control_id == Control.id)
        .where(OrgControl.org_id == t.id)
    )
    frameworks = [f for (f,) in fw_rows.all()]
    users = (await db.execute(select(func.count(User.id)).where(User.tenant_id == t.id))).scalar_one()
    admin = (await db.execute(
        select(User.display_name).where(User.tenant_id == t.id, User.role == UserRole.client_admin).limit(1)
    )).scalar_one_or_none()
    last = (await db.execute(select(func.max(User.last_login_at)).where(User.tenant_id == t.id))).scalar_one()
    fee = t.monthly_price or PLAN_MRR.get(t.plan_name or "", 0)
    eva_cost = round(fee * EVA_COST_RATIO)
    return {
        "id": str(t.id), "name": t.name, "short": _initials(t.name), "color": PALETTE[idx % len(PALETTE)],
        "compliance": compliance, "controls_done": done, "controls_total": total,
        "evidence_pending": pending, "status": _status(t.subscription_status),
        "frameworks": frameworks or ["-"], "plan": t.plan_name or "-",
        "msp_review": t.msp_review_enabled, "users": users, "admin": admin,
        "last_activity": last.strftime("%b %d, %Y") if last else "Never",
        "monthly_fee": fee, "eva_cost": eva_cost, "margin": fee - eva_cost,
    }


from app.core import platform_config as pc  # noqa: E402
FRONTEND_URL = settings.FRONTEND_URL  # legacy; invite links use pc.frontend_url()


class NewClientBody(BaseModel):
    org_name: str
    admin_name: str
    admin_email: EmailStr
    plan: str = "Professional"
    monthly_price: int = 499
    msp_review_enabled: bool = True
    framework_ids: list[str] = []


@router.post("/clients")
async def create_client(
    body: NewClientBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in (UserRole.msp_admin, UserRole.super_admin):
        raise HTTPException(status_code=403, detail="Only MSP Admins can add clients")
    await ensure_active(db, current_user)
    exists = (await db.execute(select(User).where(User.email == body.admin_email))).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="That admin email is already in use")

    # Enforce the MSP plan's client-count limit (Super Admin is unlimited).
    msp_frameworks_filter = None
    if current_user.role == UserRole.msp_admin:
        msp_tenant = (await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))).scalar_one()
        ent = await get_entitlements(db, msp_tenant)
        usage = await tenant_usage(db, msp_tenant)
        if ent["max_clients"] and usage["clients"] >= ent["max_clients"]:
            raise HTTPException(status_code=403, detail=f"Your plan's client limit ({ent['max_clients']}) is reached. Upgrade to add more.")
        msp_frameworks_filter = ent

    parent = current_user.tenant_id if current_user.role == UserRole.msp_admin else None
    tenant = Tenant(
        name=body.org_name, tenant_type=TenantType.single_client,
        parent_msp_id=parent, subscription_status=SubscriptionStatus.active,
        plan_name=body.plan, monthly_price=body.monthly_price,
        msp_review_enabled=body.msp_review_enabled,
    )
    db.add(tenant)
    await db.flush()
    # Client admin starts inactive with an unusable password until they accept the invite.
    admin = User(
        tenant_id=tenant.id, email=body.admin_email,
        password_hash=hash_password(random_password()),
        display_name=body.admin_name, role=UserRole.client_admin, is_active=False,
    )
    db.add(admin)
    await db.flush()
    fw_ids = filter_frameworks(msp_frameworks_filter, body.framework_ids) if msp_frameworks_filter else body.framework_ids
    assigned = await assign_frameworks(db, tenant.id, fw_ids)
    await db.commit()

    token = create_invite_token(admin.id, admin.email)
    dev = settings.ENVIRONMENT == "development" or settings.EMAIL_BACKEND == "console"
    print(f"[invite] {admin.email} -> /accept-invite?token={token}")
    return {
        "id": str(tenant.id), "name": tenant.name, "controls_assigned": assigned,
        "invite_link": f"{pc.frontend_url()}/accept-invite?token={token}" if dev else None,
    }


@router.get("/clients")
async def list_clients(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tenants = await _client_tenants(db, current_user)
    clients = [await _client_summary(db, t, i) for i, t in enumerate(tenants)]
    return {"clients": clients, "total": len(clients)}


# ── MSP pre-review: per-client toggle + MSP-wide default ─────────────────────
class ReviewBody(BaseModel):
    enabled: bool


@router.patch("/clients/{client_id}/review")
async def set_client_review(client_id: str, body: ReviewBody,
                            current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Turn MSP pre-review on/off for one client. MSP admins manage their own
    clients; super_admin any. When ON, the client's submitted evidence goes to
    the MSP queue before EVA; when OFF, it goes straight to EVA."""
    if current_user.role not in (UserRole.msp_admin, UserRole.super_admin):
        raise HTTPException(status_code=403, detail="MSP admin access required")
    tenants = await _client_tenants(db, current_user)
    try:
        cid = uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Client not found")
    t = next((x for x in tenants if x.id == cid), None)
    if not t:
        raise HTTPException(status_code=404, detail="Client not found")
    t.msp_review_enabled = bool(body.enabled)
    await audit_record(db, current_user, "tenant.msp_review",
                       target=t.name, detail="on" if body.enabled else "off", org_id=t.id)
    await db.commit()
    return {"id": str(t.id), "msp_review": t.msp_review_enabled}


@router.get("/review-default")
async def get_review_default(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """The MSP-wide default that pre-fills the toggle when adding a new client."""
    if current_user.role not in (UserRole.msp_admin, UserRole.msp_analyst):
        return {"default": True}
    me = (await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))).scalar_one()
    return {"default": bool((me.settings or {}).get("msp_review_default", True))}


@router.put("/review-default")
async def set_review_default(body: ReviewBody,
                             current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Set the MSP-wide default applied to newly added clients."""
    if current_user.role != UserRole.msp_admin:
        raise HTTPException(status_code=403, detail="Only an MSP Admin can set the default")
    me = (await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))).scalar_one()
    me.settings = {**(me.settings or {}), "msp_review_default": bool(body.enabled)}
    await db.commit()
    return {"default": bool(body.enabled)}


@router.get("/clients/{client_id}")
async def client_detail(client_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tenants = await _client_tenants(db, current_user)
    try:
        cid = uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Client not found")
    match = next((t for t in tenants if t.id == cid), None)
    if not match:
        raise HTTPException(status_code=404, detail="Client not found")
    idx = tenants.index(match)
    summary = await _client_summary(db, match, idx)

    # recent evidence for the client
    erows = await db.execute(
        select(EvidenceItem.title, EvidenceItem.status, Control.ref)
        .join(OrgControl, OrgControl.id == EvidenceItem.org_control_id)
        .join(Control, Control.id == OrgControl.control_id)
        .where(EvidenceItem.org_id == cid)
        .order_by(EvidenceItem.created_at.desc()).limit(6)
    )
    summary["recent_evidence"] = [
        {"title": ti, "status": st.value.replace("_", " "), "ref": rf} for ti, st, rf in erows.all()
    ]
    return summary


@router.get("/portfolio")
async def portfolio(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tenants = await _client_tenants(db, current_user)
    clients = [await _client_summary(db, t, i) for i, t in enumerate(tenants)]
    n = len(clients) or 1
    total_mrr = sum(c["monthly_fee"] for c in clients)
    total_cost = sum(c["eva_cost"] for c in clients)
    kpis = {
        "total_clients": len(clients),
        "active_clients": sum(1 for c in clients if c["status"] == "active"),
        "onboarding": sum(1 for c in clients if c["status"] == "onboarding"),
        "avg_compliance": round(sum(c["compliance"] for c in clients) / n),
        "ready": sum(1 for c in clients if c["compliance"] >= 80),
        "at_risk": sum(1 for c in clients if c["compliance"] < 40),
        "total_pending": sum(c["evidence_pending"] for c in clients),
        "total_mrr": total_mrr,
        "total_cost": total_cost,
        "total_margin": total_mrr - total_cost,
        "margin_pct": round((total_mrr - total_cost) / total_mrr * 100) if total_mrr else 0,
    }
    return {"clients": clients, "kpis": kpis}
