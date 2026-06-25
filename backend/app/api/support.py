"""Contact Support - users raise cases; the EVA team reviews them in the
Super Admin console. Config (enabled / categories / intro) is Super-Admin editable."""
import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core import storage
from app.core.upload_guard import validate_upload
from app.core.email import send_email
from app.api.auth import get_current_user
from app.api.evidence import _accessible_org_ids
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.models.support import SupportCase, SupportSettings, SupportStatus, SupportComment

router = APIRouter()

EVA_ROLES = {UserRole.super_admin, UserRole.eva_auditor}
MSP_ROLES = {UserRole.msp_admin, UserRole.msp_analyst}
ADMIN_STATUSES = {s.value for s in SupportStatus}


@router.get("/orgs")
async def selectable_orgs(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Orgs a requester can raise a case for. MSP → itself + its clients; others → just itself."""
    own = (await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))).scalar_one_or_none()
    out = []
    if own:
        out.append({"id": str(own.id), "name": own.name, "self": True})
    if current_user.role in MSP_ROLES:
        clients = (await db.execute(
            select(Tenant).where(Tenant.parent_msp_id == current_user.tenant_id).order_by(Tenant.name)
        )).scalars().all()
        out += [{"id": str(c.id), "name": c.name, "self": False} for c in clients]
    return {"orgs": out}


# ──────────────────────────── config ────────────────────────────
async def _get_settings(db: AsyncSession) -> SupportSettings:
    s = (await db.execute(select(SupportSettings).limit(1))).scalar_one_or_none()
    if not s:
        s = SupportSettings()
        db.add(s)
        await db.commit()
        await db.refresh(s)
    return s


def _cats(s: SupportSettings) -> list[str]:
    return [c.strip() for c in (s.categories or "").split(",") if c.strip()]


@router.get("/config")
async def get_config(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    s = await _get_settings(db)
    return {"enabled": s.enabled, "categories": _cats(s), "intro": s.intro,
            "can_configure": current_user.role == UserRole.super_admin}


class ConfigBody(BaseModel):
    enabled: bool
    categories: list[str]
    intro: str


@router.put("/config")
async def put_config(body: ConfigBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin only")
    s = await _get_settings(db)
    s.enabled = body.enabled
    s.categories = ",".join(c.strip() for c in body.categories if c.strip()) or "Question,Other"
    s.intro = body.intro
    await db.commit()
    await db.refresh(s)
    return {"enabled": s.enabled, "categories": _cats(s), "intro": s.intro, "can_configure": True}


# ──────────────────────────── cases ────────────────────────────
def _serialize(c: SupportCase, comments: list | None = None) -> dict:
    return {
        "id": str(c.id), "subject": c.subject, "category": c.category, "message": c.message,
        "status": c.status.value if hasattr(c.status, "value") else c.status,
        "response": c.response,
        "requester_name": c.requester_name, "requester_email": c.requester_email, "org_name": c.org_name,
        "created_at": c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else "",
        "updated_at": c.updated_at.strftime("%Y-%m-%d %H:%M") if c.updated_at else "",
        "comments": comments if comments is not None else [],
        "has_attachment": bool(c.attachment_key),
        "attachment_name": c.attachment_name,
    }


def _scomment(cm: SupportComment) -> dict:
    return {
        "id": str(cm.id), "author_name": cm.author_name, "author_role": cm.author_role,
        "is_eva": bool(cm.is_eva), "body": cm.body,
        "created_at": cm.created_at.strftime("%Y-%m-%d %H:%M") if cm.created_at else "",
    }


async def _accessible_case(db: AsyncSession, user: User, case: SupportCase) -> bool:
    if user.role in EVA_ROLES:
        return True
    return case.org_id in await _accessible_org_ids(db, user)


ATTACH_MAX_BYTES = 25 * 1024 * 1024  # 25 MB


@router.post("/cases")
async def create_case(
    subject: str = Form(...),
    message: str = Form(...),
    category: str = Form("Question"),
    org_id: Optional[str] = Form(None),   # MSP can raise a case for itself or a client
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    s = await _get_settings(db)
    if not s.enabled:
        raise HTTPException(status_code=403, detail="Contact Support is currently disabled.")
    if not subject.strip() or not message.strip():
        raise HTTPException(status_code=400, detail="Subject and message are required.")

    # Resolve the target org: default to the requester's own tenant; an MSP may
    # pick one of its clients (validated against the orgs it can access).
    target_org_id = current_user.tenant_id
    if org_id:
        try:
            oid = uuid.UUID(org_id)
        except ValueError:
            oid = None
        if oid and oid in await _accessible_org_ids(db, current_user):
            target_org_id = oid

    # Optional screenshot/attachment → local storage.
    a_key = a_name = a_type = None
    if file is not None and file.filename:
        data = await file.read()
        if len(data) > ATTACH_MAX_BYTES:
            raise HTTPException(status_code=413, detail="Attachment exceeds 25 MB limit")
        validate_upload(file.filename, data, "support")
        a_name = os.path.basename(file.filename)
        a_key = storage.save_bytes(f"{target_org_id}/support/{uuid.uuid4().hex}_{a_name}", data)
        a_type = file.content_type

    try:
        tenant = (await db.execute(select(Tenant).where(Tenant.id == target_org_id))).scalar_one_or_none()
        case = SupportCase(
            org_id=target_org_id, created_by=current_user.id,
            requester_name=current_user.display_name, requester_email=current_user.email,
            org_name=tenant.name if tenant else "",
            category=category or "Question", subject=subject.strip(), message=message.strip(),
            attachment_key=a_key, attachment_name=a_name, attachment_type=a_type,
        )
        db.add(case)
        await db.commit()
        await db.refresh(case)
    except Exception as e:  # surface the real cause to the caller for diagnosis
        await db.rollback()
        import logging
        logging.getLogger("eva.support").exception("create_case failed")
        raise HTTPException(status_code=500, detail=f"Could not save case: {type(e).__name__}: {e}")

    # Alert the EVA team (best-effort - never breaks the request).
    try:
        recipients = (await db.execute(select(User.email).where(User.role.in_(list(EVA_ROLES))))).scalars().all()
        send_email(
            recipients,
            f"[EVA Support] {case.category}: {case.subject}",
            f"New support request from {case.requester_name} ({case.requester_email}) at {case.org_name}.\n\n"
            f"Category: {case.category}\nSubject: {case.subject}\n\n{case.message}\n\n"
            f"Review it in the Super Admin support console.",
            sender="cases",
        )
    except Exception:
        import logging
        logging.getLogger("eva.support").exception("support email failed (case still saved)")

    return _serialize(case)


@router.get("/cases")
async def list_cases(status: Optional[str] = None,
                     current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(SupportCase).order_by(SupportCase.created_at.desc())
    if current_user.role in MSP_ROLES:
        # MSP sees its own cases and those it raised for its clients.
        q = q.where(SupportCase.org_id.in_(list(await _accessible_org_ids(db, current_user))))
    elif current_user.role not in EVA_ROLES:
        q = q.where(SupportCase.org_id == current_user.tenant_id)
    if status and status in ADMIN_STATUSES:
        q = q.where(SupportCase.status == SupportStatus(status))
    rows = (await db.execute(q)).scalars().all()

    # Attach the comment thread for each case (oldest first), plus any legacy
    # single-field EVA response surfaced as the first comment.
    by_case: dict = {}
    ids = [c.id for c in rows]
    if ids:
        crows = (await db.execute(
            select(SupportComment).where(SupportComment.case_id.in_(ids)).order_by(SupportComment.created_at)
        )).scalars().all()
        for cm in crows:
            by_case.setdefault(cm.case_id, []).append(_scomment(cm))

    cases = []
    for c in rows:
        thread = []
        if c.response:
            thread.append({"id": f"legacy-{c.id}", "author_name": "EVA", "author_role": "eva_auditor",
                           "is_eva": True, "body": c.response, "created_at": c.updated_at.strftime("%Y-%m-%d %H:%M") if c.updated_at else ""})
        thread += by_case.get(c.id, [])
        cases.append(_serialize(c, thread))
    return {"cases": cases, "is_admin": current_user.role in EVA_ROLES}


class CommentBody(BaseModel):
    body: str


@router.post("/cases/{case_id}/comments")
async def add_comment(case_id: str, body: CommentBody,
                      current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not body.body.strip():
        raise HTTPException(status_code=400, detail="Comment is required.")
    try:
        cid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Case not found")
    case = (await db.execute(select(SupportCase).where(SupportCase.id == cid))).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if not await _accessible_case(db, current_user, case):
        raise HTTPException(status_code=403, detail="Not permitted")

    is_eva = current_user.role in EVA_ROLES
    cm = SupportComment(
        case_id=case.id, author_id=current_user.id,
        author_name=current_user.display_name, author_role=current_user.role.value, is_eva=is_eva,
        body=body.body.strip(),
    )
    db.add(cm)
    # An EVA reply moves an untouched case into "in progress".
    if is_eva and case.status == SupportStatus.open:
        case.status = SupportStatus.in_progress
    await db.commit()
    await db.refresh(cm)
    return _scomment(cm)


class CasePatch(BaseModel):
    status: Optional[str] = None
    response: Optional[str] = None


@router.patch("/cases/{case_id}")
async def patch_case(case_id: str, body: CasePatch,
                     current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role not in EVA_ROLES:
        raise HTTPException(status_code=403, detail="EVA reviewers only")
    try:
        cid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Case not found")
    case = (await db.execute(select(SupportCase).where(SupportCase.id == cid))).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if body.status and body.status in ADMIN_STATUSES:
        case.status = SupportStatus(body.status)
    if body.response is not None:
        case.response = body.response
    await db.commit()
    await db.refresh(case)
    return _serialize(case)


@router.get("/cases/{case_id}/attachment")
async def get_attachment(case_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        cid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Case not found")
    case = (await db.execute(select(SupportCase).where(SupportCase.id == cid))).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if not await _accessible_case(db, current_user, case):
        raise HTTPException(status_code=403, detail="Not permitted")
    if not case.attachment_key:
        raise HTTPException(status_code=404, detail="No attachment")
    return storage.open_response(case.attachment_key, filename=case.attachment_name or "attachment",
                                 mime=case.attachment_type or "application/octet-stream")


async def open_case_count(db: AsyncSession) -> int:
    """Open + in-progress cases - used by the notifications bell."""
    n = (await db.execute(
        select(func.count(SupportCase.id)).where(
            SupportCase.status.in_([SupportStatus.open, SupportStatus.in_progress])
        )
    )).scalar() or 0
    return int(n)
