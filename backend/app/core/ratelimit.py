"""Lightweight in-process, per-IP sliding-window rate limiter.

Dependency-free (no Redis, no extra packages) so it can't break the build or a
deployment. Counters live in memory per worker process; with multiple workers
each enforces its own share, which is still a meaningful brake on brute force /
credential stuffing on the authentication endpoints.

Limits are deliberately generous — normal interactive use never hits them. The
limiter FAILS OPEN: any internal error lets the request through rather than
locking users out.
"""
from __future__ import annotations

import threading
import time

from fastapi import HTTPException, Request

_LOCK = threading.Lock()
# key -> list[timestamps] within the current window
_HITS: dict[str, list[float]] = {}
_LAST_PRUNE = [0.0]


def client_ip(request: Request) -> str:
    """Real client IP for rate-limit bucketing.

    Prefer X-Real-IP: nginx computes it from the proxy chain via its realip
    module (trusting only the internal Caddy/nginx hops), so it is the genuine
    client address and NOT spoofable by a client-supplied X-Forwarded-For. Fall
    back to the LAST X-Forwarded-For entry (closest, hardest to spoof) and
    finally the socket peer for non-proxied/local runs.
    """
    xri = request.headers.get("x-real-ip")
    if xri:
        return xri.strip()
    xff = request.headers.get("x-forwarded-for")
    if xff:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if parts:
            return parts[-1]
    return request.client.host if request.client else "unknown"


def _prune(now: float, window: float) -> None:
    # Opportunistic cleanup so the dict can't grow unbounded.
    if now - _LAST_PRUNE[0] < 60:
        return
    _LAST_PRUNE[0] = now
    cutoff = now - max(window, 3600)
    for k in list(_HITS.keys()):
        kept = [t for t in _HITS[k] if t > cutoff]
        if kept:
            _HITS[k] = kept
        else:
            _HITS.pop(k, None)


def enforce(request: Request, bucket: str, *, limit: int, window_seconds: int) -> None:
    """Raise HTTP 429 if this IP exceeds ``limit`` hits in ``window_seconds``.

    ``bucket`` namespaces the counter (e.g. "login") so different endpoints
    don't share a budget.
    """
    try:
        now = time.monotonic()
        key = f"{bucket}:{client_ip(request)}"
        with _LOCK:
            _prune(now, window_seconds)
            hits = [t for t in _HITS.get(key, []) if t > now - window_seconds]
            if len(hits) >= limit:
                retry = int(window_seconds - (now - hits[0])) + 1
                raise HTTPException(
                    status_code=429,
                    detail="Too many attempts. Please wait a moment and try again.",
                    headers={"Retry-After": str(max(1, retry))},
                )
            hits.append(now)
            _HITS[key] = hits
    except HTTPException:
        raise
    except Exception:
        # Fail open — never block a legitimate request because of a limiter bug.
        return
