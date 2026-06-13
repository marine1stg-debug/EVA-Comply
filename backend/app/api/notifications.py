"""Role-aware "action required" notifications for the top-bar bell.

Each item carries a stable `key` (the frontend localises the label), a `count`,
a `severity`, and a deep `link` to the exact place the action is taken.

  • Client view   → evidence returned by MSP/EVA that they must fix
  • MSP view      → client items awaiting their pre-review, and client items returned by EVA
  • EVA / Super   → items awaiting EVA decision, and open support requests
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.auth import get_current_user
from app.api.evidence import _accessible_org_ids
from app.api.support import open_case_count
from app.models.user import User, UserRole
from app.models.evidence import EvidenceItem, EvidenceStatus

router = APIRouter()

CLIENT_ROLES = {UserRole.client_admin, UserRole.contributor, UserRole.viewer}
MSP_ROLES = {UserRole.msp_admin, UserRole.msp_analyst}
EVA_ROLES = {UserRole.super_admin, UserRole.eva_auditor}


async def _count(db: AsyncSession, org_ids, statuses) -> int:
    ids = list(org_ids)
    if not ids:
        return 0
    n = (await db.execute(
        select(func.count(EvidenceItem.id)).where(
            EvidenceItem.org_id.in_(ids),
            EvidenceItem.status.in_(list(statuses)),
        )
    )).scalar() or 0
    return int(n)


@router.get("/")
async def notifications(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    role = current_user.role
    org_ids = await _accessible_org_ids(db, current_user)
    items = []

    if role in CLIENT_ROLES:
        n = await _count(db, {current_user.tenant_id},
                         [EvidenceStatus.rejected, EvidenceStatus.needs_more, EvidenceStatus.msp_flagged])
        if n:
            items.append({"key": "client_returned", "severity": "warning", "count": n, "link": "/evidence"})

    if role in MSP_ROLES:
        client_ids = {o for o in org_ids if o != current_user.tenant_id}
        n = await _count(db, client_ids, [EvidenceStatus.msp_pending])
        if n:
            items.append({"key": "msp_pending", "severity": "info", "count": n, "link": "/review"})
        r = await _count(db, client_ids, [EvidenceStatus.rejected, EvidenceStatus.needs_more])
        if r:
            items.append({"key": "msp_eva_returned", "severity": "warning", "count": r, "link": "/controls"})

    if role in EVA_ROLES:
        n = await _count(db, org_ids, [EvidenceStatus.eva_pending])
        if n:
            items.append({"key": "eva_pending", "severity": "info", "count": n, "link": "/review"})
        cases = await open_case_count(db)
        if cases:
            items.append({"key": "support_open", "severity": "warning", "count": cases, "link": "/support-cases"})

    return {"items": items, "total": sum(i["count"] for i in items)}
