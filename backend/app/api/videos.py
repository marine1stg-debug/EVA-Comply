"""Training videos for frameworks (overview) and controls.

A video is either an external link (Vimeo / YouTube / any URL) or an app-hosted
file (e.g. a webcam recording uploaded from the browser). Editing is Super Admin
only (frameworks are global content); any authenticated user can watch.
"""
import os
import re
import uuid
import mimetypes
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.i18n import get_lang, loc, loc_domain
from app.api.auth import get_current_user
from app.core import storage
from app.core.upload_guard import validate_upload
from app.core.llm import get_llm_settings, chat, LlmError
from app.models.user import User, UserRole
from app.models.framework import Framework, Control

router = APIRouter()

VIDEO_MAX_BYTES = 200 * 1024 * 1024  # 200 MB


def _require_admin(user: User):
    if user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Only the Super Admin can edit training videos")


def _video_info(url: Optional[str], key: Optional[str], file_path: str) -> dict:
    if key:
        return {"kind": "file", "url": None, "file": file_path}
    if url:
        return {"kind": "link", "url": url, "file": None}
    return {"kind": None, "url": None, "file": None}


async def _get_framework(db, fw_id: str) -> Framework:
    try:
        fid = uuid.UUID(fw_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Framework not found")
    fw = (await db.execute(select(Framework).where(Framework.id == fid))).scalar_one_or_none()
    if not fw:
        raise HTTPException(status_code=404, detail="Framework not found")
    return fw


async def _get_control(db, control_id: str) -> Control:
    try:
        cid = uuid.UUID(control_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Control not found")
    c = (await db.execute(select(Control).where(Control.id == cid))).scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Control not found")
    return c


@router.get("/framework/{fw_id}")
async def framework_videos(fw_id: str, current_user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db), lang: str = Depends(get_lang)):
    """Editor payload: framework overview video + every control's video.
    Titles/domains follow the current language."""
    fw = await _get_framework(db, fw_id)
    rows = (await db.execute(
        select(Control).where(Control.framework_id == fw.id).order_by(Control.sort_order)
    )).scalars().all()
    return {
        "framework": {
            "id": str(fw.id), "name": fw.name, "version": fw.version,
            "video": _video_info(fw.intro_video_url, fw.intro_video_key, f"/videos/file/framework/{fw.id}"),
        },
        "controls": [{
            "id": str(c.id), "ref": c.ref, "title": loc(c, "title", lang),
            "domain": loc_domain(c.domain, lang) or "",
            "video": _video_info(c.video_url, c.video_key, f"/videos/file/control/{c.id}"),
        } for c in rows],
        "can_edit": current_user.role == UserRole.super_admin,
    }


@router.get("/control/{control_id}/brief")
async def control_brief(control_id: str, current_user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db), lang: str = Depends(get_lang)):
    """A recording brief for the person filming a control's explainer video:
    the label, what to explain, the key points, and the evidence expected.
    Context fields follow the current language so the FR brief reads in French."""
    c = await _get_control(db, control_id)
    return {
        "ref": c.ref, "title": loc(c, "title", lang),
        "description": loc(c, "description", lang),
        "plain_language": loc(c, "plain_language", lang),
        "objective": loc(c, "objective", lang),
        "best_practices": loc(c, "best_practices", lang),
        "evidence_best_practices": loc(c, "evidence_best_practices", lang),
        "script_en": c.video_script_en or "",
        "script_fr": c.video_script_fr or "",
        "video": _video_info(c.video_url, c.video_key, f"/videos/file/control/{c.id}"),
    }


class LinkBody(BaseModel):
    url: Optional[str] = None


@router.put("/framework/{fw_id}/link")
async def set_framework_link(fw_id: str, body: LinkBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(current_user)
    fw = await _get_framework(db, fw_id)
    fw.intro_video_url = (body.url or "").strip() or None
    fw.intro_video_key = None  # link replaces any uploaded file
    await db.commit()
    return {"ok": True, "video": _video_info(fw.intro_video_url, fw.intro_video_key, f"/videos/file/framework/{fw.id}")}


@router.put("/control/{control_id}/link")
async def set_control_link(control_id: str, body: LinkBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(current_user)
    c = await _get_control(db, control_id)
    c.video_url = (body.url or "").strip() or None
    c.video_key = None
    await db.commit()
    return {"ok": True, "video": _video_info(c.video_url, c.video_key, f"/videos/file/control/{c.id}")}


@router.delete("/framework/{fw_id}/video")
async def delete_framework_video(fw_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(current_user)
    fw = await _get_framework(db, fw_id)
    if fw.intro_video_key:
        storage.delete(fw.intro_video_key)
    fw.intro_video_url = None
    fw.intro_video_key = None
    await db.commit()
    return {"ok": True}


@router.delete("/control/{control_id}/video")
async def delete_control_video(control_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(current_user)
    c = await _get_control(db, control_id)
    if c.video_key:
        storage.delete(c.video_key)
    c.video_url = None
    c.video_key = None
    await db.commit()
    return {"ok": True}


async def _save_upload(file: UploadFile, folder_key: str) -> str:
    data = await file.read()
    if len(data) > VIDEO_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Video exceeds the 200 MB limit")
    validate_upload(file.filename, data, "video")
    ext = os.path.splitext(file.filename or "")[1] or ".webm"
    key = f"{folder_key}/{uuid.uuid4().hex}{ext}"
    return storage.save_bytes(key, data)


@router.post("/framework/{fw_id}/upload")
async def upload_framework_video(fw_id: str, file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(current_user)
    fw = await _get_framework(db, fw_id)
    fw.intro_video_key = await _save_upload(file, f"videos/framework/{fw.id}")
    fw.intro_video_url = None
    await db.commit()
    return {"ok": True, "video": _video_info(fw.intro_video_url, fw.intro_video_key, f"/videos/file/framework/{fw.id}")}


@router.post("/control/{control_id}/upload")
async def upload_control_video(control_id: str, file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(current_user)
    c = await _get_control(db, control_id)
    c.video_key = await _save_upload(file, f"videos/control/{c.id}")
    c.video_url = None
    await db.commit()
    return {"ok": True, "video": _video_info(c.video_url, c.video_key, f"/videos/file/control/{c.id}")}


def _stream(key: Optional[str]):
    if not key:
        raise HTTPException(status_code=404, detail="No video")
    mime = mimetypes.guess_type(key)[0] or "video/webm"
    return storage.open_response(key, mime=mime)


@router.get("/file/framework/{fw_id}")
async def stream_framework_video(fw_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    fw = await _get_framework(db, fw_id)
    return _stream(fw.intro_video_key)


@router.get("/file/control/{control_id}")
async def stream_control_video(control_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    c = await _get_control(db, control_id)
    return _stream(c.video_key)


# ════════════════ RECORDING SCRIPTS (bilingual, prepared in advance) ════════════════

@router.get("/framework/{fw_id}/scripts")
async def framework_scripts(fw_id: str, current_user: User = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db), lang: str = Depends(get_lang)):
    fw = await _get_framework(db, fw_id)
    rows = (await db.execute(
        select(Control).where(Control.framework_id == fw.id).order_by(Control.sort_order)
    )).scalars().all()
    return {
        "framework": {"id": str(fw.id), "name": fw.name},
        "controls": [{
            "id": str(c.id), "ref": c.ref, "title": loc(c, "title", lang),
            "domain": loc_domain(c.domain, lang) or "",
            "has_video": bool(c.video_url or c.video_key),
            "script_en": c.video_script_en or "", "script_fr": c.video_script_fr or "",
        } for c in rows],
        "can_edit": current_user.role == UserRole.super_admin,
    }


class ScriptBody(BaseModel):
    script_en: Optional[str] = None
    script_fr: Optional[str] = None


@router.put("/control/{control_id}/script")
async def set_script(control_id: str, body: ScriptBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(current_user)
    c = await _get_control(db, control_id)
    if body.script_en is not None:
        c.video_script_en = (body.script_en or "").strip() or None
    if body.script_fr is not None:
        c.video_script_fr = (body.script_fr or "").strip() or None
    await db.commit()
    return {"ok": True, "script_en": c.video_script_en or "", "script_fr": c.video_script_fr or ""}


def _key_points(c: Control) -> str:
    parts = [p for p in [(c.objective or "").strip(), (c.best_practices or "").strip(),
                         (c.plain_language or "").strip()] if p]
    return "\n".join(parts) or "(none provided — infer the intent from the control name)"


def _template_script(c: Control, lang: str) -> str:
    """Beginner-friendly narration fallback when the AI connector is off."""
    obj = (c.objective or "").strip()
    pl = (c.plain_language or "").strip()
    bp = (c.best_practices or "").strip()
    if lang == "fr":
        return (
            f"Parlons du contrôle « {c.title} ». "
            f"{pl + ' ' if pl else ''}"
            f"En clair, l'idée est de {obj.lower() if obj else 'mettre en place cette mesure de sécurité et de pouvoir le démontrer'}. "
            f"C'est important parce que cela réduit le risque et montre que votre organisation prend la sécurité au sérieux. "
            f"Concrètement, {bp.lower() if bp else 'définissez la règle, attribuez un responsable, et appliquez-la de façon constante'}. "
            f"Lors d'un audit, on cherchera surtout des preuves que c'est réellement fait et tenu à jour. "
            f"Point clé : {obj or c.title} — faites-le simplement, et gardez la preuve."
        )
    return (
        f"Let's talk about the control \"{c.title}\". "
        f"{pl + ' ' if pl else ''}"
        f"In plain terms, the idea is to {obj.lower() if obj else 'put this safeguard in place and be able to show it'}. "
        f"It matters because it lowers risk and shows your organization takes security seriously. "
        f"In practice, {bp.lower() if bp else 'define the rule, assign an owner, and apply it consistently'}. "
        f"During an audit, the assessor mainly looks for evidence that this is actually done and kept current. "
        f"Key takeaway: {obj or c.title} — keep it simple, and keep the proof."
    )


# Master narration prompt (audience: beginners). Mirrors the authored template.
_SCRIPT_SYSTEM = (
    "You are creating a concise video narration script for a cybersecurity control. The audience is "
    "beginners with little or no cybersecurity or compliance experience.\n"
    "OBJECTIVE: Explain what the control is trying to achieve, why it matters, and the key activities "
    "required to comply. The viewer should understand the business purpose of the control, not just "
    "memorize requirements.\n"
    "SCRIPT REQUIREMENTS: 50–120 seconds read aloud (about 100–220 words); clear, simple language; avoid "
    "excessive technical jargon; focus on the intent of the control rather than reading it verbatim; use "
    "real-world analogies when helpful. Explain: (1) what the control is about, (2) why it is important, "
    "(3) the key actions required, and optionally (4) what evidence an auditor would typically look for. "
    "End with a one-sentence summary of the control's objective. Do not use bullet points. Write in a "
    "conversational training-video style.\n"
    "Write the narration in {LANG}. Output ONLY the spoken script, then a final separate line exactly in "
    "the form 'Key takeaway: <one sentence>' (translate the label 'Key takeaway' into {LANG}). Do not "
    "output the control id or name as headers."
)


async def _llm_scripts(db: AsyncSession, c: Control, lang: str, instructions: str = "") -> tuple[str, str]:
    s = await get_llm_settings(db)
    user_msg = (
        f"Control ID: {c.ref}\n"
        f"Control Name: {c.title}\n"
        f"Key Points to Cover: {_key_points(c)}\n"
        f"Expected Evidence: {(c.evidence_best_practices or '').strip() or '(none provided)'}"
    )
    if instructions.strip():
        user_msg += f"\n\nAdditional instructions from the editor (follow these): {instructions.strip()}"
    lname = "French" if lang == "fr" else "English"
    primary = await chat(s, [
        {"role": "system", "content": _SCRIPT_SYSTEM.replace("{LANG}", lname)},
        {"role": "user", "content": user_msg},
    ], max_tokens=600)

    other = "en" if lang == "fr" else "fr"
    oname = "French" if other == "fr" else "English"
    translated = await chat(s, [
        {"role": "system", "content": (
            f"Translate this cybersecurity training narration into {oname}. Keep it natural, equally short, "
            "and conversational. Keep the final 'Key takeaway' line (translate the label). Output ONLY the translation.")},
        {"role": "user", "content": primary},
    ], max_tokens=600)
    return (primary, translated) if lang == "en" else (translated, primary)


class GenScriptBody(BaseModel):
    lang: str = "en"   # language to draft in; the other is translated
    instructions: str = ""  # optional extra guidance / suggestions for the AI


async def _make_and_save(db: AsyncSession, c: Control, lang: str, instructions: str = "") -> str:
    """Generate the bilingual narration, save it on the control, return the source."""
    s = await get_llm_settings(db)
    source = "template"
    if s.enabled:
        try:
            en, fr = await _llm_scripts(db, c, lang, instructions)
            source = "ai"
        except LlmError:
            en, fr = _template_script(c, "en"), _template_script(c, "fr")
    else:
        en, fr = _template_script(c, "en"), _template_script(c, "fr")
    c.video_script_en, c.video_script_fr = en, fr
    return source


@router.post("/control/{control_id}/script/generate")
async def generate_script(control_id: str, body: GenScriptBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Generate the beginner narration (EN + FR), save it on the control, and return it.
    Optional `instructions` steer the AI. Falls back to a template if AI is off/fails."""
    _require_admin(current_user)
    c = await _get_control(db, control_id)
    lang = body.lang if body.lang in ("en", "fr") else "en"
    source = await _make_and_save(db, c, lang, body.instructions or "")
    await db.commit()
    return {"script_en": c.video_script_en, "script_fr": c.video_script_fr, "source": source}


@router.post("/framework/{fw_id}/scripts/generate")
async def generate_framework_scripts(fw_id: str, body: GenScriptBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Generate scripts for every control in a framework that doesn't have one yet.
    Returns how many were created. (Existing scripts are left untouched.)"""
    _require_admin(current_user)
    fw = await _get_framework(db, fw_id)
    lang = body.lang if body.lang in ("en", "fr") else "en"
    rows = (await db.execute(
        select(Control).where(Control.framework_id == fw.id).order_by(Control.sort_order)
    )).scalars().all()
    created = 0
    for c in rows:
        if c.video_script_en or c.video_script_fr:
            continue
        await _make_and_save(db, c, lang)
        created += 1
    await db.commit()
    return {"created": created, "total": len(rows)}


# ════════════════ CROSS-FRAMEWORK VIDEO REUSE ════════════════

def _norm_title(t: Optional[str]) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


@router.get("/reuse/suggestions")
async def reuse_suggestions(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Find controls in OTHER frameworks that have no video but are equivalent to a
    control that does — via official mappings, then by identical title."""
    _require_admin(current_user)
    rows = (await db.execute(
        select(Control, Framework.name).join(Framework, Framework.id == Control.framework_id)
    )).all()
    have = [(c, fw) for c, fw in rows if (c.video_url or c.video_key)]
    none = [(c, fw) for c, fw in rows if not (c.video_url or c.video_key)]

    by_title: dict[str, list] = {}
    by_ref: dict[str, list] = {}
    for c, fw in none:
        by_title.setdefault(_norm_title(c.title), []).append((c, fw))
        by_ref.setdefault(c.ref.strip().lower(), []).append((c, fw))

    suggestions, seen = [], set()
    for c, fw in have:
        cand = []
        mapped = set()
        if c.mappings:
            for v in c.mappings.values():
                if isinstance(v, list):
                    for r in v:
                        mapped.add(str(r).strip().lower())
        for r in mapped:
            for tc, tfw in by_ref.get(r, []):
                if tfw != fw:
                    cand.append((tc, tfw, "mapping"))
        for tc, tfw in by_title.get(_norm_title(c.title), []):
            if tfw != fw:
                cand.append((tc, tfw, "title"))
        for tc, tfw, reason in cand:
            if tc.id in seen:
                continue
            seen.add(tc.id)
            suggestions.append({
                "source": {"control_id": str(c.id), "ref": c.ref, "framework": fw, "title": c.title,
                           "video": _video_info(c.video_url, c.video_key, f"/videos/file/control/{c.id}")},
                "target": {"control_id": str(tc.id), "ref": tc.ref, "framework": tfw, "title": tc.title},
                "reason": reason,
            })
    suggestions.sort(key=lambda x: (x["target"]["framework"], x["target"]["ref"]))
    return {"suggestions": suggestions, "count": len(suggestions)}


class ReusePair(BaseModel):
    source_control_id: str
    target_control_id: str


class ReuseApplyBody(BaseModel):
    pairs: list[ReusePair] = []


@router.post("/reuse/apply")
async def reuse_apply(body: ReuseApplyBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Copy the source control's video reference onto each confirmed target control."""
    _require_admin(current_user)
    applied = 0
    for pair in body.pairs:
        try:
            sid = uuid.UUID(pair.source_control_id)
            tid = uuid.UUID(pair.target_control_id)
        except (ValueError, TypeError):
            continue
        src = (await db.execute(select(Control).where(Control.id == sid))).scalar_one_or_none()
        tgt = (await db.execute(select(Control).where(Control.id == tid))).scalar_one_or_none()
        if not src or not tgt or not (src.video_url or src.video_key):
            continue
        tgt.video_url = src.video_url
        tgt.video_key = src.video_key
        applied += 1
    await db.commit()
    return {"applied": applied}
