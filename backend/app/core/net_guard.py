"""Outbound URL validation to prevent server-side request forgery (SSRF).

Used by the LLM connector, the only place the server makes an HTTP request to a
URL chosen by an (admin) user. Without this, the configured base URL could point
at the cloud metadata endpoint (169.254.169.254), localhost, or internal-only
services, and the response — plus the configured API key — could be exfiltrated.

Self-hosted LLMs (e.g. Ollama on localhost, an internal vLLM) are a legitimate
use case, so private/loopback targets are allowed ONLY when the operator opts in
via ``LLM_ALLOW_PRIVATE_NETWORKS=true``. The default is to block them.

This validation only ever affects the LLM connector feature. It never touches
authentication or general app access.
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from app.core.config import settings


class UrlNotAllowed(ValueError):
    """Raised when a URL is rejected by the SSRF guard."""


def _is_blocked_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True  # unparseable → treat as unsafe
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local      # includes 169.254.0.0/16 (cloud metadata)
        or addr.is_reserved
        or addr.is_multicast
        or addr.is_unspecified
    )


def validate_outbound_url(url: str, *, allow_private: bool | None = None) -> None:
    """Validate that ``url`` is safe for the server to call.

    Raises :class:`UrlNotAllowed` with an admin-friendly message on rejection.
    Resolves the hostname and checks every returned address, so a hostname that
    maps to a private/loopback IP is also blocked (mitigates DNS rebinding).
    """
    if allow_private is None:
        allow_private = bool(getattr(settings, "LLM_ALLOW_PRIVATE_NETWORKS", False))

    parsed = urlparse((url or "").strip())
    if parsed.scheme not in ("http", "https"):
        raise UrlNotAllowed("URL must start with http:// or https://")
    host = parsed.hostname
    if not host:
        raise UrlNotAllowed("URL is missing a host")

    if allow_private:
        return  # operator has explicitly opted in to internal targets

    # Resolve the host to all of its IPs and reject if any is internal.
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror:
        raise UrlNotAllowed(f"Could not resolve host '{host}'")

    for info in infos:
        ip = info[4][0]
        if _is_blocked_ip(ip):
            raise UrlNotAllowed(
                f"'{host}' resolves to a private/loopback address ({ip}), which is "
                "blocked for security. If this is an internal LLM you trust, set "
                "LLM_ALLOW_PRIVATE_NETWORKS=true in the server environment."
            )
