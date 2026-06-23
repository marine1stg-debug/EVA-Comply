"""LLM connector settings API — super-admin only.

The API key is write-only from the client's perspective: it is accepted on PUT,
stored server-side, and never returned. GET returns a masked hint + has_key
flag. A sentinel ("keep") preserves the stored key on save without re-sending it.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.llm import get_llm_settings, masked_settings, test_connection, PROVIDERS, _resolve_base
from app.core.net_guard import validate_outbound_url, UrlNotAllowed
from app.core.secrets_crypto import encrypt
from app.api.auth import get_current_user
from app.models.user import User, UserRole

router = APIRouter()

_PROVIDER_KEYS = {p["key"] for p in PROVIDERS}
# When the client sends this sentinel as the key, keep the stored one.
KEEP_SENTINEL = "__KEEP__"


def _require_super_admin(user: User):
    if user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")


@router.get("/settings")
async def read_settings(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_super_admin(current_user)
    return masked_settings(await get_llm_settings(db))


class LlmSettingsBody(BaseModel):
    provider: str
    base_url: str = ""
    model: str = ""
    enabled: bool = False
    timeout_seconds: int = 30
    extra_header_name: str = ""
    extra_header_value: str = ""
    # api_key: omit / null = keep stored; "" = clear; any other value = replace.
    api_key: str | None = None


@router.put("/settings")
async def update_settings(body: LlmSettingsBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_super_admin(current_user)
    if body.provider not in _PROVIDER_KEYS:
        raise HTTPException(status_code=400, detail="Invalid provider")

    s = await get_llm_settings(db)
    s.provider = body.provider
    s.base_url = body.base_url.strip() or None
    s.model = body.model.strip() or None
    s.enabled = bool(body.enabled)
    s.timeout_seconds = max(5, min(300, int(body.timeout_seconds or 30)))
    s.extra_header_name = body.extra_header_name.strip() or None

    # SSRF guard: reject a base URL that targets a private/internal address
    # (unless the operator opted in via LLM_ALLOW_PRIVATE_NETWORKS).
    try:
        validate_outbound_url(_resolve_base(s))
    except UrlNotAllowed as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Secrets are encrypted at rest. extra_header_value: None/sentinel keeps.
    if body.extra_header_value != KEEP_SENTINEL:
        s.extra_header_value = encrypt(body.extra_header_value.strip() or None)

    # Key handling: None/sentinel keeps; "" clears; otherwise replace (encrypted).
    if body.api_key is not None and body.api_key != KEEP_SENTINEL:
        s.api_key = encrypt(body.api_key.strip() or None)

    await db.commit()
    await db.refresh(s)
    return masked_settings(s)


@router.post("/test")
async def test(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_super_admin(current_user)
    s = await get_llm_settings(db)
    return await test_connection(db, s)
