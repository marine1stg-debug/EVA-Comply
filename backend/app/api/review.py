"""
Review API — the evidence approval workflow.

Two stages, chosen by the caller's role:
  • MSP roles  → see evidence in `msp_pending` from their clients, and can
                 Approve (→ forward to EVA), Flag, or Return to client.
  • EVA roles  → see evidence in `eva_pending` across all clients, and can
                 Accept, Reject, request Needs-more, or mark N/A.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
import uuid

from app.core.database import get_db
from app.core.entitlements import ensure_active
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantType
from app.models.framework import Control, Framework
from app.models.evidence import (
    OrgControl, OrgControlStatus, AuditDecision, EvidenceItem, EvidenceStatus,
)

router = APIRouter()

MSP_ROLES = {UserRole.msp_admin, UserRole.msp_analyst}
EVA_ROLES = {UserRole.super_admin, UserRole.eva_auditor}
_DONE = {OrgControlStatus.implemented, OrgControlStatus.verified}
_PENDING_EV = {EvidenceStatus.client_submitted, EvidenceStatus.msp_pending, EvidenceStatus.eva_pending}


@router.get("/clients")
async def review_clients(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Clients the current reviewer may view — drives the header client selector."""
    if current_user.role in EVA_ROLES:
        rows = (await db.execute(
            select(Tenant).where(Tenant.tenant_type == TenantType.single_client, Tenant.archived == False)  # noqa: E712
        )).scalars().all()
    elif current_user.role in MSP_ROLES:
        rows = (await db.execute(
            select(Tenant).where(Tenant.parent_msp_id == current_user.tenant_id, Tenant.archived == False)  # noqa: E712
        )).scalars().all()
    else:
        return {"clients": []}

    out = []
    for t in rows:
        statuses = (await db.execute(
            select(OrgControl.status).where(OrgControl.org_id == t.id)
        )).scalars().all()
        total = len(statuses)
        done = sum(1 for s in statuses if s in _DONE)
        pending = (await db.execute(
            select(func.count(EvidenceItem.id)).where(
                EvidenceItem.org_id == t.id, EvidenceItem.status.in_(_PENDING_EV))
        )).scalar_one()
        out.append({"id": str(t.id), "name": t.name, "controls": total,
                    "compliance": round(done / total * 100) if total else 0,
                    "pending_review": pending})
    out.sort(key=lambda x: x["name"])
    return {"clients": out}

EXT_ICON = {
    "pdf": "📄", "xlsx": "📊", "xls": "📊", "csv": "📊", "png": "🖼", "jpg": "🖼",
    "jpeg": "🖼", "zip": "🗜", "doc": "📝", "docx": "📝", "mp4": "🎬",
}

MSP_ACTIONS = [
    {"action": "approve", "label": "✓ Approve & Forward to EVA", "cls": "q-approve"},
    {"action": "flag", "label": "⚑ Flag Issue", "cls": "q-flag"},
    {"action": "return", "label": "↩ Return to Client", "cls": "q-return"},
]
EVA_ACTIONS = [
    {"action": "accept", "label": "✓ Accept", "cls": "q-approve"},
    {"action": "reject", "label": "✗ Reject", "cls": "q-flag"},
    {"action": "needs_more", "label": "⏳ Needs more", "cls": "q-return"},
    {"action": "na", "label": "— Not applicable", "cls": "q-return"},
]


def _stage(user: User) -> str:
    if user.role in MSP_ROLES:
        return "msp"
    if user.role in EVA_ROLES:
        return "eva"
    return "none"


async def _client_org_ids(db: AsyncSession, user: User):
    if user.role in MSP_ROLES:
        rows = await db.execute(
            select(Tenant.id).where(Tenant.parent_msp_id == user.tenant_id, Tenant.archived == False)  # noqa: E712
        )
        return list(rows.scalars().all())
    rows = await db.execute(
        select(Tenant.id).where(Tenant.tenant_type == TenantType.single_client, Tenant.archived == False)  # noqa: E712
    )
    return list(rows.scalars().all())


def _icon(name) -> str:
    ext = (name or "").rsplit(".", 1)[-1].lower() if name and "." in name else ""
    return EXT_ICON.get(ext, "📎")


@router.get("/queue")
async def review_queue(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stage = _stage(current_user)
    if stage == "none":
        raise HTTPException(status_code=403, detail="Review queue is for MSP and EVA roles only")

    org_ids = await _client_org_ids(db, current_user)
    target_status = EvidenceStatus.msp_pending if stage == "msp" else EvidenceStatus.eva_pending

    items = []
    if org_ids:
        rows = await db.execute(
            select(EvidenceItem, Control.ref, Control.title, Framework.name,
                   Tenant.name, User.display_name)
            .join(OrgControl, OrgControl.id == EvidenceItem.org_control_id)
            .join(Control, Control.id == OrgControl.control_id)
            .join(Framework, Framework.id == Control.framework_id)
            .join(Tenant, Tenant.id == EvidenceItem.org_id)
            .join(User, User.id == EvidenceItem.collected_by)
            .where(EvidenceItem.org_id.in_(org_ids), EvidenceItem.status == target_status)
            .order_by(EvidenceItem.created_at.desc())
        )
        for ev, ref, ctitle, fw, client, who in rows.all():
            items.append({
                "id": str(ev.id),
                "client": client,
                "ctrl_ref": ref,
                "ctrl_name": ctitle,
                "ev_title": ev.title,
                "ev_icon": _icon(ev.file_name),
                "by": who,
                "submitted": ev.created_at.strftime("%b %d, %Y") if ev.created_at else "—",
                "size": _humanize(ev.file_size),
                "framework": fw,
                "client_note": ev.description or "",
            })

    return {
        "stage": stage,
        "actions": MSP_ACTIONS if stage == "msp" else EVA_ACTIONS,
        "items": items,
        "clients": sorted({i["client"] for i in items}),
    }


def _humanize(n) -> str:
    if not n:
        return "—"
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.0f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


class DecisionBody(BaseModel):
    action: str
    note: str = ""


# action → (new evidence status, optional org-control audit decision, optional org-control status)
MSP_MAP = {
    "approve": (EvidenceStatus.eva_pending, None, None),
    "flag": (EvidenceStatus.msp_flagged, None, None),
    "return": (EvidenceStatus.needs_more, None, None),
}
EVA_MAP = {
    "accept": (EvidenceStatus.accepted, AuditDecision.accepted, OrgControlStatus.verified),
    "reject": (EvidenceStatus.rejected, AuditDecision.rejected, None),
    "needs_more": (EvidenceStatus.needs_more, AuditDecision.needs_more_evidence, None),
    "na": (EvidenceStatus.not_applicable, AuditDecision.not_applicable, OrgControlStatus.non_applicable),
}


@router.post("/{evidence_id}/decision")
async def review_decision(
    evidence_id: str,
    body: DecisionBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stage = _stage(current_user)
    if stage == "none":
        raise HTTPException(status_code=403, detail="Not permitted")
    await ensure_active(db, current_user)
    mapping = MSP_MAP if stage == "msp" else EVA_MAP
    if body.action not in mapping:
        raise HTTPException(status_code=400, detail=f"Unknown action '{body.action}'")

    try:
        eid = uuid.UUID(evidence_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Evidence not found")

    ev = (await db.execute(select(EvidenceItem).where(EvidenceItem.id == eid))).scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    # Confirm the item is in this reviewer's scope/stage
    org_ids = await _client_org_ids(db, current_user)
    expected = EvidenceStatus.msp_pending if stage == "msp" else EvidenceStatus.eva_pending
    if ev.org_id not in org_ids or ev.status != expected:
        raise HTTPException(status_code=409, detail="Item is not awaiting your review")

    new_status, decision, oc_status = mapping[body.action]
    ev.status = new_status

    oc = (await db.execute(
        select(OrgControl).where(OrgControl.id == ev.org_control_id)
    )).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if oc:
        if stage == "msp":
            oc.msp_response = body.note or oc.msp_response
            ev.msp_reviewer_id = current_user.id
            ev.msp_reviewed_at = now
            ev.msp_pre_status = body.action
        else:  # eva
            oc.auditor_id = current_user.id
            oc.auditor_notes = body.note or oc.auditor_notes
            oc.decided_at = now
            if decision:
                oc.audit_decision = decision
            if oc_status:
                oc.status = oc_status
                if oc_status == OrgControlStatus.verified:
                    oc.coverage_pct = 100

    await db.commit()
    return {"id": str(ev.id), "status": ev.status.value, "action": body.action}
