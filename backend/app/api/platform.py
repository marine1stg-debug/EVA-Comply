"""Platform settings API — Super Admin controls monetization behavior."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.platform import get_settings
from app.core.config import settings as cfg
from app.core.email import send_email, sender_address
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.platform import BillingMode

router = APIRouter()

MODES = [
    {"key": "no_card_trial", "name": "No-card free trial", "desc": "Sign up free, full access during the trial, then lock to read-only until they subscribe."},
    {"key": "card_trial", "name": "Card-required trial (Stripe)", "desc": "Collect a card at signup; Stripe runs the trial then auto-charges."},
    {"key": "charge_immediately", "name": "Charge immediately", "desc": "Must complete Stripe checkout at signup — no trial."},
]


def _serialize(s) -> dict:
    return {"billing_mode": s.billing_mode.value, "trial_days": s.trial_days, "modes": MODES}


@router.get("/settings")
async def read_settings(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")
    return _serialize(await get_settings(db))


class SettingsBody(BaseModel):
    billing_mode: str
    trial_days: int


@router.put("/settings")
async def update_settings(body: SettingsBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")
    try:
        mode = BillingMode(body.billing_mode)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid billing mode")
    s = await get_settings(db)
    s.billing_mode = mode
    s.trial_days = max(0, int(body.trial_days))
    await db.commit()
    return _serialize(s)


@router.get("/email-config")
async def email_config(current_user: User = Depends(get_current_user)):
    """Show the active email backend + the three configured sender addresses."""
    if current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")
    return {
        "backend": cfg.EMAIL_BACKEND,
        "smtp_host": cfg.SMTP_HOST,
        "senders": {
            "invoicing": sender_address("invoicing"),
            "cases": sender_address("cases"),
            "noreply": sender_address("noreply"),
        },
    }


class EmailTestBody(BaseModel):
    to: str
    sender: str = "noreply"


@router.post("/email-test")
async def email_test(body: EmailTestBody, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")
    if not body.to.strip():
        raise HTTPException(status_code=400, detail="A recipient is required")
    sender = body.sender if body.sender in ("invoicing", "cases", "noreply") else "noreply"
    ok = send_email(body.to.strip(), "EVA Comply — test email",
                    f"This is a test from the '{sender}' sender via the '{cfg.EMAIL_BACKEND}' backend.",
                    sender=sender)
    return {"ok": ok, "backend": cfg.EMAIL_BACKEND, "from": sender_address(sender)}
