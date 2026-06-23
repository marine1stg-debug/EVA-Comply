# -*- coding: utf-8 -*-
"""Selective backup / restore — Super Admin only.

Pick data categories (and optionally specific client orgs), then either download
a JSON bundle or keep it as a server-side snapshot. Restore merges a bundle back
in (upsert by primary key — never deletes).
"""
import os
import io
import json
import uuid
import zipfile
import datetime as dt
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.core.audit import record as audit_record
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantType
from app.models.backup import Backup
from app.core import backup_io as bio

router = APIRouter()

BACKUP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backups"))
os.makedirs(BACKUP_DIR, exist_ok=True)

# Source framework catalogs (EN + FR xlsx) bundled with the app.
CATALOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "catalog_data"))


def _zip_bytes(files: dict) -> bytes:
    """files: {arcname: bytes} → in-memory zip bytes."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue()


def _require_super(user: User):
    if user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Backup & restore is Super Admin only")


def _path(fid) -> str:
    return os.path.join(BACKUP_DIR, f"{fid}.json")


def _scope_text(categories: list, client_ids: list) -> str:
    cats = ", ".join(bio.CATEGORIES.get(c, (c,))[0] for c in categories) or "—"
    who = f"{len(client_ids)} client(s)" if client_ids else "tous les clients"
    return f"{cats} · {who}"


# ── options (what can be backed up) ──────────────────────────────────────────
@router.get("/options")
async def options(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_super(current_user)
    cats = []
    for key, (label, scoped, models) in bio.CATEGORIES.items():
        rows = 0
        for model, _f in models:
            rows += (await db.execute(select(func.count()).select_from(model))).scalar_one()
        cats.append({"key": key, "label": label, "client_scoped": scoped,
                     "tables": [m.__tablename__ for m, _ in models], "rows": rows})
    clients = (await db.execute(
        select(Tenant).where(Tenant.tenant_type != TenantType.eva_internal).order_by(Tenant.name)
    )).scalars().all()
    return {
        "categories": cats,
        "clients": [{"id": str(t.id), "name": t.name, "type": t.tenant_type.value} for t in clients],
    }


# ── create a backup ──────────────────────────────────────────────────────────
class SnapshotBody(BaseModel):
    label: str = ""
    categories: list[str] = []
    client_ids: list[str] = []
    store: bool = True          # keep a server-side snapshot
    download: bool = False       # also stream the bundle back for download
    fmt: str = "json"            # download format: "json" | "zip"


@router.post("/snapshot")
async def create_snapshot(body: SnapshotBody, current_user: User = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    _require_super(current_user)
    cats = [c for c in body.categories if c in bio.CATEGORIES]
    if not cats:
        raise HTTPException(status_code=400, detail="Choisissez au moins une catégorie")
    bundle = await bio.export_bundle(db, cats, body.client_ids)
    summary = bio.bundle_summary(bundle)
    payload = json.dumps(bundle, ensure_ascii=False).encode("utf-8")

    fid = uuid.uuid4()
    if body.store:
        with open(_path(fid), "wb") as f:
            f.write(payload)
        row = Backup(
            id=fid, label=body.label or f"Sauvegarde {dt.datetime.utcnow():%Y-%m-%d %H:%M}",
            created_by=current_user.id, created_by_name=current_user.display_name or "",
            categories=cats, client_ids=[str(c) for c in body.client_ids],
            scope=_scope_text(cats, body.client_ids),
            total_rows=summary["total_rows"], size_bytes=len(payload),
            filename=f"{fid}.json",
        )
        db.add(row)
        await db.commit()

    if body.download or not body.store:
        stamp = f"{dt.datetime.utcnow():%Y%m%d-%H%M}"
        if (body.fmt or "json").lower() == "zip":
            zbytes = _zip_bytes({f"eva-backup-{stamp}.json": payload})
            return Response(content=zbytes, media_type="application/zip", headers={
                "Content-Disposition": f'attachment; filename="eva-backup-{stamp}.zip"'})
        return JSONResponse(content=bundle, headers={
            "Content-Disposition": f'attachment; filename="eva-backup-{stamp}.json"'})
    return {"ok": True, "id": str(fid), "summary": summary}


@router.get("/snapshots")
async def list_snapshots(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_super(current_user)
    rows = (await db.execute(select(Backup).order_by(Backup.created_at.desc()))).scalars().all()
    return {"snapshots": [{
        "id": str(b.id), "label": b.label, "scope": b.scope,
        "categories": b.categories or [], "client_ids": b.client_ids or [],
        "total_rows": b.total_rows, "size_bytes": b.size_bytes,
        "created_by": b.created_by_name,
        "created_at": b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else "—",
    } for b in rows]}


@router.get("/snapshots/{snap_id}/download")
async def download_snapshot(snap_id: str, fmt: str = "json",
                            current_user: User = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    _require_super(current_user)
    b = await db.get(Backup, _as_uuid(snap_id))
    if not b or not os.path.exists(_path(b.id)):
        raise HTTPException(status_code=404, detail="Sauvegarde introuvable")
    json_name = b.filename or f"{b.id}.json"
    if (fmt or "json").lower() == "zip":
        with open(_path(b.id), "rb") as f:
            data = f.read()
        zbytes = _zip_bytes({json_name: data})
        zip_name = json_name.rsplit(".", 1)[0] + ".zip"
        return Response(content=zbytes, media_type="application/zip", headers={
            "Content-Disposition": f'attachment; filename="{zip_name}"'})
    return FileResponse(_path(b.id), media_type="application/json", filename=json_name)


@router.get("/full")
async def full_backup(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Complete backup: ALL database data (every category, as JSON) PLUS every
    uploaded file (evidence, uploaded/replaced policy documents) in one zip."""
    _require_super(current_user)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    bundle = await bio.export_bundle(db, list(bio.CATEGORIES.keys()), [])
    payload = json.dumps(bundle, ensure_ascii=False).encode("utf-8")
    out_path = os.path.join(BACKUP_DIR, f"eva-full-backup-{stamp}.zip")
    uploads_root = settings.STORAGE_LOCAL_PATH
    file_count = 0
    # Stream files straight into the zip on disk (avoids holding everything in memory).
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"data/eva-data-{stamp}.json", payload)
        if os.path.isdir(uploads_root):
            for root, _dirs, files in os.walk(uploads_root):
                for fn in files:
                    fp = os.path.join(root, fn)
                    arc = os.path.join("uploads", os.path.relpath(fp, uploads_root))
                    try:
                        z.write(fp, arc)
                        file_count += 1
                    except OSError:
                        pass
        z.writestr("MANIFEST.txt", (
            "EVA Comply — FULL BACKUP\n"
            f"Created: {dt.datetime.now().isoformat()}\n"
            f"Data categories: {', '.join(bio.CATEGORIES.keys())}\n"
            f"Uploaded files included: {file_count}\n\n"
            "Contents:\n"
            "  data/eva-data-*.json   — all database records (restore via the Restore tab / API)\n"
            "  uploads/...            — evidence files and uploaded/replaced policy documents\n\n"
            "Note: the 18 built-in policy templates and framework catalogs ship with the\n"
            "application image and are not duplicated here.\n"
        ).encode("utf-8"))
    return FileResponse(out_path, media_type="application/zip",
                        filename=f"eva-full-backup-{stamp}.zip")


@router.get("/frameworks.zip")
async def download_frameworks_zip(current_user: User = Depends(get_current_user)):
    """Download all bundled framework catalogs (EN + FR .xlsx) as a single zip."""
    _require_super(current_user)
    files = (sorted(f for f in os.listdir(CATALOG_DIR) if f.lower().endswith(".xlsx"))
             if os.path.isdir(CATALOG_DIR) else [])
    if not files:
        raise HTTPException(status_code=404, detail="Aucun catalogue de référentiel trouvé")
    payload = {}
    for name in files:
        with open(os.path.join(CATALOG_DIR, name), "rb") as f:
            payload[name] = f.read()
    payload["README.txt"] = (
        "EVA Comply — catalogues de référentiels (EN + FR)\n"
        f"Exporté le {dt.datetime.utcnow():%Y-%m-%d %H:%M} UTC\n"
        f"{len(files)} fichiers : " + ", ".join(files) + "\n"
    ).encode("utf-8")
    zbytes = _zip_bytes(payload)
    fname = f"eva-frameworks-{dt.datetime.utcnow():%Y%m%d}.zip"
    return Response(content=zbytes, media_type="application/zip", headers={
        "Content-Disposition": f'attachment; filename="{fname}"'})


@router.delete("/snapshots/{snap_id}")
async def delete_snapshot(snap_id: str, current_user: User = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    _require_super(current_user)
    b = await db.get(Backup, _as_uuid(snap_id))
    if not b:
        raise HTTPException(status_code=404, detail="Sauvegarde introuvable")
    try:
        os.remove(_path(b.id))
    except OSError:
        pass
    await db.delete(b)
    await db.commit()
    return {"ok": True}


# ── restore (merge / upsert) ─────────────────────────────────────────────────
async def _do_restore(db: AsyncSession, bundle: dict, categories: Optional[list],
                      *, trusted: bool, user: User) -> dict:
    if not isinstance(bundle, dict) or "tables" not in bundle:
        raise HTTPException(status_code=400, detail="Fichier de sauvegarde invalide")
    # SECURITY: only restore bundles produced by this system. Server-side
    # snapshots are inherently trusted; uploaded files must carry a valid
    # signature, which blocks a hand-crafted bundle from escalating roles or
    # overwriting another tenant's data.
    if not trusted and not bio.verify_bundle(bundle):
        raise HTTPException(
            status_code=400,
            detail=("Ce fichier de sauvegarde n'est pas signé par ce système et ne peut "
                    "pas être restauré. Seules les sauvegardes exportées depuis EVA Comply "
                    "sont acceptées."),
        )
    try:
        counts = await bio.import_bundle(db, bundle, categories or None)
        await audit_record(db, user, "backup.restore",
                           target=",".join(categories) if categories else "all")
        await db.commit()
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Échec de la restauration : {e}")
    total = sum(c["inserted"] + c["updated"] for c in counts.values())
    return {"ok": True, "applied": total, "tables": counts}


class RestoreSnapshotBody(BaseModel):
    snapshot_id: str
    categories: list[str] = []


@router.post("/restore/snapshot")
async def restore_snapshot(body: RestoreSnapshotBody, current_user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    _require_super(current_user)
    b = await db.get(Backup, _as_uuid(body.snapshot_id))
    if not b or not os.path.exists(_path(b.id)):
        raise HTTPException(status_code=404, detail="Sauvegarde introuvable")
    with open(_path(b.id), "rb") as f:
        bundle = json.loads(f.read().decode("utf-8"))
    # Server-side snapshots are written only by this app and are super-admin
    # gated, so they are trusted regardless of signature (covers pre-signing snapshots).
    return await _do_restore(db, bundle, body.categories, trusted=True, user=current_user)


@router.post("/restore/upload")
async def restore_upload(file: UploadFile = File(...), categories: str = Form(""),
                         current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_super(current_user)
    try:
        bundle = json.loads((await file.read()).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="JSON invalide")
    cats = [c for c in (categories.split(",") if categories else []) if c]
    # Uploaded files are untrusted — _do_restore requires a valid signature.
    return await _do_restore(db, bundle, cats, trusted=False, user=current_user)


def _as_uuid(v: str) -> uuid.UUID:
    try:
        return uuid.UUID(v)
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Identifiant invalide")
