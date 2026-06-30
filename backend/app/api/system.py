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


def _check(ok: bool, label: str, detail: str, required: bool = True) -> dict:
    return {"ok": bool(ok), "label": label, "detail": detail, "required": required}


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
    email_detail = ("Configured in-app" if email_inapp
                    else f".env backend: {settings.EMAIL_BACKEND}" if email_env
                    else "Not configured (console only - links would leak)")

    storage_durable = settings.STORAGE_BACKEND in ("r2", "s3")
    stripe_on = bool(settings.STRIPE_SECRET_KEY)

    # ── .env requirements checklist (the box the operator asked for) ──────────
    env_checklist = [
        _check(is_prod, "ENVIRONMENT=production",
               f"Currently '{settings.ENVIRONMENT}'." + ("" if is_prod else " Set to production before go-live.")),
        _check(secret_ok, "SECRET_KEY set (32+ chars, not the dev default)",
               "Strong key in place." if secret_ok else "Generate with: openssl rand -hex 32"),
        _check(db_ok, "POSTGRES_PASSWORD changed from the default",
               "Custom database password." if db_ok else "Still using a default/sample password."),
        _check(email_ok, "Email backend configured (not console)", email_detail),
        _check(fe_ok, "FRONTEND_URL set to your real HTTPS domain",
               fe or "Not set." ),
        _check(storage_durable, "Durable object storage (R2/S3) for evidence",
               f"Backend: {settings.STORAGE_BACKEND}." + ("" if storage_durable else " Local works but isn't durable across rebuilds."),
               required=False),
        _check(stripe_on, "Stripe keys set (only if you charge for plans)",
               "Stripe enabled." if stripe_on else "Not set (billing checkout disabled).", required=False),
    ]

    required_done = sum(1 for c in env_checklist if c["required"] and c["ok"])
    required_total = sum(1 for c in env_checklist if c["required"])

    return {
        "environment": settings.ENVIRONMENT,
        "production": is_prod,
        "required_done": required_done,
        "required_total": required_total,
        "all_required_ok": required_done == required_total,
        "checklist": env_checklist,
        # Note about items the API can't verify (managed by nginx, not the app).
        "notes": [
            "The site password gate (BASIC_AUTH_USER / BASIC_AUTH_PASSWORD) is enforced by nginx and set in the server .env.",
            "HTTPS and your domain are managed by Caddy (caddy/Caddyfile).",
        ],
    }
