"""Private/hosted LLM connector.

Single-row config in ``llm_settings`` (super-admin managed). Supports three
provider styles behind one interface:

  - ``openai``    OpenAI & OpenAI-compatible (Azure, vLLM, LM Studio,
                  OpenRouter, together.ai…)  POST {base}/chat/completions
  - ``anthropic`` Anthropic Messages API      POST {base}/v1/messages
  - ``ollama``    local Ollama server         POST {base}/api/chat

The API key lives server-side only. Nothing here returns it to a client;
callers that serialize settings must use :func:`masked_settings`.

Exposes :func:`chat` (used by the recommendations engine + future evidence
review) and :func:`test_connection` (used by the settings page).
"""
from __future__ import annotations

from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_settings import LlmSettings
from app.core.secrets_crypto import decrypt
from app.core.net_guard import validate_outbound_url, UrlNotAllowed

PROVIDERS = [
    {"key": "openai", "name": "OpenAI-compatible",
     "desc": "OpenAI or any compatible endpoint (Azure OpenAI, vLLM, LM Studio, OpenRouter, Together…).",
     "default_base": "https://api.openai.com/v1", "needs_key": True,
     "model_hint": "gpt-4o-mini"},
    {"key": "anthropic", "name": "Anthropic",
     "desc": "Anthropic Messages API (Claude models).",
     "default_base": "https://api.anthropic.com", "needs_key": True,
     "model_hint": "claude-3-5-sonnet-latest"},
    {"key": "ollama", "name": "Ollama (self-hosted)",
     "desc": "Local or private Ollama server. No API key required by default.",
     "default_base": "http://localhost:11434", "needs_key": False,
     "model_hint": "llama3.1"},
]
_PROVIDER_KEYS = {p["key"] for p in PROVIDERS}
ANTHROPIC_VERSION = "2023-06-01"


class LlmError(Exception):
    """Raised when the connector is misconfigured or the upstream call fails."""


async def get_llm_settings(db: AsyncSession) -> LlmSettings:
    """Fetch (or lazily create) the single-row LLM config."""
    row = (await db.execute(select(LlmSettings).limit(1))).scalar_one_or_none()
    if not row:
        row = LlmSettings(provider="openai", enabled=False, timeout_seconds=30)
        db.add(row)
        await db.commit()
        await db.refresh(row)
    return row


def _mask(key: str | None) -> str | None:
    if not key:
        return None
    tail = key[-4:] if len(key) >= 4 else key
    return f"••••{tail}"


def api_key_plain(s: LlmSettings) -> str | None:
    """Decrypt the stored API key for server-side use (never sent to clients)."""
    return decrypt(s.api_key)


def extra_header_value_plain(s: LlmSettings) -> str | None:
    return decrypt(s.extra_header_value)


def masked_settings(s: LlmSettings) -> dict:
    """Client-safe view - never includes the raw API key."""
    key = api_key_plain(s)
    return {
        "provider": s.provider,
        "base_url": s.base_url or "",
        "model": s.model or "",
        "enabled": bool(s.enabled),
        "timeout_seconds": s.timeout_seconds,
        "extra_header_name": s.extra_header_name or "",
        "has_key": bool(key),
        "key_hint": _mask(key),
        "last_tested_at": s.last_tested_at.isoformat() if s.last_tested_at else None,
        "last_test_ok": s.last_test_ok,
        "last_test_msg": s.last_test_msg,
        "providers": PROVIDERS,
    }


def _resolve_base(s: LlmSettings) -> str:
    base = (s.base_url or "").strip().rstrip("/")
    if base:
        return base
    for p in PROVIDERS:
        if p["key"] == s.provider:
            return p["default_base"]
    raise LlmError(f"Unknown provider '{s.provider}'")


def _build_request(s: LlmSettings, messages: list[dict], max_tokens: int):
    """Return (url, headers, json_body) for the configured provider."""
    base = _resolve_base(s)
    # SSRF guard: never let the server call a private/internal address unless the
    # operator explicitly opted in. Validated again here (defense in depth) even
    # though it is also checked when the URL is saved.
    try:
        validate_outbound_url(base)
    except UrlNotAllowed as e:
        raise LlmError(str(e))
    model = (s.model or "").strip()
    if not model:
        raise LlmError("No model configured.")
    api_key = api_key_plain(s)
    headers: dict[str, str] = {"Content-Type": "application/json"}

    if s.provider == "anthropic":
        url = f"{base}/v1/messages"
        if api_key:
            headers["x-api-key"] = api_key
        headers["anthropic-version"] = ANTHROPIC_VERSION
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        convo = [m for m in messages if m["role"] != "system"]
        body = {"model": model, "max_tokens": max_tokens, "messages": convo}
        if system:
            body["system"] = system
    elif s.provider == "ollama":
        url = f"{base}/api/chat"
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        body = {"model": model, "messages": messages, "stream": False,
                "options": {"num_predict": max_tokens}}
    else:  # openai-compatible
        url = f"{base}/chat/completions"
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        body = {"model": model, "messages": messages, "max_tokens": max_tokens}

    header_value = extra_header_value_plain(s)
    if s.extra_header_name and header_value:
        headers[s.extra_header_name] = header_value
    return url, headers, body


def _parse_response(provider: str, data: dict) -> str:
    """Extract assistant text from a provider-specific response payload."""
    try:
        if provider == "anthropic":
            parts = data.get("content", [])
            return "".join(p.get("text", "") for p in parts if p.get("type") == "text").strip()
        if provider == "ollama":
            return (data.get("message", {}) or {}).get("content", "").strip()
        return (data["choices"][0]["message"]["content"] or "").strip()
    except (KeyError, IndexError, TypeError) as e:
        raise LlmError(f"Unexpected response shape from provider: {e}")


async def chat(s: LlmSettings, messages: list[dict], max_tokens: int = 1024) -> str:
    """One blocking round-trip to the configured LLM. Returns assistant text.

    ``messages`` is a list of {"role": "system|user|assistant", "content": str}.
    Raises :class:`LlmError` on any configuration or transport failure.
    """
    if not s.enabled:
        raise LlmError("LLM connector is disabled.")
    url, headers, body = _build_request(s, messages, max_tokens)
    timeout = max(5, int(s.timeout_seconds or 30))
    try:
        # follow_redirects=False so a 30x to an internal host can't bypass the
        # SSRF guard (which validated only the original URL).
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            resp = await client.post(url, headers=headers, json=body)
    except httpx.HTTPError as e:
        raise LlmError(f"Connection failed: {e}")
    if resp.status_code >= 400:
        snippet = resp.text[:300]
        raise LlmError(f"HTTP {resp.status_code}: {snippet}")
    try:
        data = resp.json()
    except ValueError:
        raise LlmError("Upstream returned non-JSON response.")
    text = _parse_response(s.provider, data)
    if not text:
        raise LlmError("Upstream returned an empty completion.")
    return text


async def test_connection(db: AsyncSession, s: LlmSettings) -> dict:
    """Cheap one-shot round-trip; records the result on the settings row."""
    ok, msg, latency_ms = False, "", None
    started = datetime.now(timezone.utc)
    try:
        if s.provider not in _PROVIDER_KEYS:
            raise LlmError(f"Unknown provider '{s.provider}'.")
        reply = await chat(
            s,
            [
                {"role": "system", "content": "You are a connection test. Reply with exactly: OK"},
                {"role": "user", "content": "ping"},
            ],
            max_tokens=16,
        )
        latency_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        ok = True
        msg = f"Connected. Model replied ({latency_ms} ms): {reply[:80]}"
    except LlmError as e:
        msg = str(e)
    except Exception as e:  # defensive - never leak a stack to the client
        msg = f"Unexpected error: {e}"

    s.last_tested_at = datetime.now(timezone.utc)
    s.last_test_ok = ok
    s.last_test_msg = msg
    await db.commit()
    return {"ok": ok, "message": msg, "latency_ms": latency_ms}
