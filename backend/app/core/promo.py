"""Promo-code resolution shared by signup and the public validation endpoint."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.promo import PromoCode

MODE_HINT = {
    "no_card_trial": "Free trial - no card required",
    "card_trial": "Card required - free during the trial, then auto-charges",
    "charge_immediately": "Payment required to start",
}


def is_usable(p: PromoCode) -> bool:
    if not p.is_active:
        return False
    if p.expires_at and p.expires_at < datetime.now(timezone.utc):
        return False
    if p.max_uses is not None and p.uses >= p.max_uses:
        return False
    return True


async def resolve_promo(db: AsyncSession, code: Optional[str]) -> Optional[PromoCode]:
    """Return a usable promo code (case-insensitive) or None."""
    if not code or not code.strip():
        return None
    p = (await db.execute(
        select(PromoCode).where(func.lower(PromoCode.code) == code.strip().lower())
    )).scalar_one_or_none()
    if p and is_usable(p):
        return p
    return None
