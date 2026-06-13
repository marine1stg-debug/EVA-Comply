"""Filesystem-backed policy template library.

EVA drops generated Word policies into `backend/policy_library/` (mounted into
the API container at /app/policy_library). Files are named by a slug of the
policy name, e.g. "Access Control Policy" -> Access_Control_Policy.docx.
"""
import os
import re

# /app/policy_library in Docker; resolves relative to the backend root otherwise.
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_DIR = os.environ.get("POLICY_TEMPLATE_DIR", os.path.join(_BACKEND_ROOT, "policy_library"))


def slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", name or "").strip("_")


def path_for(name: str) -> str:
    return os.path.join(TEMPLATE_DIR, slug(name) + ".docx")


def has_template(name: str) -> bool:
    return os.path.isfile(path_for(name))


def available(names) -> list:
    return sorted({n for n in names if has_template(n)})
