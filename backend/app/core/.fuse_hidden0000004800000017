"""Transparent at-rest encryption for sensitive DB columns (LLM API key,
custom auth header value, TOTP MFA secret).

Design goals:
  * **Backward compatible.** Existing rows hold plaintext. ``decrypt`` returns
    any value WITHOUT the version marker untouched, so MFA secrets and API keys
    stored before this change keep working. New writes go through ``encrypt``.
  * **No new configuration.** The Fernet key is derived from ``SECRET_KEY``
    (already required to be >=32 chars in production), so deployments need no
    extra env var and nothing breaks on upgrade.
  * **Fail safe.** If a value can't be decrypted (e.g. SECRET_KEY rotated),
    ``decrypt`` returns ``None`` — the feature degrades (key must be re-entered)
    rather than crashing a request.

If ``SECRET_KEY`` ever rotates, previously-encrypted secrets become
unreadable and must be re-entered. Plaintext legacy values are unaffected.
"""
from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

# Marker prefix identifying a value this module produced. Anything lacking it is
# treated as legacy plaintext and returned as-is by ``decrypt``.
_MARKER = "enc:v1:"


def _fernet() -> Fernet:
    # 32-byte key derived deterministically from SECRET_KEY, urlsafe-b64 encoded.
    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt(plaintext: str | None) -> str | None:
    """Encrypt a secret for storage. ``None``/empty pass through unchanged."""
    if not plaintext:
        return plaintext
    token = _fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")
    return _MARKER + token


def decrypt(stored: str | None) -> str | None:
    """Return the plaintext secret.

    * ``None``/empty → ``None``.
    * Legacy plaintext (no marker) → returned unchanged (backward compat).
    * Marked ciphertext → decrypted, or ``None`` if it can't be decrypted.
    """
    if not stored:
        return None
    if not stored.startswith(_MARKER):
        return stored  # legacy plaintext written before encryption was added
    try:
        return _fernet().decrypt(stored[len(_MARKER):].encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        return None


def is_encrypted(stored: str | None) -> bool:
    return bool(stored) and stored.startswith(_MARKER)
