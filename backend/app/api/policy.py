"""Policy library & management API.

- Everyone: list available policies (filter by category, search by topic),
  download the current-language .docx.
- Super Admin: create (upload), edit metadata, replace the file, toggle
  availability, set the category/keywords (which control family it maps to),
  and delete.

Policies are stored as .docx: built-ins under backend/policy_library/, uploads
under <STORAGE_LOCAL_PATH>/policies/ (a persistent volume).
"""
import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.core.i18n import get_lang, loc
from app.core.policy_library import TEMPLATE_DIR, slug as slugify
from app.core.upload_guard import validate_upload
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.policy import Policy

router = APIRouter()

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
UPLOAD_DIR = os.path.join(settings.STORAGE_LOCAL_PATH, "policies")
MAX_BYTES = 25 * 1024 * 1024


def _is_admin(u: User) -> bool:
    return u.role == UserRole.super_admin


def _dir(p: Policy) -> str:
    return UPLOAD_DIR if p.source == "upload" else TEMPLATE_DIR


def _file_path(p: Policy, lang: str) -> str:
    d = _dir(p)
    if lang == "fr" and p.has_fr:
        fr = os.path.join(d, p.slug + ".fr.docx")
        if os.path.isfile(fr):
            return fr
    return os.path.join(d, p.slug + ".docx")


def _serialize(p: Policy, lang: str, admin: bool) -> dict:
    out = {
        "id": str(p.id),
        "name": loc(p, "name", lang),
        "category": loc(p, "category", lang),
        "description": loc(p, "description", lang) or "",
        "is_active": p.is_active,
        "has_file": os.path.isfile(_file_path(p, "en")),
    }
    if admin:
        out.update({
            "name_en": p.name, "name_fr": p.name_fr,
            "category_en": p.category, "category_fr": p.category_fr,
            "keywords": p.keywords, "source": p.source,
            "slug": p.slug, "sort_order": p.sort_order,
        })
    return out


# ── Matcher used by the Controls view ────────────────────────────────────────
async def active_policies(db: AsyncSession) -> list[Policy]:
    return (await db.execute(
        select(Policy).where(Policy.is_active == True).order_by(Policy.sort_order)  # noqa: E712
    )).scalars().all()


def match_policy_name(domain: str, policies: list[Policy], lang: str = "en") -> Optional[str]:
    dl = (domain or "").lower()
    for p in policies:
        kws = [k.strip() for k in (p.keywords or "").split(",") if k.strip()]
        if kws and all(k in dl for k in kws):
            return loc(p, "name", lang)
    return None


# ── Read (all users) ─────────────────────────────────────────────────────────
@router.get("/")
async def list_policies(
    category: Optional[str] = None,
    q: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang),
):
    admin = _is_admin(current_user)
    rows = (await db.execute(select(Policy).order_by(Policy.sort_order, Policy.name))).scalars().all()
    if not admin:
        rows = [p for p in rows if p.is_active]
    if category:
        rows = [p for p in rows if loc(p, "category", lang) == category or p.category == category]
    if q:
        ql = q.lower()
        rows = [p for p in rows if ql in (p.name or "").lower() or ql in (p.name_fr or "").lower()
                or ql in (p.description or "").lower() or ql in (p.keywords or "").lower()
                or ql in (p.category or "").lower()]
    cats = sorted({loc(p, "category", lang) for p in (await db.execute(
        select(Policy).where(Policy.is_active == True) if not admin else select(Policy)  # noqa: E712
    )).scalars().all()})
    return {"policies": [_serialize(p, lang, admin) for p in rows],
            "categories": cats, "can_manage": admin}


@router.get("/file")
async def download_by_name(
    name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang),
):
    """Download by policy name (used by the Controls view)."""
    rows = (await db.execute(select(Policy))).scalars().all()
    pol = next((p for p in rows if loc(p, "name", lang) == name or p.name == name), None)
    if not pol or (not pol.is_active and not _is_admin(current_user)):
        raise HTTPException(status_code=404, detail="Policy not available")
    path = _file_path(pol, lang)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="No file for this policy")
    fr = path.endswith(".fr.docx")
    return FileResponse(path, media_type=DOCX_MIME, filename=pol.slug + ("_FR.docx" if fr else ".docx"))


@router.get("/{policy_id}/file")
async def download_by_id(
    policy_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang),
):
    pol = await db.get(Policy, uuid.UUID(policy_id))
    if not pol or (not pol.is_active and not _is_admin(current_user)):
        raise HTTPException(status_code=404, detail="Policy not available")
    path = _file_path(pol, lang)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="No file for this policy")
    fr = path.endswith(".fr.docx")
    return FileResponse(path, media_type=DOCX_MIME, filename=pol.slug + ("_FR.docx" if fr else ".docx"))


# ── Manage (super admin) ─────────────────────────────────────────────────────
async def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Policy management is restricted to Super Admins")
    return current_user


class PolicyMeta(BaseModel):
    name: Optional[str] = None
    name_fr: Optional[str] = None
    category: Optional[str] = None
    category_fr: Optional[str] = None
    description: Optional[str] = None
    description_fr: Optional[str] = None
    keywords: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


def _save_upload(slug: str, lang_suffix: str, data: bytes):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    fname = f"{slug}{lang_suffix}.docx"
    with open(os.path.join(UPLOAD_DIR, fname), "wb") as fh:
        fh.write(data)


@router.post("/")
async def create_policy(
    name: str = Form(...),
    category: str = Form("General"),
    keywords: str = Form(""),
    description: str = Form(""),
    name_fr: str = Form(""),
    category_fr: str = Form(""),
    file: UploadFile = File(...),
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 25 MB limit")
    validate_upload(file.filename, data, "policy")
    base = slugify(name) or uuid.uuid4().hex
    pol = Policy(name=name, name_fr=(name_fr or None), category=category or "General",
                 category_fr=(category_fr or None), description=(description or None),
                 keywords=keywords.strip().lower(), slug=base, source="upload",
                 has_fr=False, is_active=True, sort_order=999)
    _save_upload(base, "", data)
    db.add(pol)
    await db.commit()
    return {"id": str(pol.id), "ok": True}


@router.patch("/{policy_id}")
async def update_policy(
    policy_id: str, body: PolicyMeta,
    admin: User = Depends(_require_admin), db: AsyncSession = Depends(get_db),
):
    pol = await db.get(Policy, uuid.UUID(policy_id))
    if not pol:
        raise HTTPException(status_code=404, detail="Policy not found")
    for field in ("name", "name_fr", "category", "category_fr", "description",
                  "description_fr", "keywords", "is_active", "sort_order"):
        val = getattr(body, field)
        if val is not None:
            setattr(pol, field, (val.strip().lower() if field == "keywords" else val))
    await db.commit()
    return {"ok": True}


@router.post("/{policy_id}/file")
async def replace_file(
    policy_id: str, file: UploadFile = File(...), fr: bool = Form(False),
    admin: User = Depends(_require_admin), db: AsyncSession = Depends(get_db),
):
    pol = await db.get(Policy, uuid.UUID(policy_id))
    if not pol:
        raise HTTPException(status_code=404, detail="Policy not found")
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 25 MB limit")
    validate_upload(file.filename, data, "policy")
    # Uploaded replacements always live in the upload dir; flip source so they win.
    pol.source = "upload"
    _save_upload(pol.slug, ".fr" if fr else "", data)
    if fr:
        pol.has_fr = True
    await db.commit()
    return {"ok": True}


@router.delete("/{policy_id}")
async def delete_policy(
    policy_id: str, admin: User = Depends(_require_admin), db: AsyncSession = Depends(get_db),
):
    pol = await db.get(Policy, uuid.UUID(policy_id))
    if not pol:
        raise HTTPException(status_code=404, detail="Policy not found")
    if pol.source == "upload":
        for suffix in ("", ".fr"):
            fp = os.path.join(UPLOAD_DIR, f"{pol.slug}{suffix}.docx")
            try:
                if os.path.isfile(fp):
                    os.remove(fp)
            except OSError:
                pass
    await db.delete(pol)
    await db.commit()
    return {"ok": True}
