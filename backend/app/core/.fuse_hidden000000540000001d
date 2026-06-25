"""Upload content validation.

Two layers, designed to block dangerous content WITHOUT rejecting the legitimate
files users actually upload:

  1. **Extension allowlist** (reliable, dependency-free). Per upload kind we permit
     the document / image / archive / media types the feature expects, and reject
     executables, scripts, and markup (.exe, .sh, .js, .html, …).
  2. **Magic-byte sniff** (best-effort, via python-magic). Even if the extension
     looks fine, we reject content that sniffs as an executable, shared library,
     or HTML — catching a payload renamed to a safe extension. If libmagic is
     unavailable, this layer is skipped silently so uploads still work.

Client-supplied Content-Type is never trusted for the decision.
"""
from __future__ import annotations

import os

from fastapi import HTTPException

# Per-kind allowed lowercase extensions (no leading dot).
_DOCS = {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "csv", "txt", "md", "rtf", "odt", "ods"}
# NOTE: SVG is deliberately excluded — it can carry embedded <script>/onload and
# would be a stored-XSS vector if served inline. Use PNG/JPG for image evidence.
_IMAGES = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff", "heic"}
_ARCHIVES = {"zip", "7z", "rar", "gz", "tgz"}
_VIDEO = {"mp4", "mov", "webm", "m4v", "avi", "mkv"}

ALLOWED_EXTENSIONS: dict[str, set[str]] = {
    "evidence": _DOCS | _IMAGES | _ARCHIVES,
    "support": _DOCS | _IMAGES | _ARCHIVES,
    "policy": {"docx"},
    "video": _VIDEO,
}

# If the sniffed MIME starts with any of these, reject regardless of extension.
_DANGEROUS_MIME_PREFIXES = (
    "application/x-dosexec",          # Windows PE/EXE/DLL
    "application/x-executable",       # ELF
    "application/x-elf",
    "application/x-sharedlib",
    "application/x-mach-binary",      # macOS
    "application/x-msdownload",
    "application/vnd.microsoft.portable-executable",
    "text/html",
    "application/xhtml",
    "image/svg",                      # scriptable SVG, even if renamed .png
    "application/x-shellscript",
    "application/x-perl",
    "application/x-python",
    "application/javascript",
    "application/x-php",
)


def _ext(filename: str | None) -> str:
    return os.path.splitext(filename or "")[1].lstrip(".").lower()


def _sniff_mime(data: bytes) -> str | None:
    """Best-effort libmagic sniff. Returns None if magic/libmagic unavailable."""
    try:
        import magic  # python-magic
        return magic.from_buffer(data[:4096], mime=True)
    except Exception:
        return None


def validate_upload(filename: str | None, data: bytes, kind: str = "evidence") -> None:
    """Raise HTTP 400 if the file's extension or sniffed content is not allowed
    for ``kind``. ``kind`` ∈ {evidence, support, policy, video}."""
    allowed = ALLOWED_EXTENSIONS.get(kind, ALLOWED_EXTENSIONS["evidence"])
    ext = _ext(filename)
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"File type .{ext or '?'} is not allowed. Accepted: {', '.join(sorted(allowed))}",
        )
    mime = _sniff_mime(data)
    if mime:
        low = mime.lower()
        if any(low.startswith(p) for p in _DANGEROUS_MIME_PREFIXES):
            raise HTTPException(status_code=400, detail="This file's contents are not permitted.")
