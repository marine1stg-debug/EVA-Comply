"""
Tenant management API — list + suspend/reactivate.
Scope: super_admin → all tenants; MSP → own MSP + its client tenants.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from datetime import datetime, timezone, date
import uuid

from app.core.database import get_db
from app.core.provisioning import assign_frameworks
from app.core.audit import record as audit_record
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantType, SubscriptionStatus
from app.models.framework import Framework, Control
from app.models.evidence import OrgControl, OrgControlStatus, EvidenceItem, EvidenceStatus, ExpectedEvidence
from app.models.billing import BillingPlan, PlanTier

router = APIRouter()

DONE = {OrgControlStatus.implemented, OrgControlStatus.verified}
PENDING_EV = {EvidenceStatus.client_submitted, EvidenceStatus.msp_pending, EvidenceStatus.eva_pending}
PLAN_MRR = {"Professional": 499, "MSP Professional": 1499}
PALETTE = ["#2563EB", "#7C3AED", "#0D9488", "#D97706", "#DC2626", "#0891B2", "#16A34A"]


def _initials(name: str) -> str:
    parts = [p for p in name.split() if p]
    return (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper() if parts else "?"


def _type_label(t: TenantType) -> str:
    return {"msp": "msp", "single_client": "client", "eva_internal": "eva"}[t.value]


def _status_label(s: SubscriptionStatus) -> str:
    return {"active": "active", "trialing": "onboarding", "suspended": "suspended",
            "past_due": "past_due", "cancelled": "cancelled"}.get(s.value, s.value)


@router.get("/")
async def list_tenants(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == UserRole.super_admin:
        # Exclude the platform tenant itself (EVA Technologies / eva_internal) —
        # it's the operator org, not a managed MSP or client.
        rows = (await db.execute(
            select(Tenant).where(Tenant.tenant_type != TenantType.eva_internal)
        )).scalars().all()
    elif current_user.role in (UserRole.msp_admin, UserRole.msp_analyst):
        rows = (await db.execute(
            select(Tenant).where(
                (Tenant.id == current_user.tenant_id) | (Tenant.parent_msp_id == current_user.tenant_id)
            )
        )).scalars().all()
    else:
        raise HTTPException(status_code=403, detail="Tenant management requires admin access")

    by_id = {t.id: t for t in rows}
    out = []
    for i, t in enumerate(rows):
        oc_rows = (await db.execute(
            select(OrgControl.status).where(OrgControl.org_id == t.id)
        )).scalars().all()
        total = len(oc_rows)
        done = sum(1 for s in oc_rows if s in DONE)
        compliance = round(done / total * 100) if total else 0
        ev_pending = (await db.execute(
            select(func.count(EvidenceItem.id)).where(
                EvidenceItem.org_id == t.id, EvidenceItem.status.in_(PENDING_EV)
            )
        )).scalar_one()
        admin = (await db.execute(
            select(User.display_name).where(
                User.tenant_id == t.id,
                User.role.in_([UserRole.super_admin, UserRole.msp_admin, UserRole.client_admin]),
            ).limit(1)
        )).scalar_one_or_none()
        last_login = (await db.execute(
            select(func.max(User.last_login_at)).where(User.tenant_id == t.id)
        )).scalar_one()
        parent = by_id.get(t.parent_msp_id)

        out.append({
            "id": str(t.id),
            "name": t.name,
            "short": _initials(t.name),
            "color": PALETTE[i % len(PALETTE)],
            "type": _type_label(t.tenant_type),
            "plan": t.plan_name or "—",
            "mrr": t.monthly_price or PLAN_MRR.get(t.plan_name or "", 0),
            "msp": parent.name if parent else None,
            "compliance": compliance,
            "evidence_pending": ev_pending,
            "status": _status_label(t.subscription_status),
            "admin": admin,
            "archived": t.archived,
            "activation_pending": t.activation_pending,
            "audit_level": t.audit_level or "self",
            "created": t.created_at.strftime("%b %Y") if t.created_at else "—",
            "last_login": last_login.strftime("%b %d, %Y") if last_login else "Never",
        })
    out.sort(key=lambda x: (x["type"] != "msp", x["name"]))
    return {
        "tenants": out,
        "counts": {
            "all": len(out),
            "msp": sum(1 for t in out if t["type"] == "msp"),
            "client": sum(1 for t in out if t["type"] == "client"),
        },
    }


class ConvertBody(BaseModel):
    plan_id: str


@router.post("/{tenant_id}/convert-to-direct")
async def convert_to_direct(
    tenant_id: str,
    body: ConvertBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Graduate an MSP-managed client into a direct EVA client on a single-client plan.
    Keeps all data (controls, evidence, users); changes ownership + billing."""
    if current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found")
    t = (await db.execute(select(Tenant).where(Tenant.id == tid))).scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if t.tenant_type != TenantType.single_client or not t.parent_msp_id:
        raise HTTPException(status_code=400, detail="Only an MSP-managed client can be converted")

    try:
        plan = (await db.execute(select(BillingPlan).where(BillingPlan.id == uuid.UUID(body.plan_id)))).scalar_one_or_none()
    except ValueError:
        plan = None
    if not plan or plan.tier != PlanTier.single_client:
        raise HTTPException(status_code=400, detail="Choose an active single-client plan")

    # Detach from MSP, move to direct billing on the chosen plan.
    t.parent_msp_id = None
    t.plan_id = plan.id
    t.plan_name = plan.name
    t.monthly_price = plan.price_monthly
    t.msp_review_enabled = False
    t.subscription_status = SubscriptionStatus.active

    # Evidence that was waiting on MSP pre-review now goes straight to EVA.
    rows = (await db.execute(
        select(EvidenceItem).where(
            EvidenceItem.org_id == t.id,
            EvidenceItem.status.in_([EvidenceStatus.msp_pending, EvidenceStatus.msp_flagged]),
        )
    )).scalars().all()
    for ev in rows:
        ev.status = EvidenceStatus.eva_pending
    await db.commit()
    return {"id": str(t.id), "name": t.name, "plan": plan.name, "rerouted_evidence": len(rows)}


class PlanBody(BaseModel):
    plan_id: str


@router.patch("/{tenant_id}/plan")
async def set_tenant_plan(
    tenant_id: str,
    body: PlanBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Assign a billing plan to any tenant. The plan's tier must match the tenant:
    MSP tenants → 'msp' plans; client/EVA tenants → 'single_client' plans."""
    if current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found")
    t = (await db.execute(select(Tenant).where(Tenant.id == tid))).scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    try:
        plan = (await db.execute(select(BillingPlan).where(BillingPlan.id == uuid.UUID(body.plan_id)))).scalar_one_or_none()
    except ValueError:
        plan = None
    if not plan or not plan.is_active:
        raise HTTPException(status_code=400, detail="Choose an active plan")
    want = PlanTier.msp if t.tenant_type == TenantType.msp else PlanTier.single_client
    if plan.tier != want:
        raise HTTPException(status_code=400, detail=f"This tenant requires a '{want.value}' plan")
    old_plan = t.plan_name or "—"
    t.plan_id = plan.id
    t.plan_name = plan.name
    t.monthly_price = plan.price_monthly
    await audit_record(db, current_user, "tenant.plan_changed", target=t.name,
                       detail=f"{old_plan} → {plan.name}", org_id=t.id)
    await db.commit()
    return {"id": str(t.id), "plan": plan.name, "mrr": plan.price_monthly}


class StatusBody(BaseModel):
    suspend: bool


@router.patch("/{tenant_id}/status")
async def set_tenant_status(
    tenant_id: str,
    body: StatusBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found")
    t = (await db.execute(select(Tenant).where(Tenant.id == tid))).scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    t.subscription_status = SubscriptionStatus.suspended if body.suspend else SubscriptionStatus.active
    t.is_active = not body.suspend
    await audit_record(db, current_user, "tenant.suspended" if body.suspend else "tenant.reactivated",
                       target=t.name, org_id=t.id)
    await db.commit()
    return {"id": str(t.id), "status": _status_label(t.subscription_status)}


@router.post("/{tenant_id}/authorize")
async def authorize_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Super Admin authorizes a pending MSP/Reseller account so it can sign in."""
    if current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found")
    t = (await db.execute(select(Tenant).where(Tenant.id == tid))).scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    t.activation_pending = False
    t.is_active = True
    t.subscription_status = SubscriptionStatus.active
    await audit_record(db, current_user, "tenant.authorized", target=t.name, org_id=t.id)
    await db.commit()
    return {"id": str(t.id), "activation_pending": False}


_AUDIT_LEVELS = {"self", "assisted", "audited"}


class AuditLevelBody(BaseModel):
    audit_level: str


@router.patch("/{tenant_id}/audit-level")
async def set_audit_level(
    tenant_id: str,
    body: AuditLevelBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set a client's engagement model: self / assisted / audited."""
    if current_user.role not in (UserRole.super_admin, UserRole.eva_auditor, UserRole.msp_admin):
        raise HTTPException(status_code=403, detail="Reviewer access required")
    if body.audit_level not in _AUDIT_LEVELS:
        raise HTTPException(status_code=400, detail="audit_level must be self, assisted or audited")
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found")
    t = (await db.execute(select(Tenant).where(Tenant.id == tid))).scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    # MSP can only set it for its own clients.
    if current_user.role == UserRole.msp_admin and t.parent_msp_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Out of scope")
    t.audit_level = body.audit_level
    await audit_record(db, current_user, "tenant.audit_level", target=t.name, detail=body.audit_level, org_id=t.id)
    await db.commit()
    return {"id": str(t.id), "audit_level": t.audit_level}


class ArchiveBody(BaseModel):
    archived: bool


@router.patch("/{tenant_id}/archive")
async def set_tenant_archive(
    tenant_id: str,
    body: ArchiveBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Archive/unarchive a tenant. Archived tenants keep all history but are hidden
    from selectors and every listing except Tenant Management."""
    if current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found")
    t = (await db.execute(select(Tenant).where(Tenant.id == tid))).scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if t.tenant_type == TenantType.eva_internal:
        raise HTTPException(status_code=400, detail="The EVA internal tenant can't be archived")
    t.archived = body.archived
    t.archived_at = datetime.now(timezone.utc) if body.archived else None
    await audit_record(db, current_user, "tenant.archived" if body.archived else "tenant.restored",
                       target=t.name, org_id=t.id)
    await db.commit()
    return {"id": str(t.id), "archived": t.archived}


# ════════════════ PER-CLIENT FRAMEWORK MANAGEMENT (EVA / MSP) ════════════════
BILLING_TYPES = {"recurring", "one_time", "none"}


async def _scoped_tenant(db: AsyncSession, current_user: User, tenant_id: str) -> Tenant:
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found")
    t = (await db.execute(select(Tenant).where(Tenant.id == tid))).scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if current_user.role == UserRole.super_admin:
        return t
    if current_user.role == UserRole.msp_admin and t.parent_msp_id == current_user.tenant_id:
        return t
    raise HTTPException(status_code=403, detail="Not allowed to manage this client")


def _billing_map(t: Tenant) -> dict:
    return dict((t.settings or {}).get("framework_billing", {}))


async def _frameworks_payload(db: AsyncSession, t: Tenant) -> dict:
    billing = _billing_map(t)
    # frameworks the client currently has = distinct frameworks among their org-controls
    assigned_ids = (await db.execute(
        select(func.distinct(Control.framework_id))
        .join(OrgControl, OrgControl.control_id == Control.id)
        .where(OrgControl.org_id == t.id)
    )).scalars().all()
    assigned_ids = [fid for fid in assigned_ids if fid]
    fw_rows = (await db.execute(select(Framework))).scalars().all()
    fw_by_id = {f.id: f for f in fw_rows}

    # A framework is "assigned" if it has provisioned controls OR it was
    # explicitly added (billed) — so a framework with no/zero provisioned
    # controls still appears in the list instead of silently vanishing.
    for key in billing.keys():
        try:
            bid = uuid.UUID(str(key))
        except (ValueError, TypeError):
            continue
        if bid in fw_by_id and bid not in assigned_ids:
            assigned_ids.append(bid)

    assigned = []
    for fid in assigned_ids:
        fw = fw_by_id.get(fid)
        if not fw:
            continue
        provisioned = (await db.execute(
            select(func.count(OrgControl.id))
            .join(Control, Control.id == OrgControl.control_id)
            .where(OrgControl.org_id == t.id, Control.framework_id == fid)
        )).scalar_one()
        total = (await db.execute(
            select(func.count(Control.id)).where(Control.framework_id == fid)
        )).scalar_one()
        meta = billing.get(str(fid), {})
        assigned.append({
            "framework_id": str(fid), "name": fw.name, "version": fw.version,
            "controls": total, "provisioned": provisioned,
            "billing_type": meta.get("billing_type", "none"),
            "amount": meta.get("amount", 0), "added_at": meta.get("added_at"),
        })
    assigned.sort(key=lambda x: x["name"])

    available = []
    for f in fw_rows:
        if f.id in assigned_ids:
            continue
        total = (await db.execute(
            select(func.count(Control.id)).where(Control.framework_id == f.id)
        )).scalar_one()
        available.append({"framework_id": str(f.id), "name": f.name, "version": f.version, "controls": total})
    available.sort(key=lambda x: x["name"])

    return {
        "tenant_id": str(t.id), "tenant_name": t.name,
        "monthly_price": t.monthly_price or 0,
        "assigned": assigned, "available": available,
    }


@router.get("/{tenant_id}/frameworks")
async def get_tenant_frameworks(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    t = await _scoped_tenant(db, current_user, tenant_id)
    return await _frameworks_payload(db, t)


@router.post("/{tenant_id}/frameworks/sync")
async def sync_tenant_frameworks(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ensure every control of the client's assigned frameworks has an
    org-control row. Fixes clients whose provisioning was lost (e.g. after a
    framework re-import). Assigned = frameworks with existing rows ∪ billed ones."""
    t = await _scoped_tenant(db, current_user, tenant_id)
    have = set((await db.execute(
        select(func.distinct(Control.framework_id))
        .join(OrgControl, OrgControl.control_id == Control.id)
        .where(OrgControl.org_id == t.id)
    )).scalars().all())
    fids = {str(f) for f in have if f} | set(_billing_map(t).keys())
    created = await assign_frameworks(db, t.id, list(fids)) if fids else 0
    if created:
        await db.commit()
    payload = await _frameworks_payload(db, t)
    payload["synced"] = created
    return payload


class AddFrameworkBody(BaseModel):
    framework_id: str
    billing_type: str = "recurring"   # recurring | one_time | none
    amount: int = 0


@router.post("/{tenant_id}/frameworks")
async def add_tenant_framework(
    tenant_id: str,
    body: AddFrameworkBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    t = await _scoped_tenant(db, current_user, tenant_id)
    if body.billing_type not in BILLING_TYPES:
        raise HTTPException(status_code=400, detail="Invalid billing type")
    try:
        fid = uuid.UUID(body.framework_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid framework id")
    fw = (await db.execute(select(Framework).where(Framework.id == fid))).scalar_one_or_none()
    if not fw:
        raise HTTPException(status_code=404, detail="Framework not found")

    created = await assign_frameworks(db, t.id, [str(fid)])
    if created == 0:
        # already had controls for this framework
        existing = (await db.execute(
            select(func.count(OrgControl.id))
            .join(Control, Control.id == OrgControl.control_id)
            .where(OrgControl.org_id == t.id, Control.framework_id == fid)
        )).scalar_one()
        if existing:
            raise HTTPException(status_code=400, detail="Client already has this framework")

    amount = max(0, int(body.amount or 0))
    billing = _billing_map(t)
    billing[str(fid)] = {
        "billing_type": body.billing_type, "amount": amount,
        "name": fw.name, "added_at": datetime.now(timezone.utc).isoformat(),
        "added_by": current_user.email,
    }
    t.settings = {**(t.settings or {}), "framework_billing": billing}
    if body.billing_type == "recurring":
        t.monthly_price = (t.monthly_price or 0) + amount
    await db.commit()
    return await _frameworks_payload(db, t)


@router.delete("/{tenant_id}/frameworks/{framework_id}")
async def remove_tenant_framework(
    tenant_id: str,
    framework_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    t = await _scoped_tenant(db, current_user, tenant_id)
    try:
        fid = uuid.UUID(framework_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Framework not found")

    control_ids = (await db.execute(
        select(Control.id).where(Control.framework_id == fid)
    )).scalars().all()
    if control_ids:
        oc_ids = (await db.execute(
            select(OrgControl.id).where(OrgControl.org_id == t.id, OrgControl.control_id.in_(control_ids))
        )).scalars().all()
        if oc_ids:
            await db.execute(delete(EvidenceItem).where(EvidenceItem.org_control_id.in_(oc_ids)))
        await db.execute(delete(ExpectedEvidence).where(
            ExpectedEvidence.org_id == t.id, ExpectedEvidence.control_id.in_(control_ids)))
        await db.execute(delete(OrgControl).where(
            OrgControl.org_id == t.id, OrgControl.control_id.in_(control_ids)))

    billing = _billing_map(t)
    meta = billing.pop(str(fid), None)
    t.settings = {**(t.settings or {}), "framework_billing": billing}
    if meta and meta.get("billing_type") == "recurring":
        t.monthly_price = max(0, (t.monthly_price or 0) - int(meta.get("amount", 0)))
    await db.commit()
    return await _frameworks_payload(db, t)


# ════════════════ PER-CLIENT DATA EXPORT (Super Admin) ════════════════

def _row(obj, fields: list[str]) -> dict:
    out = {}
    for f in fields:
        v = getattr(obj, f, None)
        if isinstance(v, (datetime, date)):
            v = v.isoformat()
        elif isinstance(v, uuid.UUID):
            v = str(v)
        elif hasattr(v, "value"):  # enum
            v = v.value
        out[f] = v
    return out


@router.get("/{tenant_id}/export")
async def export_tenant(tenant_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Download one tenant's data as JSON (no secrets). Super Admin only."""
    if current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found")
    t = (await db.execute(select(Tenant).where(Tenant.id == tid))).scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")

    from app.models.recommendation import Recommendation
    from app.models.support import SupportCase, SupportComment

    users = (await db.execute(select(User).where(User.tenant_id == tid))).scalars().all()
    ocs = (await db.execute(select(OrgControl).where(OrgControl.org_id == tid))).scalars().all()
    ee = (await db.execute(select(ExpectedEvidence).where(ExpectedEvidence.org_id == tid))).scalars().all()
    ev = (await db.execute(select(EvidenceItem).where(EvidenceItem.org_id == tid))).scalars().all()
    recs = (await db.execute(select(Recommendation).where(Recommendation.org_id == tid))).scalars().all()
    cases = (await db.execute(select(SupportCase).where(SupportCase.org_id == tid))).scalars().all()
    case_ids = [c.id for c in cases]
    comments = []
    if case_ids:
        comments = (await db.execute(select(SupportComment).where(SupportComment.case_id.in_(case_ids)))).scalars().all()

    # control ref/title lookup so the export is human-readable
    ctrl_ids = {oc.control_id for oc in ocs} | {e.control_id for e in ee}
    ctrl_map = {}
    if ctrl_ids:
        for c in (await db.execute(select(Control).where(Control.id.in_(ctrl_ids)))).scalars().all():
            ctrl_map[c.id] = {"ref": c.ref, "title": c.title}

    data = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exported_by": current_user.email,
        "tenant": _row(t, ["id", "name", "tenant_type", "subscription_status", "plan_name",
                           "monthly_price", "audit_level", "archived", "created_at"]),
        "users": [_row(u, ["id", "email", "display_name", "role", "is_active", "mfa_enabled", "last_login_at"]) for u in users],
        "org_controls": [{**_row(oc, ["id", "control_id", "status", "audit_status", "coverage_pct",
                                      "client_response", "remediation_notes", "due_date", "created_at"]),
                          "control": ctrl_map.get(oc.control_id)} for oc in ocs],
        "expected_evidence": [{**_row(e, ["id", "control_id", "text", "evidence_type", "frequency", "origin", "satisfied"]),
                               "control": ctrl_map.get(e.control_id)} for e in ee],
        "evidence_items": [_row(e, ["id", "org_control_id", "title", "description", "file_name", "file_size",
                                    "file_type", "checksum_sha256", "status", "frequency", "expires_at", "created_at"]) for e in ev],
        "recommendations": [_row(r, ["id", "control_id", "title", "text", "effort", "impact", "status", "is_top10", "created_at"]) for r in recs],
        "support_cases": [_row(c, ["id", "subject", "category", "message", "status", "created_at"]) for c in cases],
        "support_comments": [_row(cm, ["id", "case_id", "author_name", "author_role", "is_eva", "body", "created_at"]) for cm in comments],
        "counts": {"users": len(users), "controls": len(ocs), "evidence": len(ev),
                   "recommendations": len(recs), "support_cases": len(cases)},
    }
    safe = "".join(ch if ch.isalnum() else "_" for ch in (t.name or "client")).strip("_") or "client"
    await audit_record(db, current_user, "tenant.exported", target=t.name, org_id=t.id)
    await db.commit()
    return JSONResponse(content=data, headers={"Content-Disposition": f'attachment; filename="client_{safe}.json"'})
