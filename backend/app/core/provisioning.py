"""Shared provisioning helpers used by onboarding flows."""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.framework import Control
from app.models.evidence import OrgControl, OrgControlStatus

PLANS = [
    {"key": "professional", "name": "Professional", "price": 499, "tenant_type": "single_client"},
    {"key": "msp_professional", "name": "MSP Professional", "price": 1499, "tenant_type": "msp"},
]


async def assign_frameworks(db: AsyncSession, org_id, framework_ids: list) -> int:
    """Create org_control rows for every control in the given frameworks
    (skipping any that already exist). Returns the number created."""
    if not framework_ids:
        return 0
    fids = []
    for f in framework_ids:
        try:
            fids.append(uuid.UUID(str(f)))
        except (ValueError, TypeError):
            continue
    if not fids:
        return 0

    controls = (await db.execute(
        select(Control.id).where(Control.framework_id.in_(fids))
    )).scalars().all()
    existing = set((await db.execute(
        select(OrgControl.control_id).where(OrgControl.org_id == org_id)
    )).scalars().all())

    created = 0
    for cid in controls:
        if cid in existing:
            continue
        db.add(OrgControl(org_id=org_id, control_id=cid, status=OrgControlStatus.not_started))
        created += 1
    return created
