"""
Evidence API - functional: list, multipart upload to local storage,
submit-for-review, delete (drafts), and download.
"""
import os
import io
import csv
import uuid
import hashlib
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.config import settings
from app.core import storage
from app.core.entitlements import ensure_active
from app.core.upload_guard import validate_upload
from app.core.i18n import get_lang
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantType
from app.models.framework import Control
from app.models.evidence import (
    OrgControl, OrgControlStatus, EvidenceItem, EvidenceStatus,
    EvidenceSource, EvidenceFrequency, ExpectedEvidence,
)

router = APIRouter()

CLIENT_ROLES = {UserRole.client_admin, UserRole.contributor, UserRole.viewer}
MAX_BYTES = 50 * 1024 * 1024  # 50 MB


def _require_can_write(user: User) -> None:
    """The viewer role is read-only. All other roles (contributor, client_admin,
    and the reviewer/admin roles acting on a client's behalf) may write."""
    if user.role == UserRole.viewer:
        raise HTTPException(status_code=403, detail="Your role has read-only access")

EV_BADGE = {
    "accepted": "b-green", "needs_more": "b-amber", "draft": "b-gray",
    "rejected": "b-red", "client_submitted": "b-blue", "eva_pending": "b-blue",
    "msp_pending": "b-blue", "msp_approved": "b-teal", "msp_flagged": "b-orange",
    "not_applicable": "b-gray",
}
EV_LABEL = {
    "accepted": "Accepted", "needs_more": "Needs more", "draft": "Draft",
    "rejected": "Rejected", "client_submitted": "Submitted", "eva_pending": "In EVA review",
    "msp_pending": "In MSP review", "msp_approved": "MSP approved",
    "msp_flagged": "Flagged", "not_applicable": "N/A",
}
EV_LABEL_FR = {
    "accepted": "Acceptée", "needs_more": "Complément requis", "draft": "Brouillon",
    "rejected": "Rejetée", "client_submitted": "Soumise", "eva_pending": "En revue EVA",
    "msp_pending": "En revue MSP", "msp_approved": "Approuvée MSP",
    "msp_flagged": "Signalée", "not_applicable": "S.O.",
}
# Statuses that count as "submitted / under review"
PENDING = {
    EvidenceStatus.client_submitted, EvidenceStatus.msp_pending, EvidenceStatus.eva_pending,
}
EXT_ICON = {
    "pdf": "📄", "xlsx": "📊", "xls": "📊", "csv": "📊", "png": "🖼", "jpg": "🖼",
    "jpeg": "🖼", "gif": "🖼", "zip": "🗜", "doc": "📝", "docx": "📝", "mp4": "🎬",
}


def _humanize(n) -> str:
    if not n:
        return "-"
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.0f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


async def _target_org(db: AsyncSession, user: User):
    """Org this request acts on - the selected client for reviewers, own tenant for clients."""
    from app.core.client_context import resolve_org
    return await resolve_org(db, user)


def _serialize(ev: EvidenceItem, ctrl_ref: str, who: str, lang: str = "en", ee_text_fr: str | None = None) -> dict:
    ext = (ev.file_name or "").rsplit(".", 1)[-1].lower() if ev.file_name and "." in ev.file_name else ""
    # The stored title is the English expected-evidence text. In French, show the
    # French requirement text (text_fr) of the linked expected-evidence when present.
    title = ev.title
    if lang == "fr" and ee_text_fr:
        title = ee_text_fr
    labels = EV_LABEL_FR if lang == "fr" else EV_LABEL
    return {
        "id": str(ev.id),
        "title": title,
        "icon": EXT_ICON.get(ext, "📎"),
        "status": ev.status.value,
        "statusBadge": EV_BADGE.get(ev.status.value, "b-gray"),
        "statusLabel": labels.get(ev.status.value, ev.status.value),
        "ctrl_ref": ctrl_ref,
        "by": who,
        "date": ev.created_at.strftime("%b %d, %Y") if ev.created_at else "-",
        "size": _humanize(ev.file_size),
        "freq": ev.frequency.value,
        "note": ev.description or None,
        "can_submit": ev.status == EvidenceStatus.draft,
        "can_delete": ev.status == EvidenceStatus.draft,
        "has_file": bool(ev.file_key),
    }


@router.get("/")
async def list_evidence(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang),
):
    org_id = await _target_org(db, current_user)
    if not org_id:
        return {"items": [], "counts": {"all": 0, "accepted": 0, "submitted": 0, "needs_more": 0, "draft": 0}}

    rows = await db.execute(
        select(EvidenceItem, Control.ref, User.display_name, ExpectedEvidence.text_fr)
        .join(OrgControl, OrgControl.id == EvidenceItem.org_control_id)
        .join(Control, Control.id == OrgControl.control_id)
        .join(User, User.id == EvidenceItem.collected_by)
        .outerjoin(ExpectedEvidence, ExpectedEvidence.id == EvidenceItem.expected_evidence_id)
        .where(EvidenceItem.org_id == org_id)
        .order_by(EvidenceItem.created_at.desc())
    )
    items = [_serialize(ev, ref, who, lang, ee_fr) for ev, ref, who, ee_fr in rows.all()]
    counts = {
        "all": len(items),
        "accepted": sum(1 for i in items if i["status"] == "accepted"),
        "submitted": sum(1 for i in items if i["status"] in {s.value for s in PENDING}),
        "needs_more": sum(1 for i in items if i["status"] in ("needs_more", "rejected")),
        "draft": sum(1 for i in items if i["status"] == "draft"),
    }
    return {"items": items, "counts": counts}


FREQ_DAYS = {"monthly": 30, "quarterly": 90, "semi_annual": 180, "annual": 365, "continuous": 30}


@router.get("/renewals")
async def renewals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Periodic evidence that needs renewal, with computed expiry windows."""
    org_id = await _target_org(db, current_user)
    if not org_id:
        return {"items": [], "counts": {"expired": 0, "soon": 0, "ok": 0}}

    rows = await db.execute(
        select(EvidenceItem, Control.ref, Control.title, User.display_name)
        .join(OrgControl, OrgControl.id == EvidenceItem.org_control_id)
        .join(Control, Control.id == OrgControl.control_id)
        .join(User, User.id == EvidenceItem.collected_by)
        .where(EvidenceItem.org_id == org_id, EvidenceItem.frequency != EvidenceFrequency.once)
        .order_by(EvidenceItem.created_at.desc())
    )
    today = date.today()
    items, counts = [], {"expired": 0, "soon": 0, "ok": 0}
    for ev, ref, ctitle, who in rows.all():
        interval = FREQ_DAYS.get(ev.frequency.value, 90)
        base = ev.expires_at or ((ev.created_at.date() if ev.created_at else today) + timedelta(days=interval))
        days_left = (base - today).days
        status = "expired" if days_left < 0 else "soon" if days_left <= 30 else "ok"
        counts[status] += 1
        items.append({
            "id": str(ev.id), "ev_title": ev.title, "ctrl_ref": ref, "ctrl_name": ctitle,
            "freq": ev.frequency.value, "owner": who, "due": base.strftime("%b %d, %Y"),
            "days_left": days_left, "status": status,
        })
    items.sort(key=lambda x: x["days_left"])
    return {"items": items, "counts": counts}


@router.post("/upload")
async def upload_evidence(
    title: str = Form(...),
    control_id: str = Form(...),
    frequency: str = Form("once"),
    description: str = Form(""),
    submit: bool = Form(False),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_can_write(current_user)
    await ensure_active(db, current_user)
    org_id = await _target_org(db, current_user)
    if not org_id:
        raise HTTPException(status_code=400, detail="No organization in scope for upload")

    try:
        cid = uuid.UUID(control_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid control id")
    control = (await db.execute(select(Control).where(Control.id == cid))).scalar_one_or_none()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    try:
        freq = EvidenceFrequency(frequency)
    except ValueError:
        freq = EvidenceFrequency.once

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 50 MB limit")
    validate_upload(file.filename, data, "evidence")

    # Resolve or create the org-control link for this org + control
    oc = (await db.execute(
        select(OrgControl).where(OrgControl.org_id == org_id, OrgControl.control_id == cid)
        .order_by(OrgControl.created_at.asc())
    )).scalars().first()
    if not oc:
        oc = OrgControl(
            org_id=org_id, control_id=cid,
            status=OrgControlStatus.in_progress, coverage_pct=20,
            owner_user_id=current_user.id,
        )
        db.add(oc)
        await db.flush()
    elif oc.status == OrgControlStatus.not_started:
        oc.status = OrgControlStatus.in_progress

    # Persist file via the storage layer (local disk or S3/R2 per config).
    safe_name = os.path.basename(file.filename or "evidence")
    file_key = storage.save_bytes(f"{org_id}/{uuid.uuid4().hex}_{safe_name}", data)

    if submit:
        tenant = (await db.execute(select(Tenant).where(Tenant.id == org_id))).scalar_one_or_none()
        if tenant and (tenant.audit_level or "self") == "self":
            # Self-audit engagement: no reviewer step - evidence is accepted on submit.
            status = EvidenceStatus.accepted
        elif tenant and tenant.msp_review_enabled:
            status = EvidenceStatus.msp_pending
        else:
            status = EvidenceStatus.eva_pending
    else:
        status = EvidenceStatus.draft

    ev = EvidenceItem(
        org_control_id=oc.id, org_id=org_id,
        title=title, description=description or None,
        file_key=file_key, file_name=safe_name, file_size=len(data),
        file_type=file.content_type, checksum_sha256=hashlib.sha256(data).hexdigest(),
        source=EvidenceSource.upload, status=status, frequency=freq,
        collected_by=current_user.id,
    )
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    return _serialize(ev, control.ref, current_user.display_name)


@router.post("/{evidence_id}/submit")
async def submit_evidence(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_can_write(current_user)
    await ensure_active(db, current_user)
    ev = await _get_owned(db, evidence_id, current_user)
    if ev.status != EvidenceStatus.draft:
        raise HTTPException(status_code=400, detail="Only drafts can be submitted")
    tenant = (await db.execute(select(Tenant).where(Tenant.id == ev.org_id))).scalar_one_or_none()
    ev.status = (EvidenceStatus.msp_pending
                 if (tenant and tenant.msp_review_enabled)
                 else EvidenceStatus.eva_pending)
    await db.commit()
    return {"id": str(ev.id), "status": ev.status.value}


@router.delete("/{evidence_id}")
async def delete_evidence(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_can_write(current_user)
    ev = await _get_owned(db, evidence_id, current_user)
    org_id = ev.org_id
    ee_id = ev.expected_evidence_id
    fname = ev.file_name
    oc = (await db.execute(select(OrgControl).where(OrgControl.id == ev.org_control_id))).scalar_one_or_none()
    control = None
    if oc:
        control = (await db.execute(select(Control).where(Control.id == oc.control_id))).scalar_one_or_none()
    if ev.file_key:
        storage.delete(ev.file_key)
    # Removing evidence sends its expected-evidence item back to "missing".
    if ee_id:
        ee = (await db.execute(select(ExpectedEvidence).where(ExpectedEvidence.id == ee_id))).scalar_one_or_none()
        if ee:
            ee.satisfied = False
    await db.delete(ev)
    await db.flush()
    if control:
        from app.api.controls import _log_event, _recompute
        await _log_event(db, org_id, control.id, None, current_user, "deleted", f"Removed “{fname or 'evidence'}”")
        await _recompute(db, org_id, control)
    await db.commit()
    return {"deleted": evidence_id}


@router.get("/{evidence_id}/download")
async def download_evidence(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ev = await _get_owned(db, evidence_id, current_user, require_org_match=False)
    # Authorize: the file's tenant must be within the caller's accessible scope
    # (client → own tenant; MSP → its clients; EVA → all clients). Prevents IDOR.
    if ev.org_id not in await _accessible_org_ids(db, current_user):
        raise HTTPException(status_code=403, detail="Not permitted")
    if not ev.file_key:
        raise HTTPException(status_code=404, detail="No file attached")
    return storage.open_response(ev.file_key, filename=ev.file_name or "evidence",
                                 mime=ev.file_type or "application/octet-stream")


@router.get("/{evidence_id}/preview")
async def preview_evidence(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Structured preview for inline rendering (image/pdf use the download blob)."""
    ev = await _get_owned(db, evidence_id, current_user, require_org_match=False)
    if ev.org_id not in await _accessible_org_ids(db, current_user):
        raise HTTPException(status_code=403, detail="Not permitted")
    if not ev.file_key or not storage.exists(ev.file_key):
        raise HTTPException(status_code=404, detail="File missing from storage")

    name = (ev.file_name or "").lower()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    if ext in ("png", "jpg", "jpeg", "gif", "webp", "svg"):
        return {"kind": "image", "file_name": ev.file_name}
    if ext == "pdf":
        return {"kind": "pdf", "file_name": ev.file_name}
    try:
        data = storage.read_bytes(ev.file_key)
        if ext == "csv":
            rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig", "replace"))))
            rows = [r for r in rows if any(str(c).strip() for c in r)]
            cols = rows[0] if rows else []
            return {"kind": "table", "columns": cols, "rows": rows[1:51], "file_name": ev.file_name}
        if ext in ("xlsx", "xlsm"):
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
            ws = wb.active
            allrows = [[("" if c is None else str(c)) for c in r] for r in ws.iter_rows(values_only=True)]
            allrows = [r for r in allrows if any(str(c).strip() for c in r)]
            cols = allrows[0] if allrows else []
            return {"kind": "table", "columns": cols, "rows": allrows[1:51], "file_name": ev.file_name}
        if ext in ("txt", "md", "json", "log", "csv"):
            return {"kind": "text", "content": data[:8000].decode("utf-8", "replace"), "file_name": ev.file_name}
    except Exception:
        pass
    return {"kind": "none", "file_name": ev.file_name}


async def _accessible_org_ids(db: AsyncSession, user: User):
    """All tenant IDs whose evidence this user may read."""
    if user.role in CLIENT_ROLES:
        return {user.tenant_id}
    if user.role in (UserRole.msp_admin, UserRole.msp_analyst):
        rows = await db.execute(
            select(Tenant.id).where(
                ((Tenant.id == user.tenant_id) | (Tenant.parent_msp_id == user.tenant_id)),
                Tenant.archived == False,  # noqa: E712
            )
        )
        return set(rows.scalars().all())
    # EVA / super admin → all client tenants
    rows = await db.execute(
        select(Tenant.id).where(Tenant.tenant_type == TenantType.single_client, Tenant.archived == False)  # noqa: E712
    )
    return set(rows.scalars().all())


async def _get_owned(db, evidence_id, user, require_org_match=True) -> EvidenceItem:
    try:
        eid = uuid.UUID(evidence_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Evidence not found")
    ev = (await db.execute(select(EvidenceItem).where(EvidenceItem.id == eid))).scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")
    if require_org_match:
        org_id = await _target_org(db, user)
        if ev.org_id != org_id:
            raise HTTPException(status_code=403, detail="Not permitted")
    return ev
