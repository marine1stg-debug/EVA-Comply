"""Accessor for the single-row platform settings (billing mode + trial length)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import PlatformSettings, BillingMode


async def get_settings(db: AsyncSession) -> PlatformSettings:
    row = (await db.execute(select(PlatformSettings).limit(1))).scalar_one_or_none()
    if not row:
        row = PlatformSettings(billing_mode=BillingMode.no_card_trial, trial_days=14)
        db.add(row)
        await db.commit()
        await db.refresh(row)
    return row
