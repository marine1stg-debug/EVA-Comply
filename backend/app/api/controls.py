"""
Controls API — list (with per-org status/coverage/evidence) and detail.
Org scope: client roles → own tenant; MSP/EVA roles → a client tenant in
their scope (the seeded demo client) so they see real posture.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from typing import Optional
import uuid
import os
import hashlib

from app.core.database import get_db
from app.core.config import settings
from app.core import storage
from app.core.i18n import get_lang, loc, loc_domain, has_fr, lines as _lines
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantType
from app.models.framework import Framework, Control, ControlRisk, ControlPriority
from app.models.evidence import (
    OrgControl, EvidenceItem, ExpectedEvidence, ControlEvent,
    OrgControlStatus, AuditDecision, EvidenceFrequency,
    EvidenceStatus, EvidenceSource, ControlStatus,
)
from app.models.self_assessment import SelfAssessment
from app.core.maturity_questions import generate_questions, perceived_level

MAX_BYTES = 50 * 1024 * 1024  # 50 MB

FREQS = [f.value for f in EvidenceFrequency]
EVIDENCE_TYPES = ["Document", "Policy", "Screenshot", "Log", "Configuration", "Report", "Record", "Other"]


def _coerce_freq(value) -> EvidenceFrequency:
    try:
        return EvidenceFrequency(str(value).strip().lower())
    except (ValueError, AttributeError):
        return EvidenceFrequency.annual

router = APIRouter()

CLIENT_ROLES = {UserRole.client_admin, UserRole.contributor, UserRole.viewer}
STATUS_BADGE = {
    "not_started": "b-red", "in_progress": "b-amber",
    "implemented": "b-green", "verified": "b-teal", "non_applicable": "b-gray",
}

# Audit-status (user-facing) presentation + reviewer gating.
REVIEWER_ROLES = {UserRole.super_admin, UserRole.eva_auditor,
                  UserRole.msp_admin, UserRole.msp_analyst}


def _is_coach(user: User) -> bool:
    """A coach can challenge controls (re-open them under review). Super admins
    always can; other reviewers need the can_coach flag."""
    if user.role == UserRole.super_admin:
        return True
    return user.role in REVIEWER_ROLES and bool(getattr(user, "can_coach", False))
AUDIT_LABEL = {
    "compliant": "Compliant", "non_compliant": "Non-Compliant",
    "in_progress": "In Progress", "not_applicable": "Not Applicable",
    "not_started": "Not Started",
}
AUDIT_LABEL_FR = {
    "compliant": "Conforme", "non_compliant": "Non conforme",
    "in_progress": "En cours", "not_applicable": "Non applicable",
    "not_started": "Non démarré",
}
AUDIT_BADGE = {
    "compliant": "b-green", "non_compliant": "b-red",
    "in_progress": "b-amber", "not_applicable": "b-gray",
    "not_started": "b-gray",
}


def audit_label(ds: str, lang: str) -> str:
    """Localized audit-status label, falling back to English."""
    if lang == "fr":
        return AUDIT_LABEL_FR.get(ds) or AUDIT_LABEL.get(ds, "Non démarré")
    return AUDIT_LABEL.get(ds, "Not Started")


def _display_status(oc, ev_count: int, has_self_assessment: bool) -> str:
    """User-facing status for a control.

    - Manual override (reviewer set it): use the stored audit status as-is.
    - Auto: Compliant when evidence is complete/accepted; In Progress once
      there's *any* activity (a self-assessment answer or deposited evidence);
      otherwise Not Started.
    """
    if oc is not None and oc.status_mode == "manual" and oc.audit_status:
        return oc.audit_status
    if oc is not None and oc.audit_status == "compliant":
        return "compliant"
    if ev_count > 0 or has_self_assessment:
        return "in_progress"
    return "not_started"
# Mirror a manual audit status back onto the legacy enum so dashboard/MSP
# rollups reflect the auditor's call.
_LEGACY_FROM_AUDIT = {
    "compliant": OrgControlStatus.verified,
    "non_compliant": OrgControlStatus.in_progress,
    "in_progress": OrgControlStatus.in_progress,
    "not_applicable": OrgControlStatus.non_applicable,
}
PRIORITY_BADGE = {"high": "b-red", "medium": "b-amber", "low": "b-green"}
RISK_BADGE = {"critical": "b-red", "high": "b-orange", "medium": "b-amber", "low": "b-green"}
EV_BADGE = {
    "accepted": "b-green", "needs_more": "b-amber", "draft": "b-gray",
    "rejected": "b-red", "client_submitted": "b-blue", "eva_pending": "b-blue",
    "msp_pending": "b-blue", "msp_approved": "b-teal",
}


async def _target_org(db: AsyncSession, user: User):
    """Org this request acts on — the selected client for reviewers, own tenant for clients."""
    from app.core.client_context import resolve_org
    return await resolve_org(db, user)


def _bp_list(control: Control) -> list:
    raw = control.evidence_best_practices or ""
    return [line.strip() for line in raw.split("\n") if line.strip()]


import re as _re
_POLICY_KW = _re.compile(r"\b(policy|policies|procedure|procedures|plan|rules of behavior|standard)\b", _re.I)
# control family (domain) → the policy template that documents it
_FAMILY_POLICY = [
    (("access", "control"), "Access Control Policy"),
    (("awareness",), "Security Awareness & Training Policy"),
    (("audit",), "Audit & Accountability Policy"),
    (("configuration",), "Configuration Management Policy"),
    (("identification",), "Identification & Authentication Policy"),
    (("incident",), "Incident Response Policy & Plan"),
    (("maintenance",), "System Maintenance Policy"),
    (("media",), "Media Protection Policy"),
    (("personnel",), "Personnel Security Policy"),
    (("physical",), "Physical Protection Policy"),
    (("risk", "assessment"), "Risk Assessment Policy"),
    (("security", "assessment"), "Security Assessment & Continuous Monitoring Policy"),
    (("communications",), "System & Communications Protection Policy"),
    (("information", "integrity"), "System & Information Integrity Policy"),
    (("planning",), "Information Security Program Plan (SSP)"),
    (("services", "acquisition"), "System & Services Acquisition Policy"),
    (("supply", "chain"), "Supply Chain Risk Management Policy"),
]


def _policy_template_for(control: Control):
    """Name of the policy template a control needs, or None if it doesn't call
    for a documented policy/procedure/plan."""
    blob = " ".join(filter(None, [
        control.description, control.evidence_best_practices, control.best_practices,
    ]))
    if not _POLICY_KW.search(blob or ""):
        return None
    dom = (control.domain or "").lower()
    for keys, name in _FAMILY_POLICY:
        if all(k in dom for k in keys):
            return name
    return "Information Security Policy"


async def _evidence_counts(db: AsyncSession, org_id) -> dict:
    if not org_id:
        return {}
    rows = await db.execute(
        select(EvidenceItem.org_control_id, func.count(EvidenceItem.id))
        .where(EvidenceItem.org_id == org_id)
        .group_by(EvidenceItem.org_control_id)
    )
    return {oc_id: n for oc_id, n in rows.all()}


async def _returned_counts(db: AsyncSession, org_id) -> dict:
    """Per-org-control count of evidence the auditor sent back (needs more /
    rejected) — i.e. items the client must act on."""
    if not org_id:
        return {}
    rows = await db.execute(
        select(EvidenceItem.org_control_id, func.count(EvidenceItem.id))
        .where(
            EvidenceItem.org_id == org_id,
            EvidenceItem.status.in_([EvidenceStatus.needs_more, EvidenceStatus.rejected]),
        )
        .group_by(EvidenceItem.org_control_id)
    )
    return {oc_id: n for oc_id, n in rows.all()}


@router.get("/")
async def list_controls(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang),
):
    org_id = await _target_org(db, current_user)

    fw_map = {fid: name for fid, name in (await db.execute(select(Framework.id, Framework.name))).all()}

    ocs = {}
    owners = {}
    if org_id:
        oc_rows = (await db.execute(
            select(OrgControl).where(OrgControl.org_id == org_id)
        )).scalars().all()
        ocs = {oc.control_id: oc for oc in oc_rows}
        owner_ids = {oc.owner_user_id for oc in oc_rows if oc.owner_user_id}
        if owner_ids:
            urows = await db.execute(
                select(User.id, User.display_name).where(User.id.in_(owner_ids))
            )
            owners = {uid: name for uid, name in urows.all()}
    # Controls the client has actually answered a self-assessment for.
    answered_sa = set()
    if org_id:
        sa_rows = (await db.execute(
            select(SelfAssessment.control_id, SelfAssessment.answers)
            .where(SelfAssessment.org_id == org_id)
        )).all()
        answered_sa = {cid for cid, answers in sa_rows if answers}

    # Scope to the client's subscribed frameworks, showing EVERY control in
    # those frameworks (not only the ones already provisioned). Subscription =
    # the frameworks the org has any org-control in. No org in scope → full catalog.
    if org_id is not None:
        sub_fws = list((await db.execute(
            select(Control.framework_id)
            .join(OrgControl, OrgControl.control_id == Control.id)
            .where(OrgControl.org_id == org_id)
            .distinct()
        )).scalars().all())
        controls = (await db.execute(
            select(Control).where(Control.framework_id.in_(sub_fws)).order_by(Control.sort_order)
        )).scalars().all() if sub_fws else []
    else:
        controls = (await db.execute(
            select(Control).order_by(Control.sort_order)
        )).scalars().all()

    ev_counts = await _evidence_counts(db, org_id)
    returned_counts = await _returned_counts(db, org_id)

    items = []
    total_ev = coll_ev = complete = missing = 0
    for c in controls:
        oc = ocs.get(c.id)
        status = oc.status.value if oc else "not_started"
        coverage = oc.coverage_pct if oc else 0
        ev_count = ev_counts.get(oc.id, 0) if oc else 0
        returned_count = returned_counts.get(oc.id, 0) if oc else 0
        ev_expected = max(len(_bp_list(c)), 1)
        owner = owners.get(oc.owner_user_id) if (oc and oc.owner_user_id) else None
        due = oc.due_date.isoformat() if (oc and oc.due_date) else None

        total_ev += ev_expected
        coll_ev += ev_count
        if ev_count >= ev_expected:
            complete += 1
        if ev_count == 0:
            missing += 1

        items.append({
            "id": str(c.id),
            "ref": c.ref,
            "title": loc(c, "title", lang),
            "framework": fw_map.get(c.framework_id, "—"),
            "domain": loc_domain(c.domain, lang) or "—",
            "level": c.level or "—",
            "priority": c.priority.value if c.priority else "low",
            "risk": c.risk_rating.value if c.risk_rating else "low",
            "category": c.control_category.value if c.control_category else "—",
            "status": status,
            "statusBadge": STATUS_BADGE.get(status, "b-gray"),
            "audit_status": (_ds := _display_status(oc, ev_count, c.id in answered_sa)),
            "audit_status_label": audit_label(_ds, lang),
            "audit_status_badge": AUDIT_BADGE.get(_ds, "b-gray"),
            "priorityBadge": PRIORITY_BADGE.get(c.priority.value if c.priority else "low", "b-gray"),
            "coverage": coverage,
            "returned_count": returned_count,
            "needs_action": returned_count > 0,
            "evidence_count": ev_count,
            "evidence_expected": ev_expected,
            "owner": owner,
            "due": due,
            "policy_template": _policy_template_for(c),
        })

    domains = sorted({c["domain"] for c in items if c["domain"] != "—"})
    frameworks = sorted({c["framework"] for c in items if c["framework"] != "—"})
    return {
        "items": items,
        "domains": domains,
        "frameworks": frameworks,
        "summary": {
            "total_evidence": total_ev,
            "collected_evidence": coll_ev,
            "complete": complete,
            "missing": missing,
        },
    }


@router.get("/{control_id}")
async def control_detail(
    control_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang),
):
    try:
        cid = uuid.UUID(control_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Control not found")

    control = (await db.execute(
        select(Control).where(Control.id == cid)
    )).scalar_one_or_none()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    framework = (await db.execute(
        select(Framework).where(Framework.id == control.framework_id)
    )).scalar_one_or_none()

    org_id = await _target_org(db, current_user)
    oc = None
    evidence = []
    if org_id:
        oc = (await db.execute(
            select(OrgControl).where(
                OrgControl.org_id == org_id, OrgControl.control_id == cid
            ).order_by(OrgControl.created_at.asc())
        )).scalars().first()
        if oc:
            erows = await db.execute(
                select(EvidenceItem, User.display_name)
                .join(User, User.id == EvidenceItem.collected_by)
                .where(EvidenceItem.org_control_id == oc.id)
                .order_by(EvidenceItem.created_at.desc())
            )
            for ev, who in erows.all():
                evidence.append({
                    "id": str(ev.id),
                    "title": ev.title,
                    "status": ev.status.value,
                    "statusBadge": EV_BADGE.get(ev.status.value, "b-gray"),
                    "review_state": _ee_state(ev),
                    "review_note": ev.review_note,
                    "file_name": ev.file_name,
                    "file_size": ev.file_size,
                    "can_preview": bool(ev.file_key),
                    "by": who,
                    "date": ev.created_at.strftime("%b %d, %Y") if ev.created_at else "—",
                    "note": ev.description,
                })

    owner = None
    if oc and oc.owner_user_id:
        owner = (await db.execute(
            select(User.display_name).where(User.id == oc.owner_user_id)
        )).scalar_one_or_none()

    # Live coverage + status from per-client expected evidence (auto, auditor overrides).
    _ee_rows, _ev_map, cov, status, ee_valid, ee_total, status_source = await _recompute(db, org_id, control, oc)
    await db.commit()
    # Display status: Not Started until a self-assessment is answered or evidence deposited.
    _has_sa = False
    if org_id:
        _sa = (await db.execute(
            select(SelfAssessment.answers).where(
                SelfAssessment.org_id == org_id, SelfAssessment.control_id == control.id
            )
        )).scalar_one_or_none()
        _has_sa = bool(_sa)
    _ds = _display_status(oc, len(evidence), _has_sa)
    expected = _lines(loc(control, "evidence_best_practices", lang)) or _bp_list(control)
    best = _lines(loc(control, "best_practices", lang))
    # English companion (for the per-control "View in English" toggle).
    english = {
        "title": control.title,
        "plain_language": control.plain_language or "",
        "objective": control.objective or "",
        "description": control.description or "",
        "discussion": control.discussion or "",
        "best_practices": _lines(control.best_practices),
        "expected_evidence": _bp_list(control),
    }
    fr_available = lang == "fr" and (
        has_fr(control, "plain_language") or has_fr(control, "description")
        or has_fr(control, "title") or has_fr(control, "discussion")
    )
    risk = control.risk_rating.value if control.risk_rating else "low"
    priority = control.priority.value if control.priority else "low"
    return {
        "id": str(control.id),
        "ref": control.ref,
        "title": loc(control, "title", lang),
        "domain": loc_domain(control.domain, lang) or "—",
        "english": english,
        "fr_available": fr_available,
        "level": control.level or "—",
        "category": control.control_category.value if control.control_category else "—",
        "framework": framework.name if framework else "—",
        "priority": priority,
        "priorityBadge": PRIORITY_BADGE.get(priority, "b-gray"),
        "risk": risk,
        "riskBadge": RISK_BADGE.get(risk, "b-gray"),
        "status": status,
        "statusBadge": STATUS_BADGE.get(status, "b-gray"),
        "status_source": status_source,
        "audit_status": (oc.audit_status if oc else ControlStatus.IN_PROGRESS) or ControlStatus.IN_PROGRESS,
        "audit_status_label": audit_label(_ds, lang),
        "audit_status_badge": AUDIT_BADGE.get(_ds, "b-gray"),
        "status_mode": (oc.status_mode if oc else "auto") or "auto",
        "status_note": oc.status_note if oc else None,
        "previous_audit_notes": oc.previous_audit_notes if oc else None,
        "audit_status_options": [
            {"value": v, "label": audit_label(v, lang)} for v in ControlStatus.ALL
        ],
        "can_review": current_user.role in REVIEWER_ROLES,
        "can_coach": _is_coach(current_user),
        "under_review": bool(oc and oc.under_review),
        "under_review_note": (oc.under_review_note if oc else None),
        "coverage": cov,
        "expected_valid": ee_valid,
        "expected_total": ee_total,
        "owner": owner,
        "due": oc.due_date.strftime("%b %d, %Y") if (oc and oc.due_date) else None,
        "plain_language": loc(control, "plain_language", lang),
        "objective": loc(control, "objective", lang),
        "description": loc(control, "description", lang),
        "discussion": loc(control, "discussion", lang),
        "video": (
            {"kind": "file", "url": None, "file": f"/videos/file/control/{control.id}"} if control.video_key
            else {"kind": "link", "url": control.video_url, "file": None} if control.video_url
            else {"kind": None, "url": None, "file": None}
        ),
        "best_practices": best,
        "expected_evidence": expected,
        "evidence_count": len(evidence),
        "evidence_expected": max(len(expected), 1),
        "evidence": evidence,
        "mappings": control.mappings or {},
        "policy_template": _policy_template_for(control),
    }


# ════════════════ COACH: PUT A CONTROL UNDER REVIEW ════════════════

class UnderReviewBody(BaseModel):
    under_review: bool
    note: Optional[str] = None


@router.post("/{control_id}/under-review")
async def set_under_review(
    control_id: str,
    body: UnderReviewBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """A coach challenges a control by putting it 'under review' (with a note), or
    clears it once satisfied. Reviewer-only auditors can't do this."""
    if not _is_coach(current_user):
        raise HTTPException(status_code=403, detail="Only a coach auditor can put a control under review")
    control = await _load_control(db, control_id)
    org_id = await _target_org(db, current_user)
    if org_id is None:
        raise HTTPException(status_code=400, detail="No client organization in scope")
    oc = await _get_or_create_oc(db, org_id, control.id)
    oc.under_review = body.under_review
    oc.under_review_note = (body.note or "").strip() or None if body.under_review else None
    await _log_event(db, org_id, control.id, None, current_user, "review",
                     (f"Put under review: {body.note}" if body.under_review else "Cleared under review"))
    await db.commit()
    return {"under_review": oc.under_review, "under_review_note": oc.under_review_note}


# ════════════════ EVA CATALOG EDIT (risk / priority) ════════════════

EVA_ROLES = {UserRole.super_admin, UserRole.eva_auditor}


class ControlMetaUpdate(BaseModel):
    risk: Optional[str] = None
    priority: Optional[str] = None


@router.patch("/{control_id}/meta")
async def update_control_meta(
    control_id: str,
    body: ControlMetaUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """EVA-only: curate a control's risk / priority in the shared catalog."""
    if current_user.role not in EVA_ROLES:
        raise HTTPException(status_code=403, detail="Only EVA can edit control risk and priority")
    control = await _load_control(db, control_id)
    if body.risk is not None:
        try:
            control.risk_rating = ControlRisk(body.risk.strip().lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid risk '{body.risk}'")
    if body.priority is not None:
        try:
            control.priority = ControlPriority(body.priority.strip().lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid priority '{body.priority}'")
    await db.commit()
    return {
        "risk": control.risk_rating.value if control.risk_rating else "low",
        "riskBadge": RISK_BADGE.get(control.risk_rating.value if control.risk_rating else "low", "b-gray"),
        "priority": control.priority.value if control.priority else "low",
        "priorityBadge": PRIORITY_BADGE.get(control.priority.value if control.priority else "low", "b-gray"),
    }


# ════════════════ EXPECTED EVIDENCE (per-client requirements) ════════════════

async def _load_control(db: AsyncSession, control_id: str) -> Control:
    try:
        cid = uuid.UUID(control_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Control not found")
    control = (await db.execute(select(Control).where(Control.id == cid))).scalar_one_or_none()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    return control


async def _get_or_create_oc(db: AsyncSession, org_id, control_id) -> OrgControl:
    oc = (await db.execute(
        select(OrgControl).where(OrgControl.org_id == org_id, OrgControl.control_id == control_id)
        .order_by(OrgControl.created_at.asc())
    )).scalars().first()
    if oc is None:
        oc = OrgControl(org_id=org_id, control_id=control_id,
                        status=OrgControlStatus.not_started, coverage_pct=0)
        db.add(oc)
        await db.flush()
    return oc


async def _seed_expected(db: AsyncSession, org_id, control: Control):
    """Return the org's expected-evidence rows for a control, creating the
    catalog base list on first access."""
    rows = (await db.execute(
        select(ExpectedEvidence)
        .where(ExpectedEvidence.org_id == org_id, ExpectedEvidence.control_id == control.id)
        .order_by(ExpectedEvidence.sort_order)
    )).scalars().all()
    if rows:
        return list(rows)
    base = _bp_list(control)  # authored expected-evidence lines from the catalog
    base_fr = [ln.strip() for ln in (control.evidence_best_practices_fr or "").split("\n") if ln.strip()]
    if base:
        # Two endpoints can seed concurrently on a single page load. A unique
        # index (org_id, control_id, text) makes this safe: seed inside a
        # SAVEPOINT and, if another request won the race, swallow the conflict
        # and just re-read the rows it created.
        try:
            async with db.begin_nested():
                for i, txt in enumerate(base):
                    db.add(ExpectedEvidence(
                        org_id=org_id, control_id=control.id, text=txt,
                        text_fr=(base_fr[i] if i < len(base_fr) else None),
                        frequency=EvidenceFrequency.annual, evidence_type="Document",
                        origin="catalog", sort_order=i, satisfied=False,
                    ))
        except IntegrityError:
            pass  # already seeded by a concurrent request
    rows = (await db.execute(
        select(ExpectedEvidence)
        .where(ExpectedEvidence.org_id == org_id, ExpectedEvidence.control_id == control.id)
        .order_by(ExpectedEvidence.sort_order)
    )).scalars().all()
    return list(rows)


def _derive_status(oc: OrgControl, coverage: int):
    """Auditor decision overrides; otherwise status follows coverage."""
    if oc.audit_decision == AuditDecision.accepted:
        return OrgControlStatus.verified, "auditor"
    if oc.audit_decision == AuditDecision.not_applicable:
        return OrgControlStatus.non_applicable, "auditor"
    if oc.audit_decision in (AuditDecision.rejected, AuditDecision.needs_more_evidence):
        return OrgControlStatus.in_progress, "auditor"
    if coverage >= 100:
        return OrgControlStatus.implemented, "auto"
    if coverage > 0:
        return OrgControlStatus.in_progress, "auto"
    return OrgControlStatus.not_started, "auto"


async def _log_event(db, org_id, control_id, evidence_id, user: User, action: str, detail: str = None):
    """Append a history event (caller commits)."""
    db.add(ControlEvent(
        org_id=org_id, control_id=control_id, evidence_id=evidence_id,
        actor_id=getattr(user, "id", None),
        actor_name=getattr(user, "display_name", None) or getattr(user, "email", None),
        action=action, detail=detail,
    ))


async def _evidence_for_ees(db: AsyncSession, org_id, control_id) -> dict:
    """Latest evidence item per expected-evidence id for this org+control."""
    rows = (await db.execute(
        select(EvidenceItem)
        .where(EvidenceItem.org_id == org_id, EvidenceItem.expected_evidence_id.isnot(None))
        .order_by(EvidenceItem.created_at.asc())
    )).scalars().all()
    out = {}
    for ev in rows:
        out[ev.expected_evidence_id] = ev  # later (newer) wins
    return out


def _ee_state(ev: Optional[EvidenceItem]) -> str:
    if not ev:
        return "missing"
    s = ev.status.value
    if s == "accepted":
        return "accepted"
    if s in ("needs_more", "rejected"):
        return "returned"
    return "submitted"


async def _recompute(db: AsyncSession, org_id, control: Control, oc: Optional[OrgControl] = None):
    """Re-derive coverage% and status from accepted evidence.
    Returns (rows, ev_map, coverage, status_str, valid, total, status_source)."""
    if org_id is None:
        return [], {}, 0, "not_started", 0, 0, "auto"
    if oc is None:
        oc = await _get_or_create_oc(db, org_id, control.id)
    rows = await _seed_expected(db, org_id, control)
    ev_map = await _evidence_for_ees(db, org_id, control.id)
    total = len(rows)
    valid = sum(1 for r in rows if _ee_state(ev_map.get(r.id)) == "accepted")
    flagged = any(_ee_state(ev_map.get(r.id)) == "returned" for r in rows)
    coverage = round(valid / total * 100) if total else 0
    status, source = _derive_status(oc, coverage)
    oc.coverage_pct = coverage
    oc.status = status
    # Audit-status layer: auto re-derives from evidence; manual is pinned and
    # mirrored back onto the legacy enum for rollups.
    if oc.status_mode == "manual" and oc.audit_status:
        oc.status = _LEGACY_FROM_AUDIT.get(oc.audit_status, oc.status)
    else:
        oc.audit_status = (ControlStatus.COMPLIANT
                           if (total > 0 and valid == total and not flagged)
                           else ControlStatus.IN_PROGRESS)
    return rows, ev_map, coverage, status.value, valid, total, source


def _ee_dict(r: ExpectedEvidence, ev: Optional[EvidenceItem], lang: str = "en") -> dict:
    state = _ee_state(ev)
    text = (r.text_fr or r.text) if lang == "fr" else r.text
    return {
        "id": str(r.id), "text": text, "frequency": r.frequency.value,
        "evidence_type": r.evidence_type, "origin": r.origin,
        "state": state, "satisfied": state == "accepted",
        "evidence": None if not ev else {
            "evidence_id": str(ev.id), "file_name": ev.file_name,
            "status": ev.status.value, "review_note": ev.review_note,
            "can_preview": bool(ev.file_key),
        },
    }


def _ee_payload(rows, ev_map, cov, status, valid, total, source, lang: str = "en") -> dict:
    return {
        "items": [_ee_dict(r, ev_map.get(r.id), lang) for r in rows],
        "coverage": cov, "status": status,
        "statusBadge": STATUS_BADGE.get(status, "b-gray"), "status_source": source,
        "valid": valid, "total": total,
        "frequencies": FREQS, "types": EVIDENCE_TYPES,
    }


class EECreate(BaseModel):
    text: str
    frequency: str = "annual"
    evidence_type: str = "Document"


class EEUpdate(BaseModel):
    frequency: Optional[str] = None
    evidence_type: Optional[str] = None
    satisfied: Optional[bool] = None


@router.get("/{control_id}/expected-evidence")
async def list_expected_evidence(
    control_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang),
):
    control = await _load_control(db, control_id)
    org_id = await _target_org(db, current_user)
    if org_id is None:
        raise HTTPException(status_code=400, detail="No client organization in scope")
    rows, ev_map, cov, status, valid, total, source = await _recompute(db, org_id, control)
    await db.commit()
    return _ee_payload(rows, ev_map, cov, status, valid, total, source, lang)


@router.post("/{control_id}/expected-evidence")
async def add_expected_evidence(
    control_id: str,
    body: EECreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang),
):
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    control = await _load_control(db, control_id)
    org_id = await _target_org(db, current_user)
    if org_id is None:
        raise HTTPException(status_code=400, detail="No client organization in scope")
    rows = await _seed_expected(db, org_id, control)
    order = max((r.sort_order for r in rows), default=-1) + 1
    db.add(ExpectedEvidence(
        org_id=org_id, control_id=control.id, text=text,
        frequency=_coerce_freq(body.frequency), evidence_type=(body.evidence_type or "Document"),
        origin="custom", sort_order=order, satisfied=False,
    ))
    await db.flush()
    rows, ev_map, cov, status, valid, total, source = await _recompute(db, org_id, control)
    await db.commit()
    return _ee_payload(rows, ev_map, cov, status, valid, total, source, lang)


async def _load_ee(db, org_id, ee_id) -> ExpectedEvidence:
    try:
        eid = uuid.UUID(ee_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Item not found")
    ee = (await db.execute(
        select(ExpectedEvidence).where(ExpectedEvidence.id == eid, ExpectedEvidence.org_id == org_id)
    )).scalar_one_or_none()
    if not ee:
        raise HTTPException(status_code=404, detail="Item not found")
    return ee


@router.patch("/{control_id}/expected-evidence/{ee_id}")
async def update_expected_evidence(
    control_id: str,
    ee_id: str,
    body: EEUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang),
):
    control = await _load_control(db, control_id)
    org_id = await _target_org(db, current_user)
    if org_id is None:
        raise HTTPException(status_code=400, detail="No client organization in scope")
    ee = await _load_ee(db, org_id, ee_id)
    if body.frequency is not None:
        ee.frequency = _coerce_freq(body.frequency)
    if body.evidence_type is not None:
        ee.evidence_type = body.evidence_type
    if body.satisfied is not None:
        ee.satisfied = body.satisfied
    await db.flush()
    rows, ev_map, cov, status, valid, total, source = await _recompute(db, org_id, control)
    await db.commit()
    return _ee_payload(rows, ev_map, cov, status, valid, total, source, lang)


@router.delete("/{control_id}/expected-evidence/{ee_id}")
async def delete_expected_evidence(
    control_id: str,
    ee_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang),
):
    control = await _load_control(db, control_id)
    org_id = await _target_org(db, current_user)
    if org_id is None:
        raise HTTPException(status_code=400, detail="No client organization in scope")
    ee = await _load_ee(db, org_id, ee_id)
    if ee.origin != "custom":
        raise HTTPException(status_code=400, detail="Only custom items can be removed")
    await db.delete(ee)
    await db.flush()
    rows, ev_map, cov, status, valid, total, source = await _recompute(db, org_id, control)
    await db.commit()
    return _ee_payload(rows, ev_map, cov, status, valid, total, source, lang)


@router.post("/{control_id}/evidence")
async def add_standalone_evidence(
    control_id: str,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an additional, standalone evidence item to a control (not tied to a
    specific expected-evidence requirement), with a title and an optional note
    documenting what it is. Goes through the same review pipeline."""
    title = (title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="A title is required")
    control = await _load_control(db, control_id)
    org_id = await _target_org(db, current_user)
    if org_id is None:
        raise HTTPException(status_code=400, detail="No client organization in scope")
    oc = await _get_or_create_oc(db, org_id, control.id)

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 50 MB limit")
    safe_name = os.path.basename(file.filename or "evidence")
    file_key = storage.save_bytes(f"{org_id}/{uuid.uuid4().hex}_{safe_name}", data)

    db.add(EvidenceItem(
        org_control_id=oc.id, expected_evidence_id=None, org_id=org_id,
        title=title[:280], description=((description or "").strip() or None),
        file_key=file_key, file_name=safe_name, file_size=len(data),
        file_type=file.content_type, checksum_sha256=hashlib.sha256(data).hexdigest(),
        source=EvidenceSource.upload, status=EvidenceStatus.eva_pending,
        frequency=EvidenceFrequency.once, collected_by=current_user.id,
    ))
    await _log_event(db, org_id, control.id, None, current_user, "collected",
                     f"Added evidence “{title[:120]}”")
    await db.commit()
    return {"ok": True}


@router.post("/{control_id}/expected-evidence/{ee_id}/collect")
async def collect_expected_evidence(
    control_id: str,
    ee_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang),
):
    """Upload a file against a specific expected-evidence requirement, which
    marks it satisfied (→ valid) and lifts the control's coverage."""
    control = await _load_control(db, control_id)
    org_id = await _target_org(db, current_user)
    if org_id is None:
        raise HTTPException(status_code=400, detail="No client organization in scope")
    ee = await _load_ee(db, org_id, ee_id)
    oc = await _get_or_create_oc(db, org_id, control.id)

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 50 MB limit")

    safe_name = os.path.basename(file.filename or "evidence")
    file_key = storage.save_bytes(f"{org_id}/{uuid.uuid4().hex}_{safe_name}", data)

    db.add(EvidenceItem(
        org_control_id=oc.id, expected_evidence_id=ee.id, org_id=org_id,
        title=(ee.text[:280] if ee.text else "Evidence"),
        file_key=file_key, file_name=safe_name, file_size=len(data),
        file_type=file.content_type, checksum_sha256=hashlib.sha256(data).hexdigest(),
        source=EvidenceSource.upload, status=EvidenceStatus.eva_pending,
        frequency=ee.frequency, collected_by=current_user.id,
    ))
    ee.satisfied = False  # uploaded → pending review; becomes valid only when accepted
    await _log_event(db, org_id, control.id, None, current_user, "collected", f"Uploaded “{safe_name}” for: {ee.text[:120]}")
    await db.flush()
    rows, ev_map, cov, status, valid, total, source = await _recompute(db, org_id, control)
    await db.commit()
    return _ee_payload(rows, ev_map, cov, status, valid, total, source, lang)


class EEReview(BaseModel):
    decision: str           # "accept" | "return"
    note: Optional[str] = None


@router.post("/{control_id}/expected-evidence/{ee_id}/review")
async def review_expected_evidence(
    control_id: str,
    ee_id: str,
    body: EEReview,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang),
):
    """Auditor accepts or returns the collected evidence for an expected item.
    Returning sets it to 'needs more' with a comment so the client must act."""
    if current_user.role not in (UserRole.super_admin, UserRole.eva_auditor,
                                 UserRole.msp_admin, UserRole.msp_analyst):
        raise HTTPException(status_code=403, detail="Only reviewers can accept or return evidence")
    if body.decision not in ("accept", "return"):
        raise HTTPException(status_code=400, detail="decision must be 'accept' or 'return'")
    control = await _load_control(db, control_id)
    org_id = await _target_org(db, current_user)
    if org_id is None:
        raise HTTPException(status_code=400, detail="No client organization in scope")
    ee = await _load_ee(db, org_id, ee_id)
    ev_map = await _evidence_for_ees(db, org_id, control.id)
    ev = ev_map.get(ee.id)
    if not ev:
        raise HTTPException(status_code=400, detail="No collected evidence to review")
    note = (body.note or "").strip() or None
    if body.decision == "accept":
        ev.status = EvidenceStatus.accepted
        ev.review_note = note
        ee.satisfied = True
        await _log_event(db, org_id, control.id, ev.id, current_user, "accepted", note)
    else:
        ev.status = EvidenceStatus.needs_more
        ev.review_note = note
        ee.satisfied = False
        await _log_event(db, org_id, control.id, ev.id, current_user, "returned", note or "Returned for changes")
    await db.flush()
    rows, ev_map, cov, status, valid, total, source = await _recompute(db, org_id, control)
    await db.commit()
    return _ee_payload(rows, ev_map, cov, status, valid, total, source, lang)


@router.get("/{control_id}/events")
async def control_events(
    control_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """History feed for a control (collected / accepted / returned / deleted)."""
    control = await _load_control(db, control_id)
    org_id = await _target_org(db, current_user)
    if org_id is None:
        return {"events": []}
    rows = (await db.execute(
        select(ControlEvent)
        .where(ControlEvent.org_id == org_id, ControlEvent.control_id == control.id)
        .order_by(ControlEvent.created_at.desc())
    )).scalars().all()
    ACTION_LABEL = {"collected": "Evidence uploaded", "accepted": "Evidence accepted",
                    "returned": "Evidence returned", "deleted": "Evidence removed",
                    "status": "Status changed"}
    return {"events": [{
        "id": str(e.id), "action": e.action, "label": ACTION_LABEL.get(e.action, e.action),
        "detail": e.detail, "actor": e.actor_name or "—",
        "date": e.created_at.strftime("%b %d, %Y %H:%M") if e.created_at else "—",
    } for e in rows]}


# ════════════════ EVIDENCE-ITEM REVIEW + AUDIT STATUS ════════════════

async def _load_evidence(db, org_id, evidence_id) -> EvidenceItem:
    try:
        eid = uuid.UUID(evidence_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Evidence not found")
    ev = (await db.execute(
        select(EvidenceItem).where(EvidenceItem.id == eid, EvidenceItem.org_id == org_id)
    )).scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return ev


class EvidenceReview(BaseModel):
    decision: str           # "accept" | "return"
    note: Optional[str] = None


@router.post("/{control_id}/evidence/{evidence_id}/review")
async def review_evidence_item(
    control_id: str,
    evidence_id: str,
    body: EvidenceReview,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve or flag (return) a single uploaded evidence item — the
    evidence-centric review used by the Evidence tab. Works whether or not the
    item is linked to an expected-evidence suggestion."""
    if current_user.role not in REVIEWER_ROLES:
        raise HTTPException(status_code=403, detail="Only reviewers can accept or return evidence")
    if body.decision not in ("accept", "return"):
        raise HTTPException(status_code=400, detail="decision must be 'accept' or 'return'")
    control = await _load_control(db, control_id)
    org_id = await _target_org(db, current_user)
    if org_id is None:
        raise HTTPException(status_code=400, detail="No client organization in scope")
    ev = await _load_evidence(db, org_id, evidence_id)
    note = (body.note or "").strip() or None
    if body.decision == "return" and not note:
        raise HTTPException(status_code=400, detail="A comment is required when flagging an issue")

    if body.decision == "accept":
        ev.status = EvidenceStatus.accepted
        ev.review_note = note
        await _log_event(db, org_id, control.id, ev.id, current_user, "accepted",
                         f"{ev.title[:80]}" + (f" — {note}" if note else ""))
    else:
        ev.status = EvidenceStatus.needs_more
        ev.review_note = note
        await _log_event(db, org_id, control.id, ev.id, current_user, "returned", note)
    # Keep the linked suggestion's satisfied flag in sync (drives coverage).
    if ev.expected_evidence_id:
        ee = (await db.execute(
            select(ExpectedEvidence).where(ExpectedEvidence.id == ev.expected_evidence_id)
        )).scalar_one_or_none()
        if ee:
            ee.satisfied = (body.decision == "accept")
    await db.flush()
    rows, ev_map, cov, status, valid, total, source = await _recompute(db, org_id, control)
    oc = await _get_or_create_oc(db, org_id, control.id)
    await db.commit()
    return {
        "ok": True,
        "evidence": {"id": str(ev.id), "status": ev.status.value,
                     "review_state": _ee_state(ev), "review_note": ev.review_note},
        "coverage": cov,
        "audit_status": oc.audit_status or ControlStatus.IN_PROGRESS,
        "audit_status_label": AUDIT_LABEL.get(oc.audit_status or "in_progress", "In Progress"),
        "audit_status_badge": AUDIT_BADGE.get(oc.audit_status or "in_progress", "b-amber"),
        "status_mode": oc.status_mode or "auto",
    }


class StatusUpdate(BaseModel):
    mode: str                       # "auto" | "manual"
    status: Optional[str] = None    # required when mode == "manual"
    note: Optional[str] = None


@router.patch("/{control_id}/status")
async def set_control_status(
    control_id: str,
    body: StatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set the control's audit status: 'auto' re-derives from evidence,
    'manual' pins a chosen status with an optional comment (reviewers only)."""
    if current_user.role not in REVIEWER_ROLES:
        raise HTTPException(status_code=403, detail="Only reviewers can change control status")
    if body.mode not in ("auto", "manual"):
        raise HTTPException(status_code=400, detail="mode must be 'auto' or 'manual'")
    control = await _load_control(db, control_id)
    org_id = await _target_org(db, current_user)
    if org_id is None:
        raise HTTPException(status_code=400, detail="No client organization in scope")
    oc = await _get_or_create_oc(db, org_id, control.id)

    if body.mode == "manual":
        st = (body.status or "").strip().lower()
        if st not in ControlStatus.ALL:
            raise HTTPException(status_code=400, detail=f"Invalid status '{body.status}'")
        oc.status_mode = "manual"
        oc.audit_status = st
        oc.status_note = (body.note or "").strip() or None
        await _log_event(db, org_id, control.id, None, current_user, "status",
                         f"Set to {AUDIT_LABEL[st]}" + (f" — {oc.status_note}" if oc.status_note else ""))
    else:
        oc.status_mode = "auto"
        oc.status_note = None
        await _log_event(db, org_id, control.id, None, current_user, "status", "Reverted to auto")

    await db.flush()
    await _recompute(db, org_id, control, oc)   # applies auto rule / mirror
    await db.commit()
    return {
        "audit_status": oc.audit_status or ControlStatus.IN_PROGRESS,
        "audit_status_label": AUDIT_LABEL.get(oc.audit_status or "in_progress", "In Progress"),
        "audit_status_badge": AUDIT_BADGE.get(oc.audit_status or "in_progress", "b-amber"),
        "status_mode": oc.status_mode, "status_note": oc.status_note,
    }


class NotesUpdate(BaseModel):
    previous_audit_notes: Optional[str] = None


@router.patch("/{control_id}/notes")
async def set_control_notes(
    control_id: str,
    body: NotesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save the per-control Previous Audit Notes (reviewers only; clients read-only)."""
    if current_user.role not in REVIEWER_ROLES:
        raise HTTPException(status_code=403, detail="Only reviewers can edit audit notes")
    control = await _load_control(db, control_id)
    org_id = await _target_org(db, current_user)
    if org_id is None:
        raise HTTPException(status_code=400, detail="No client organization in scope")
    oc = await _get_or_create_oc(db, org_id, control.id)
    oc.previous_audit_notes = (body.previous_audit_notes or "").strip() or None
    await db.commit()
    return {"previous_audit_notes": oc.previous_audit_notes}


# ════════════════ MATURITY SELF-ASSESSMENT ════════════════

def _localize_questions(qs: list, lang: str) -> list:
    """Render question prompts/options in the requested language, with EN fallback.
    Authored questions may carry prompt_fr and per-option label_fr / short_fr."""
    out = []
    for q in qs:
        opts = []
        for o in q.get("options", []):
            opts.append({
                **o,
                "short": (o.get("short_fr") if lang == "fr" and o.get("short_fr") else o.get("short")),
                "label": (o.get("label_fr") if lang == "fr" and o.get("label_fr") else o.get("label")),
            })
        out.append({
            "key": q.get("key"),
            "prompt": (q.get("prompt_fr") if lang == "fr" and q.get("prompt_fr") else q.get("prompt")),
            "options": opts,
        })
    return out


def _questions_fr_available(qs: list) -> bool:
    return any(q.get("prompt_fr") for q in qs)


async def _self_assessment_payload(db, org_id, control: Control, lang: str = "en") -> dict:
    sa = (await db.execute(
        select(SelfAssessment).where(
            SelfAssessment.org_id == org_id, SelfAssessment.control_id == control.id
        )
    )).scalar_one_or_none()
    answers = (sa.answers if sa and isinstance(sa.answers, dict) else {}) or {}
    level = perceived_level(answers)
    raw = generate_questions(control)
    return {
        "questions": _localize_questions(raw, lang),
        "english": _localize_questions(raw, "en"),
        "fr_available": lang == "fr" and _questions_fr_available(raw),
        "answers": answers,
        "comment": sa.comment if sa else None,
        "perceived_level": level,
        "scale_max": 5,
    }


@router.get("/{control_id}/self-assessment")
async def get_self_assessment(
    control_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang),
):
    control = await _load_control(db, control_id)
    org_id = await _target_org(db, current_user)
    if org_id is None:
        raise HTTPException(status_code=400, detail="No client organization in scope")
    return await _self_assessment_payload(db, org_id, control, lang)


class SelfAssessmentBody(BaseModel):
    answers: dict[str, int] = {}
    comment: Optional[str] = None


@router.put("/{control_id}/self-assessment")
async def save_self_assessment(
    control_id: str,
    body: SelfAssessmentBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang),
):
    """Client (or a reviewer on their behalf) records the perceived maturity
    rating + an optional Comments / Additional info note for this control."""
    control = await _load_control(db, control_id)
    org_id = await _target_org(db, current_user)
    if org_id is None:
        raise HTTPException(status_code=400, detail="No client organization in scope")
    # Validate levels against the control's generated question keys.
    valid_keys = {q["key"] for q in generate_questions(control)}
    clean = {}
    for k, v in (body.answers or {}).items():
        if k in valid_keys and isinstance(v, int) and 1 <= v <= 5:
            clean[k] = v
    sa = (await db.execute(
        select(SelfAssessment).where(
            SelfAssessment.org_id == org_id, SelfAssessment.control_id == control.id
        )
    )).scalar_one_or_none()
    if sa is None:
        sa = SelfAssessment(org_id=org_id, control_id=control.id)
        db.add(sa)
    sa.answers = clean
    sa.comment = (body.comment or "").strip() or None
    await db.commit()
    return await _self_assessment_payload(db, org_id, control, lang)
