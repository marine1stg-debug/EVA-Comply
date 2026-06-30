"""In-app email / SMTP configuration API - Super Admin only.

Lets the operator set the mail provider from the Administration UI instead of
editing the server .env. Secrets are write-only: the SMTP password and SendGrid
key are accepted on save, stored encrypted, and never returned (GET shows only
whether one is set). Sending "__KEEP__" preserves the stored secret.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.core.secrets_crypto import encrypt
from app.core.email import send_test, reload_email_config
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.email_settings import EmailSettings

router = APIRouter()

KEEP = "__KEEP__"
BACKENDS = {"smtp", "sendgrid", "console"}


def _require_super(user: User):
    if user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")


async def _get_row(db: AsyncSession) -> EmailSettings:
    row = (await db.execute(select(EmailSettings).limit(1))).scalar_one_or_none()
    if not row:
        row = EmailSettings(backend="smtp", smtp_port=587, smtp_tls=True, configured=False)
        db.add(row)
        await db.commit()
        await db.refresh(row)
    return row


def _serialize(r: EmailSettings) -> dict:
    return {
        "configured": r.configured,
        "backend": r.backend,
        "from_email": r.from_email or "",
        "smtp_host": r.smtp_host or "",
        "smtp_port": r.smtp_port or 587,
        "smtp_user": r.smtp_user or "",
        "smtp_tls": r.smtp_tls,
        "has_password": bool(r.smtp_password),
        "has_sendgrid_key": bool(r.sendgrid_api_key),
        # For reference: what the server .env falls back to when not configured here.
        "env_backend": settings.EMAIL_BACKEND,
        "env_from": settings.FROM_EMAIL,
    }


@router.get("/")
async def get_settings(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_super(current_user)
    return _serialize(await _get_row(db))


class EmailBody(BaseModel):
    backend: str = "smtp"
    from_email: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_tls: bool = True
    smtp_password: str | None = None       # None/__KEEP__ keeps; "" clears; else replace
    sendgrid_api_key: str | None = None    # same


@router.put("/")
async def update_settings(body: EmailBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_super(current_user)
    if body.backend not in BACKENDS:
        raise HTTPException(status_code=400, detail="Invalid backend")
    r = await _get_row(db)
    r.backend = body.backend
    r.from_email = body.from_email.strip() or None
    r.smtp_host = body.smtp_host.strip() or None
    r.smtp_port = max(1, min(65535, int(body.smtp_port or 587)))
    r.smtp_user = body.smtp_user.strip() or None
    r.smtp_tls = bool(body.smtp_tls)
    if body.smtp_password is not None and body.smtp_password != KEEP:
        r.smtp_password = encrypt(body.smtp_password.strip() or None)
    if body.sendgrid_api_key is not None and body.sendgrid_api_key != KEEP:
        r.sendgrid_api_key = encrypt(body.sendgrid_api_key.strip() or None)
    r.configured = True
    await db.commit()
    await db.refresh(r)
    reload_email_config()   # so a following "send test" uses the new values now
    return _serialize(r)


@router.post("/test")
async def test_email(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_super(current_user)
    await _get_row(db)  # ensure a row exists
    ok, detail = send_test(current_user.email)
    return {"ok": ok, "detail": detail, "to": current_user.email}
