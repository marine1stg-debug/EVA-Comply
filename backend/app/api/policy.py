"""Policy template library API — list available templates and download one by
policy name (the .docx EVA placed in backend/policy_library)."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.auth import get_current_user
from app.api.controls import _FAMILY_POLICY
from app.core.policy_library import path_for, has_template, available, slug
from app.models.user import User

router = APIRouter()

# Canonical policy names this app knows about.
POLICY_NAMES = [name for _keys, name in _FAMILY_POLICY] + ["Information Security Policy"]

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@router.get("/")
async def list_templates(current_user: User = Depends(get_current_user)):
    return {"available": available(POLICY_NAMES)}


@router.get("/file")
async def download_template(
    name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not has_template(name):
        raise HTTPException(status_code=404, detail="No template uploaded for this policy yet")
    return FileResponse(path_for(name), media_type=DOCX_MIME, filename=slug(name) + ".docx")
