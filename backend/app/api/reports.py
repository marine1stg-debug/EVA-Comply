"""
Reports API — list report types and generate them synchronously as a download.
PDF (WeasyPrint) and Word (python-docx) for narrative reports; Excel for the
evidence register. Targets the selected client (reviewers) or the user's tenant.
"""
import urllib.parse
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.entitlements import ensure_feature
from app.core.client_context import resolve_org
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantType
from app import reports_gen

router = APIRouter()

REPORT_TYPES = [
    {"key": "readiness", "name": "Audit Readiness Report", "desc": "Full control-by-control posture with evidence status.", "formats": ["pdf", "docx"], "icon": "🛡"},
    {"key": "gap", "name": "Gap Analysis", "desc": "Outstanding and high-risk controls needing attention.", "formats": ["pdf", "docx"], "icon": "⚠️"},
    {"key": "recommendations", "name": "Recommendations & Top 10", "desc": "Top 10 priorities, quick wins, and the full remediation list.", "formats": ["pdf", "docx"], "icon": "✦"},
    {"key": "executive", "name": "Executive Summary", "desc": "One-page compliance & maturity overview for leadership.", "formats": ["pdf", "docx"], "icon": "📄"},
    {"key": "evidence", "name": "Evidence Register", "desc": "Excel register + a ZIP of all evidence files, foldered by framework & control.", "formats": ["zip"], "icon": "📊"},
]
_VALID = {r["key"] for r in REPORT_TYPES}


@router.get("/")
async def list_reports(current_user: User = Depends(get_current_user)):
    return {"types": REPORT_TYPES}


class GenerateBody(BaseModel):
    report_type: str
    format: str = "pdf"   # pdf | docx (evidence always xlsx)


@router.post("/generate")
async def generate_report(body: GenerateBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await ensure_feature(db, current_user, "reports")
    if body.report_type not in _VALID:
        raise HTTPException(status_code=400, detail="Unknown report type")
    fmt = body.format if body.format in ("pdf", "docx") else "pdf"
    org_id = await resolve_org(db, current_user) or current_user.tenant_id
    if org_id is None:
        raise HTTPException(status_code=400, detail="No client organization in scope")
    try:
        content, mime, filename = await reports_gen.build_report(db, org_id, body.report_type, fmt)
    except Exception as e:  # pragma: no cover - surface generation errors clearly
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")
    quoted = urllib.parse.quote(filename)
    return Response(
        content=content, media_type=mime,
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{quoted}"},
    )


class AggregateBody(BaseModel):
    format: str = "pdf"   # pdf | docx


@router.post("/aggregate")
async def generate_aggregate(body: AggregateBody, current_user: User = Depends(get_current_user),
                             db: AsyncSession = Depends(get_db)):
    """Portfolio report across many clients: an MSP's whole base, or — for a
    super admin — every client org. Client-level roles cannot run it."""
    await ensure_feature(db, current_user, "reports")
    role = current_user.role
    if role == UserRole.super_admin:
        scope = "All clients (EVA)"
        orgs = (await db.execute(
            select(Tenant.id).where(Tenant.tenant_type == TenantType.single_client,
                                    Tenant.archived == False)  # noqa: E712
        )).scalars().all()
    elif role in (UserRole.msp_admin, UserRole.msp_analyst):
        msp = (await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))).scalar_one_or_none()
        scope = msp.name if msp else "MSP portfolio"
        orgs = (await db.execute(
            select(Tenant.id).where(Tenant.parent_msp_id == current_user.tenant_id,
                                    Tenant.archived == False)  # noqa: E712
        )).scalars().all()
    else:
        raise HTTPException(status_code=403, detail="Aggregate reports are for MSP and EVA accounts only")
    if not orgs:
        raise HTTPException(status_code=400, detail="No client organizations in scope")
    fmt = body.format if body.format in ("pdf", "docx") else "pdf"
    try:
        content, mime, filename = await reports_gen.build_aggregate_report(db, list(orgs), scope, fmt)
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")
    quoted = urllib.parse.quote(filename)
    return Response(content=content, media_type=mime,
                    headers={"Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{quoted}"})
