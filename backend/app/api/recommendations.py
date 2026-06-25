"""Recommendations API - per-client remediation actions for maturity gaps.

GET    /                       rollup for the in-scope client (all + Top 10 + Quick Wins)
POST   /generate               (re)generate for every gapped control (source=premade|ai)
GET    /control/{control_id}    recommendations for one control (control-view panel)
POST   /control/{control_id}/generate   generate for a single control
PATCH  /{rec_id}               edit status / effort / impact / text
DELETE /{rec_id}               remove
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.auth import get_current_user
from app.core.client_context import resolve_org, CLIENT_ROLES
from app.core.i18n import get_lang, loc, loc_domain
from app.models.user import User, UserRole
from app.models.framework import Control
from app.models.recommendation import Recommendation
from app.core.llm import get_llm_settings, LlmError
from app.core import recommendations as engine

router = APIRouter()

REVIEWER_ROLES = {UserRole.super_admin, UserRole.eva_auditor, UserRole.msp_admin, UserRole.msp_analyst}
_EFFORT = {"low", "medium", "high"}
_STATUS = {"open", "in_progress", "done", "dismissed"}


def _risk(c: Control) -> str:
    return engine._risk_value(c.risk_rating)


def _serialize(r: Recommendation, c: Control, lang: str = "en") -> dict:
    risk = engine._risk_value(c.risk_rating)
    return {
        "id": str(r.id),
        "control_id": str(c.id),
        "control_ref": c.ref,
        "control_title": loc(c, "title", lang),
        "domain": loc_domain(c.domain, lang) or "General",
        "risk": risk,
        "source": r.source,
        "title": loc(r, "title", lang),
        "text": loc(r, "text", lang),
        "rationale": r.rationale,
        "effort": r.effort,
        "impact": r.impact,
        "current_level": r.current_level,
        "target_level": r.target_level,
        "gap": (r.target_level - r.current_level) if (r.target_level is not None and r.current_level is not None) else None,
        "status": r.status,
        "is_top10": bool(r.is_top10),
        "quick_win": engine.is_quick_win(r.effort, r.impact),
        "priority": engine.priority_score(
            r.effort, r.impact,
            (r.target_level - r.current_level) if (r.target_level is not None and r.current_level is not None) else None,
            risk,
        ),
    }


async def _scoped_org(db, user) -> uuid.UUID:
    org_id = await resolve_org(db, user)
    if org_id is None:
        raise HTTPException(status_code=400, detail="No client organization in scope")
    return org_id


async def _all_for_org(db: AsyncSession, org_id, lang: str = "en") -> list[dict]:
    rows = (await db.execute(
        select(Recommendation, Control)
        .join(Control, Control.id == Recommendation.control_id)
        .where(Recommendation.org_id == org_id)
    )).all()
    items = [_serialize(r, c, lang) for r, c in rows]
    items.sort(key=lambda x: x["priority"], reverse=True)
    return items


@router.get("/")
async def list_recommendations(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), lang: str = Depends(get_lang)):
    org_id = await resolve_org(db, current_user)
    if org_id is None:
        return {"recommendations": [], "top10": [], "quick_wins": [], "counts": {},
                "needs_client": current_user.role not in CLIENT_ROLES, "can_generate": False, "has_llm": False}
    items = await _all_for_org(db, org_id, lang)
    active = [i for i in items if i["status"] not in ("done", "dismissed")]
    quick = [i for i in active if i["quick_win"]]
    pinned = [i for i in active if i["is_top10"]]
    # Top 10 = the manually/AI-flagged set if any, else the highest-priority 10.
    top10 = (pinned if pinned else active[:10])
    llm = await get_llm_settings(db)
    counts = {
        "total": len(items),
        "open": sum(1 for i in items if i["status"] == "open"),
        "in_progress": sum(1 for i in items if i["status"] == "in_progress"),
        "done": sum(1 for i in items if i["status"] == "done"),
        "quick_wins": len(quick),
        "top10": len(pinned),
    }
    return {
        "recommendations": items,
        "top10": top10,
        "top10_pinned": bool(pinned),
        "quick_wins": quick,
        "counts": counts,
        "needs_client": False,
        "can_generate": current_user.role in REVIEWER_ROLES,
        "has_llm": bool(llm.enabled),
    }


@router.post("/auto-top10")
async def auto_top10(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Flag the 10 highest-priority active recommendations as Top 10 (clears any
    prior flags first). Ranking = impact × gap × control risk, effort-weighted."""
    if current_user.role not in REVIEWER_ROLES:
        raise HTTPException(status_code=403, detail="Only reviewers can set the Top 10")
    org_id = await _scoped_org(db, current_user)
    rows = (await db.execute(
        select(Recommendation, Control)
        .join(Control, Control.id == Recommendation.control_id)
        .where(Recommendation.org_id == org_id)
    )).all()
    scored = []
    for r, c in rows:
        r.is_top10 = False  # reset
        if r.status in ("done", "dismissed"):
            continue
        gap = (r.target_level - r.current_level) if (r.target_level is not None and r.current_level is not None) else None
        scored.append((engine.priority_score(r.effort, r.impact, gap, engine._risk_value(c.risk_rating)), r))
    scored.sort(key=lambda t: t[0], reverse=True)
    for _, r in scored[:10]:
        r.is_top10 = True
    await db.commit()
    return {"flagged": min(10, len(scored))}


class GenerateBody(BaseModel):
    source: str = "premade"   # premade | ai
    overwrite: bool = True     # replace existing generated recs (keeps manual)


async def _generate(db: AsyncSession, org_id, source: str, overwrite: bool,
                    only_control: uuid.UUID | None = None) -> dict:
    gaps = await engine.gather_gaps(db, org_id)
    if only_control is not None:
        gaps = [g for g in gaps if g["control"].id == only_control]

    llm = None
    if source == "ai":
        llm = await get_llm_settings(db)
        if not llm.enabled:
            raise HTTPException(status_code=400, detail="The AI connector is disabled. Configure it under AI Connector first.")

    # Clear prior generated recs of this source (manual recs are always kept).
    if overwrite and (gaps or only_control is not None):
        cond = [Recommendation.org_id == org_id, Recommendation.source == source]
        if only_control is not None:
            cond.append(Recommendation.control_id == only_control)
        else:
            cond.append(Recommendation.control_id.in_([g["control"].id for g in gaps]))
        await db.execute(delete(Recommendation).where(and_(*cond)))

    created = 0
    errors: list[str] = []
    for g in gaps:
        c: Control = g["control"]
        if source == "ai":
            try:
                recs = [await engine.ai_for_control(llm, g)]
            except LlmError as e:
                errors.append(str(e))
                continue
        else:
            recs = engine.premade_for_control(c, g["gap"], g["target"])
        for rec in recs:
            db.add(Recommendation(
                org_id=org_id, control_id=c.id, source=source,
                title=rec["title"], text=rec["text"],
                title_fr=rec.get("title_fr"), text_fr=rec.get("text_fr"),
                effort=rec["effort"], impact=rec["impact"],
                current_level=g["current"], target_level=g["target"],
                status="open",
            ))
            created += 1
    await db.commit()
    out = {"created": created, "gapped_controls": len(gaps), "source": source}
    if errors:
        out["warnings"] = errors[:5]
        out["warning_count"] = len(errors)
    return out


@router.post("/generate")
async def generate(body: GenerateBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role not in REVIEWER_ROLES:
        raise HTTPException(status_code=403, detail="Only reviewers can generate recommendations")
    if body.source not in ("premade", "ai"):
        raise HTTPException(status_code=400, detail="source must be 'premade' or 'ai'")
    org_id = await _scoped_org(db, current_user)
    return await _generate(db, org_id, body.source, body.overwrite)


@router.get("/control/{control_id}")
async def control_recommendations(control_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), lang: str = Depends(get_lang)):
    org_id = await _scoped_org(db, current_user)
    try:
        cid = uuid.UUID(control_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Control not found")
    rows = (await db.execute(
        select(Recommendation, Control)
        .join(Control, Control.id == Recommendation.control_id)
        .where(Recommendation.org_id == org_id, Recommendation.control_id == cid)
    )).all()
    items = [_serialize(r, c, lang) for r, c in rows]
    items.sort(key=lambda x: x["priority"], reverse=True)
    llm = await get_llm_settings(db)
    return {"recommendations": items, "can_generate": current_user.role in REVIEWER_ROLES, "has_llm": bool(llm.enabled)}


@router.post("/control/{control_id}/generate")
async def generate_for_control(control_id: str, body: GenerateBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role not in REVIEWER_ROLES:
        raise HTTPException(status_code=403, detail="Only reviewers can generate recommendations")
    if body.source not in ("premade", "ai"):
        raise HTTPException(status_code=400, detail="source must be 'premade' or 'ai'")
    org_id = await _scoped_org(db, current_user)
    try:
        cid = uuid.UUID(control_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Control not found")
    return await _generate(db, org_id, body.source, body.overwrite, only_control=cid)


@router.delete("/all")
async def delete_all_recommendations(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Remove every recommendation for the in-scope client. Reviewers only."""
    if current_user.role not in REVIEWER_ROLES:
        raise HTTPException(status_code=403, detail="Only reviewers can delete recommendations")
    org_id = await _scoped_org(db, current_user)
    res = await db.execute(delete(Recommendation).where(Recommendation.org_id == org_id))
    await db.commit()
    return {"deleted": res.rowcount}


class RecUpdate(BaseModel):
    status: str | None = None
    effort: str | None = None
    impact: str | None = None
    title: str | None = None
    text: str | None = None
    is_top10: bool | None = None


@router.patch("/{rec_id}")
async def update_recommendation(rec_id: str, body: RecUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role not in REVIEWER_ROLES:
        raise HTTPException(status_code=403, detail="Only reviewers can edit recommendations")
    org_id = await _scoped_org(db, current_user)
    try:
        rid = uuid.UUID(rec_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    rec = (await db.execute(
        select(Recommendation).where(Recommendation.id == rid, Recommendation.org_id == org_id)
    )).scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if body.status is not None:
        if body.status not in _STATUS:
            raise HTTPException(status_code=400, detail="Invalid status")
        rec.status = body.status
    if body.effort is not None:
        if body.effort not in _EFFORT:
            raise HTTPException(status_code=400, detail="Invalid effort")
        rec.effort = body.effort
    if body.impact is not None:
        if body.impact not in _EFFORT:
            raise HTTPException(status_code=400, detail="Invalid impact")
        rec.impact = body.impact
    if body.title is not None:
        rec.title = body.title.strip()[:300] or rec.title
    if body.text is not None and body.text.strip():
        rec.text = body.text.strip()
    if body.is_top10 is not None:
        rec.is_top10 = body.is_top10
    await db.commit()
    c = (await db.execute(select(Control).where(Control.id == rec.control_id))).scalar_one()
    return _serialize(rec, c)


@router.delete("/{rec_id}")
async def delete_recommendation(rec_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role not in REVIEWER_ROLES:
        raise HTTPException(status_code=403, detail="Only reviewers can delete recommendations")
    org_id = await _scoped_org(db, current_user)
    try:
        rid = uuid.UUID(rec_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    res = await db.execute(
        delete(Recommendation).where(Recommendation.id == rid, Recommendation.org_id == org_id)
    )
    await db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return {"deleted": True}
