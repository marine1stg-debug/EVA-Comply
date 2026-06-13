"""Per-client, per-framework maturity assessment.

Domain-level 0–5 ratings with Current / Target / Previous series. Current is
auto-seeded from each domain's compliance and overridable by reviewers.
"""
import uuid
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.auth import get_current_user
from app.core.client_context import resolve_org, CLIENT_ROLES
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantType
from app.models.framework import Framework, Control
from app.models.evidence import OrgControl
from app.models.maturity import MaturityAssessment, MaturitySnapshot
from app.models.self_assessment import SelfAssessment
from app.core.maturity_questions import perceived_level

router = APIRouter()

EDIT_ROLES = {UserRole.super_admin, UserRole.eva_auditor, UserRole.msp_admin, UserRole.msp_analyst}
RISK_WEIGHT = {"low": 1, "medium": 2, "high": 3, "critical": 4}
DEFAULT_TARGET = 4


def _risk_value(r) -> str:
    return r.value if hasattr(r, "value") else (r or "low")


def _compliance_level(compliant: int, total: int) -> int:
    """Map a domain's compliance ratio onto the 0–5 maturity scale."""
    if total <= 0:
        return 0
    return round(compliant / total * 5)


async def _subscribed_frameworks(db: AsyncSession, org_id):
    rows = (await db.execute(
        select(Framework.id, Framework.name)
        .join(Control, Control.framework_id == Framework.id)
        .join(OrgControl, OrgControl.control_id == Control.id)
        .where(OrgControl.org_id == org_id)
        .distinct()
    )).all()
    return [{"id": str(fid), "name": name} for fid, name in rows]


@router.get("/frameworks")
async def maturity_frameworks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = await resolve_org(db, current_user)
    if org_id is None:
        # Reviewer with no client selected vs. a client with nothing provisioned.
        return {"frameworks": [], "needs_client": current_user.role not in CLIENT_ROLES}
    return {"frameworks": await _subscribed_frameworks(db, org_id), "needs_client": False}


async def _build(db: AsyncSession, org_id, framework: Framework, can_edit: bool):
    # Pull every control in this framework that the client is subscribed to,
    # with its domain, risk, and the client's audit status.
    rows = (await db.execute(
        select(Control.domain, Control.risk_rating, OrgControl.audit_status)
        .outerjoin(OrgControl, and_(OrgControl.control_id == Control.id, OrgControl.org_id == org_id))
        .where(Control.framework_id == framework.id)
    )).all()

    # Aggregate per domain.
    agg: dict[str, dict] = {}
    for domain, risk, audit_status in rows:
        d = domain or "General"
        a = agg.setdefault(d, {"total": 0, "compliant": 0, "risk_w": 0})
        a["total"] += 1
        if (audit_status or "") == "compliant":
            a["compliant"] += 1
        a["risk_w"] = max(a["risk_w"], RISK_WEIGHT.get(_risk_value(risk), 1))

    # Perceived (client self-assessment) levels per domain.
    sa_rows = (await db.execute(
        select(Control.domain, SelfAssessment.answers)
        .join(SelfAssessment, and_(SelfAssessment.control_id == Control.id, SelfAssessment.org_id == org_id))
        .where(Control.framework_id == framework.id)
    )).all()
    perc_by_domain: dict[str, list] = {}
    all_perc: list = []
    for domain, answers in sa_rows:
        lvl = perceived_level(answers or {})
        if lvl is not None:
            perc_by_domain.setdefault(domain or "General", []).append(lvl)
            all_perc.append(lvl)

    # Stored overrides.
    stored = {a.domain: a for a in (await db.execute(
        select(MaturityAssessment).where(
            MaturityAssessment.org_id == org_id, MaturityAssessment.framework_id == framework.id
        )
    )).scalars().all()}

    # Latest snapshot → previous levels.
    snap = (await db.execute(
        select(MaturitySnapshot)
        .where(MaturitySnapshot.org_id == org_id, MaturitySnapshot.framework_id == framework.id)
        .order_by(MaturitySnapshot.taken_at.desc())
    )).scalars().first()
    prev_map = {row["domain"]: row["level"] for row in (snap.payload or [])} if snap else {}

    domains = []
    cur_sum = tgt_sum = prev_sum = 0
    risk_num = risk_den = 0
    RISK_LABEL = {1: "low", 2: "medium", 3: "high", 4: "critical"}
    for name in sorted(agg.keys()):
        a = agg[name]
        auto = _compliance_level(a["compliant"], a["total"])
        ov = stored.get(name)
        current = ov.current_level if (ov and ov.current_level is not None) else auto
        target = ov.target_level if (ov and ov.target_level is not None) else DEFAULT_TARGET
        prev = prev_map.get(name)
        risk_w = a["risk_w"]
        gap = max(0, target - current)
        risk_num += gap * risk_w
        risk_den += DEFAULT_TARGET * risk_w
        cur_sum += current
        tgt_sum += target
        prev_sum += (prev if prev is not None else current)
        pvals = perc_by_domain.get(name, [])
        perceived = round(sum(pvals) / len(pvals), 1) if pvals else None
        domains.append({
            "domain": name,
            "controls": a["total"],
            "compliant": a["compliant"],
            "auto_level": auto,
            "current": current,
            "perceived": perceived,
            "target": target,
            "previous": prev,
            "current_overridden": bool(ov and ov.current_level is not None),
            "target_set": bool(ov and ov.target_level is not None),
            "note": ov.note if ov else None,
            "risk": RISK_LABEL.get(risk_w, "low"),
        })

    n = len(domains) or 1
    overall_current = round(cur_sum / n, 1)
    overall_target = round(tgt_sum / n, 1)
    overall_previous = round(prev_sum / n, 1) if snap else None
    overall_perceived = round(sum(all_perc) / len(all_perc), 1) if all_perc else None
    risk_score = round(risk_num / risk_den * 100) if risk_den else 0

    return {
        "framework": {"id": str(framework.id), "name": framework.name},
        "domains": domains,
        "overall_current": overall_current,
        "overall_perceived": overall_perceived,
        "overall_target": overall_target,
        "overall_previous": overall_previous,
        "risk_score": risk_score,
        "scale_max": 5,
        "can_edit": can_edit,
        "snapshot_at": snap.taken_at.strftime("%b %d, %Y") if snap else None,
    }


async def _load_fw(db, framework_id) -> Framework:
    try:
        fid = uuid.UUID(framework_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Framework not found")
    fw = (await db.execute(select(Framework).where(Framework.id == fid))).scalar_one_or_none()
    if not fw:
        raise HTTPException(status_code=404, detail="Framework not found")
    return fw


async def _overall(db: AsyncSession, org_id) -> dict:
    """Org-level Perceived vs Assessed maturity across all subscribed frameworks."""
    fws = await _subscribed_frameworks(db, org_id)
    if not fws:
        return {"perceived": None, "assessed": 0, "target": 0, "gap": None,
                "risk_score": 0, "scale_max": 5, "has_data": False}
    fw_ids = [uuid.UUID(f["id"]) for f in fws]
    fw_rows = {f.id: f for f in (await db.execute(
        select(Framework).where(Framework.id.in_(fw_ids))
    )).scalars().all()}
    assessed, target, risk, perc = [], [], [], []
    for fid in fw_ids:
        fw = fw_rows.get(fid)
        if not fw:
            continue
        b = await _build(db, org_id, fw, False)
        assessed.append(b["overall_current"])
        target.append(b["overall_target"])
        risk.append(b["risk_score"])
        if b["overall_perceived"] is not None:
            perc.append(b["overall_perceived"])
    a = round(sum(assessed) / len(assessed), 1) if assessed else 0
    t = round(sum(target) / len(target), 1) if target else 0
    p = round(sum(perc) / len(perc), 1) if perc else None
    r = round(sum(risk) / len(risk)) if risk else 0
    return {
        "perceived": p, "assessed": a, "target": t,
        "gap": (round(p - a, 1) if p is not None else None),
        "risk_score": r, "scale_max": 5, "has_data": True,
    }


@router.get("/summary")
async def maturity_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Perceived vs Assessed maturity for the in-scope client (dashboard card)."""
    org_id = await resolve_org(db, current_user)
    if org_id is None:
        return {"has_data": False, "needs_client": current_user.role not in CLIENT_ROLES}
    out = await _overall(db, org_id)
    out["needs_client"] = False
    return out


@router.get("/portfolio")
async def maturity_portfolio(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Per-client Perceived vs Assessed gap across an MSP's / EVA's clients."""
    if current_user.role == UserRole.super_admin:
        tenants = (await db.execute(
            select(Tenant).where(Tenant.tenant_type == TenantType.single_client, Tenant.archived == False)  # noqa: E712
        )).scalars().all()
    elif current_user.role in (UserRole.msp_admin, UserRole.msp_analyst):
        tenants = (await db.execute(
            select(Tenant).where(Tenant.parent_msp_id == current_user.tenant_id, Tenant.archived == False)  # noqa: E712
        )).scalars().all()
    else:
        raise HTTPException(status_code=403, detail="Portfolio access required")
    clients = []
    for t in tenants:
        o = await _overall(db, t.id)
        clients.append({"id": str(t.id), "name": t.name, **o})
    # Biggest overrating gap first (perceived far above assessed).
    clients.sort(key=lambda c: (c["gap"] if c["gap"] is not None else -999), reverse=True)
    return {"clients": clients}


@router.get("/{framework_id}")
async def get_maturity(
    framework_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = await resolve_org(db, current_user)
    if org_id is None:
        raise HTTPException(status_code=400, detail="No client organization in scope")
    fw = await _load_fw(db, framework_id)
    return await _build(db, org_id, fw, current_user.role in EDIT_ROLES)


class DomainUpdate(BaseModel):
    domain: str
    current_level: Optional[int] = None
    target_level: Optional[int] = None
    note: Optional[str] = None
    clear_current: bool = False   # revert current to auto (compliance-derived)


@router.patch("/{framework_id}/domain")
async def update_domain(
    framework_id: str,
    body: DomainUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in EDIT_ROLES:
        raise HTTPException(status_code=403, detail="Only reviewers can edit maturity ratings")
    org_id = await resolve_org(db, current_user)
    if org_id is None:
        raise HTTPException(status_code=400, detail="No client organization in scope")
    fw = await _load_fw(db, framework_id)
    name = (body.domain or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="domain is required")
    for lvl in (body.current_level, body.target_level):
        if lvl is not None and not (0 <= lvl <= 5):
            raise HTTPException(status_code=400, detail="levels must be between 0 and 5")

    ass = (await db.execute(
        select(MaturityAssessment).where(
            MaturityAssessment.org_id == org_id,
            MaturityAssessment.framework_id == fw.id,
            MaturityAssessment.domain == name,
        )
    )).scalar_one_or_none()
    if ass is None:
        ass = MaturityAssessment(org_id=org_id, framework_id=fw.id, domain=name)
        db.add(ass)
    if body.clear_current:
        ass.current_level = None
    elif body.current_level is not None:
        ass.current_level = body.current_level
    if body.target_level is not None:
        ass.target_level = body.target_level
    if body.note is not None:
        ass.note = body.note.strip() or None
    await db.commit()
    return await _build(db, org_id, fw, True)


class SnapshotBody(BaseModel):
    label: Optional[str] = None


@router.post("/{framework_id}/snapshot")
async def take_snapshot(
    framework_id: str,
    body: SnapshotBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Freeze the current per-domain levels as a dated baseline → 'Previous'."""
    if current_user.role not in EDIT_ROLES:
        raise HTTPException(status_code=403, detail="Only reviewers can snapshot maturity")
    org_id = await resolve_org(db, current_user)
    if org_id is None:
        raise HTTPException(status_code=400, detail="No client organization in scope")
    fw = await _load_fw(db, framework_id)
    built = await _build(db, org_id, fw, True)
    payload = [{"domain": d["domain"], "level": d["current"]} for d in built["domains"]]
    db.add(MaturitySnapshot(
        org_id=org_id, framework_id=fw.id,
        taken_at=datetime.now(timezone.utc),
        label=(body.label or "").strip() or None,
        payload=payload, overall=built["overall_current"],
    ))
    await db.commit()
    return await _build(db, org_id, fw, True)
