"""In-app deployment configuration API (General / Storage / Payments / Security).

Super Admin only. Secrets (R2 secret key, Stripe keys) are write-only: accepted
on save, stored encrypted, never returned. Sending "__KEEP__" preserves a stored
secret. Every blank field falls back to the server .env, so clearing a value
simply reverts to the .env behavior. All saves are audit-logged.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.core.secrets_crypto import encrypt
from app.core.audit import record as audit_record
from app.core import platform_config as pc
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.platform_settings import PlatformSettings

router = APIRouter()
KEEP = "__KEEP__"


def _require_super(user: User):
    if user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")


async def _row(db: AsyncSession) -> PlatformSettings:
    r = (await db.execute(select(PlatformSettings).limit(1))).scalar_one_or_none()
    if not r:
        r = PlatformSettings()
        db.add(r)
        await db.commit()
        await db.refresh(r)
    return r


def _serialize(r: PlatformSettings) -> dict:
    return {
        "general": {
            "site_url": r.site_url or "", "app_name": r.app_name or "",
            "support_email": r.support_email or "",
            "from_noreply": r.from_noreply or "", "from_cases": r.from_cases or "",
            "from_invoicing": r.from_invoicing or "",
        },
        "storage": {
            "backend": r.storage_backend or "", "r2_account_id": r.r2_account_id or "",
            "r2_access_key_id": r.r2_access_key_id or "", "r2_bucket": r.r2_bucket or "",
            "has_secret": bool(r.r2_secret_access_key),
        },
        "payments": {
            "has_secret_key": bool(r.stripe_secret_key),
            "has_webhook_secret": bool(r.stripe_webhook_secret),
        },
        "security": {
            "session_minutes": r.session_minutes, "min_password_length": r.min_password_length,
        },
        "env": {
            "site_url": settings.FRONTEND_URL, "storage_backend": settings.STORAGE_BACKEND,
            "stripe_enabled": bool(settings.STRIPE_SECRET_KEY),
            "session_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES, "min_password_length": 12,
        },
    }


async def _save(db: AsyncSession, user: User, group: str):
    await db.commit()
    pc.reload()
    try:
        await audit_record(db, user, "platform.config_updated", target=group, org_id=user.tenant_id)
        await db.commit()
    except Exception:
        pass


@router.get("/")
async def get_all(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_super(current_user)
    return _serialize(await _row(db))


class GeneralBody(BaseModel):
    site_url: str = ""
    app_name: str = ""
    support_email: str = ""
    from_noreply: str = ""
    from_cases: str = ""
    from_invoicing: str = ""


@router.put("/general")
async def put_general(b: GeneralBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_super(current_user)
    r = await _row(db)
    r.site_url = b.site_url.strip().rstrip("/") or None
    r.app_name = b.app_name.strip() or None
    r.support_email = b.support_email.strip() or None
    r.from_noreply = b.from_noreply.strip() or None
    r.from_cases = b.from_cases.strip() or None
    r.from_invoicing = b.from_invoicing.strip() or None
    await _save(db, current_user, "general")
    return _serialize(r)


class StorageBody(BaseModel):
    backend: str = ""              # "" | local | r2 | s3
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_bucket: str = ""
    r2_secret_access_key: str | None = None    # None/__KEEP__ keeps; "" clears


@router.put("/storage")
async def put_storage(b: StorageBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_super(current_user)
    if b.backend and b.backend not in ("local", "r2", "s3"):
        raise HTTPException(status_code=400, detail="Invalid storage backend")
    r = await _row(db)
    r.storage_backend = b.backend.strip() or None
    r.r2_account_id = b.r2_account_id.strip() or None
    r.r2_access_key_id = b.r2_access_key_id.strip() or None
    r.r2_bucket = b.r2_bucket.strip() or None
    if b.r2_secret_access_key is not None and b.r2_secret_access_key != KEEP:
        r.r2_secret_access_key = encrypt(b.r2_secret_access_key.strip() or None)
    await _save(db, current_user, "storage")
    return _serialize(r)


@router.post("/storage/test")
async def test_storage(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_super(current_user)
    await _row(db)
    pc.reload()
    from app.core import storage
    key = f"_systest/{uuid.uuid4().hex}.txt"
    payload = b"eva-comply storage test"
    try:
        storage.save_bytes(key, payload)
        ok = storage.exists(key) and storage.read_bytes(key) == payload
        storage.delete(key)
        cfg = pc.storage_cfg()
        return {"ok": bool(ok), "detail": f"Wrote and read back a test object on backend '{cfg['backend']}'." if ok else "Object did not round-trip."}
    except Exception as e:
        return {"ok": False, "detail": f"Storage error: {e}"}


class PaymentsBody(BaseModel):
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None


@router.put("/payments")
async def put_payments(b: PaymentsBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_super(current_user)
    r = await _row(db)
    if b.stripe_secret_key is not None and b.stripe_secret_key != KEEP:
        r.stripe_secret_key = encrypt(b.stripe_secret_key.strip() or None)
    if b.stripe_webhook_secret is not None and b.stripe_webhook_secret != KEEP:
        r.stripe_webhook_secret = encrypt(b.stripe_webhook_secret.strip() or None)
    await _save(db, current_user, "payments")
    return _serialize(r)


@router.post("/payments/test")
async def test_payments(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_super(current_user)
    await _row(db)
    pc.reload()
    key = pc.stripe_key()
    if not key:
        return {"ok": False, "detail": "No Stripe secret key is set."}
    try:
        import stripe
        stripe.api_key = key
        acct = stripe.Account.retrieve()
        return {"ok": True, "detail": f"Connected to Stripe account {getattr(acct, 'id', '?')}."}
    except Exception as e:
        return {"ok": False, "detail": f"Stripe error: {e}"}


class SecurityBody(BaseModel):
    session_minutes: int | None = None      # None = use .env default
    min_password_length: int | None = None


@router.put("/security")
async def put_security(b: SecurityBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_super(current_user)
    r = await _row(db)
    # Clamp to safe ranges; None reverts to .env / built-in default.
    r.session_minutes = max(15, min(43200, int(b.session_minutes))) if b.session_minutes else None
    r.min_password_length = max(8, min(64, int(b.min_password_length))) if b.min_password_length else None
    await _save(db, current_user, "security")
    return _serialize(r)
