"""Effective deployment config: in-app platform_settings override the .env.

Read at use time from the single deployment_config row via a short-lived sync
connection (works in both the API and the worker), cached briefly. Every getter
falls back to the .env value when the in-app field is blank, so an unset value
never changes current behavior. Call reload() after a save so it takes effect.
"""
import time

from app.core.config import settings

_cache: dict = {"at": 0.0, "row": None, "loaded": False}
_TTL = 15.0


def reload() -> None:
    _cache.update(at=0.0, row=None, loaded=False)


def _row() -> dict | None:
    now = time.time()
    if _cache["loaded"] and now - _cache["at"] < _TTL:
        return _cache["row"]
    row = None
    try:
        import psycopg2
        from app.core.secrets_crypto import decrypt
        url = settings.DATABASE_URL.replace("+asyncpg", "")
        conn = psycopg2.connect(url, connect_timeout=5)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT site_url, app_name, support_email, from_noreply, from_cases, "
                "from_invoicing, storage_backend, r2_account_id, r2_access_key_id, "
                "r2_secret_access_key, r2_bucket, stripe_secret_key, stripe_webhook_secret, "
                "session_minutes, min_password_length FROM deployment_config LIMIT 1")
            r = cur.fetchone()
        finally:
            conn.close()
        if r:
            row = {
                "site_url": r[0], "app_name": r[1], "support_email": r[2],
                "from_noreply": r[3], "from_cases": r[4], "from_invoicing": r[5],
                "storage_backend": r[6], "r2_account_id": r[7], "r2_access_key_id": r[8],
                "r2_secret_access_key": decrypt(r[9]), "r2_bucket": r[10],
                "stripe_secret_key": decrypt(r[11]), "stripe_webhook_secret": decrypt(r[12]),
                "session_minutes": r[13], "min_password_length": r[14],
            }
    except Exception:
        row = None   # table missing / DB hiccup → pure .env fallback
    _cache.update(at=now, row=row, loaded=True)
    return row


def _v(key: str):
    r = _row()
    return r.get(key) if r else None


# ── Getters (DB value if set, else .env / built-in) ──────────────────────────
def frontend_url() -> str:
    return (_v("site_url") or settings.FRONTEND_URL or "").rstrip("/")


def sender_only(kind: str) -> str:
    """Per-type sender override (in-app, else .env). Empty when none is set -
    the caller falls back to the configured default From address."""
    m = {"noreply": "from_noreply", "cases": "from_cases", "invoicing": "from_invoicing"}
    env = {"noreply": settings.EMAIL_FROM_NOREPLY, "cases": settings.EMAIL_FROM_CASES,
           "invoicing": settings.EMAIL_FROM_INVOICING}
    return (_v(m.get(kind, "")) or env.get(kind, "") or "").strip()


def storage_cfg() -> dict:
    return {
        "backend": (_v("storage_backend") or settings.STORAGE_BACKEND or "local"),
        "account_id": _v("r2_account_id") or settings.R2_ACCOUNT_ID,
        "access_key_id": _v("r2_access_key_id") or settings.R2_ACCESS_KEY_ID,
        "secret_access_key": _v("r2_secret_access_key") or settings.R2_SECRET_ACCESS_KEY,
        "bucket": _v("r2_bucket") or settings.R2_BUCKET_NAME,
    }


def stripe_key() -> str:
    return _v("stripe_secret_key") or settings.STRIPE_SECRET_KEY or ""


def stripe_webhook_secret() -> str:
    return _v("stripe_webhook_secret") or settings.STRIPE_WEBHOOK_SECRET or ""


def session_minutes() -> int:
    v = _v("session_minutes")
    return int(v) if v else int(settings.ACCESS_TOKEN_EXPIRE_MINUTES)


def min_password_length() -> int:
    v = _v("min_password_length")
    return int(v) if v else 12
