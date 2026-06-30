"""System / readiness panel - Super Admin only.

Read-only. Surfaces (1) the .env requirements with a done/not-done check, and
(2) production-readiness checks. Nothing here changes settings; it just lets the
operator see, in one place, whether the deployment is configured correctly -
including the values that are managed in the server .env and can't be edited in
the app.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.email_settings import EmailSettings

router = APIRouter()

_DEV_SECRET = "dev_secret_key_change_in_production_min_32_chars"
_DEV_DB = ("eva_secret_change_in_prod", "change_me")


@router.get("/readiness")
async def readiness(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != UserRole.super_admin:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Super Admin access required")

    is_prod = settings.ENVIRONMENT == "production"
    secret_ok = settings.SECRET_KEY != _DEV_SECRET and len(settings.SECRET_KEY or "") >= 32
    db_ok = not any(d in (settings.DATABASE_URL or "") for d in _DEV_DB)
    fe = settings.FRONTEND_URL or ""
    fe_ok = bool(fe) and "localhost" not in fe and (fe.startswith("https://") or not is_prod)

    email_row = (await db.execute(select(EmailSettings).limit(1))).scalar_one_or_none()
    email_inapp = bool(email_row and email_row.configured and email_row.backend != "console")
    email_env = settings.EMAIL_BACKEND != "console"
    email_ok = email_inapp or email_env
    email_mode = "inapp" if email_inapp else ("env" if email_env else "none")

    storage_durable = settings.STORAGE_BACKEND in ("r2", "s3")
    stripe_on = bool(settings.STRIPE_SECRET_KEY)

    # Stable keys + raw values; the frontend renders the labels/details in the
    # user's language (so the panel is fully bilingual).
    checklist = [
        {"key": "env_production", "ok": is_prod, "required": True, "meta": {"env": settings.ENVIRONMENT}},
        {"key": "secret_key", "ok": secret_ok, "required": True, "meta": {}},
        {"key": "db_password", "ok": db_ok, "required": True, "meta": {}},
        {"key": "email", "ok": email_ok, "required": True, "meta": {"mode": email_mode, "backend": settings.EMAIL_BACKEND}},
        {"key": "frontend_url", "ok": fe_ok, "required": True, "meta": {"url": fe}},
        {"key": "storage", "ok": storage_durable, "required": False, "meta": {"backend": settings.STORAGE_BACKEND}},
        {"key": "stripe", "ok": stripe_on, "required": False, "meta": {}},
    ]
    required_done = sum(1 for c in checklist if c["required"] and c["ok"])
    required_total = sum(1 for c in checklist if c["required"])

    return {
        "environment": settings.ENVIRONMENT,
        "production": is_prod,
        "required_done": required_done,
        "required_total": required_total,
        "all_required_ok": required_done == required_total,
        "checklist": checklist,
        # Items the API can't verify (managed by nginx / Caddy, not the app).
        "notes": ["basic_auth", "caddy_https"],
    }
