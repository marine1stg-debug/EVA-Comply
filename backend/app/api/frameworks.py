"""
Framework library API — list built-in/custom frameworks and per-framework
detail (domain breakdown, levels, sample controls, orgs-using count).
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
import uuid
import io
import csv
import json

from app.core.database import get_db
from app.core.entitlements import ensure_feature
from app.core.i18n import get_lang, loc, loc_domain
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.framework import (
    Framework, Control, ControlPriority, ControlRisk, ControlCategory,
)
from app.models.evidence import OrgControl

router = APIRouter()

ADMIN_ROLES = {UserRole.super_admin, UserRole.msp_admin}
FW_VISUAL = {
    "CMMC 2.0":     {"icon": "🛡", "color": "#2563EB", "bg": "#EFF6FF"},
    "CMMC 2.0 — Level 1": {"icon": "🛡", "color": "#2563EB", "bg": "#EFF6FF"},
    "CMMC 2.0 — Level 2": {"icon": "🛡", "color": "#1D4ED8", "bg": "#EFF6FF"},
    "NIST CSF":     {"icon": "⎇",  "color": "#7C3AED", "bg": "#EDE9FE"},
    "NIST SP 800-171 Rev. 3": {"icon": "⎇", "color": "#7C3AED", "bg": "#EDE9FE"},
    "ITSP.10.171 (CPCSC)": {"icon": "⚑",  "color": "#D97706", "bg": "#FFFBEB"},
}
PRIORITY_BADGE = {"high": "b-red", "medium": "b-amber", "low": "b-green"}


async def _controls_count(db, fw_id) -> int:
    return (await db.execute(
        select(func.count(Control.id)).where(Control.framework_id == fw_id)
    )).scalar_one()


async def _domains_count(db, fw_id) -> int:
    return (await db.execute(
        select(func.count(func.distinct(Control.domain)))
        .where(Control.framework_id == fw_id, Control.domain.isnot(None))
    )).scalar_one()


async def _orgs_using(db, fw_id) -> int:
    return (await db.execute(
        select(func.count(func.distinct(OrgControl.org_id)))
        .join(Control, Control.id == OrgControl.control_id)
        .where(Control.framework_id == fw_id)
    )).scalar_one()


@router.get("/")
async def list_frameworks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang),
):
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Framework library requires admin access")

    # The Library is the framework CATALOG admins browse and assign from, so it
    # always shows the full set of frameworks an admin can manage — NOT only the
    # selected client's assigned frameworks.
    #   • super_admin → every framework (system + all imported)
    #   • msp_admin   → all system frameworks + ones they imported
    fw_q = select(Framework)
    if current_user.role == UserRole.msp_admin:
        fw_q = fw_q.where(or_(Framework.is_system.is_(True),
                              Framework.imported_by == current_user.id))

    fws = (await db.execute(fw_q)).scalars().all()
    out = []
    for fw in fws:
        vis = FW_VISUAL.get(fw.name, {"icon": "📋", "color": "#2563EB", "bg": "#EFF6FF"})
        out.append({
            "id": str(fw.id),
            "name": fw.name,
            "version": fw.version,
            "desc": loc(fw, "description", lang),
            "type": "system" if fw.is_system else "custom",
            "status": "active" if fw.is_active else "draft",
            "controls": await _controls_count(db, fw.id),
            "domains": await _domains_count(db, fw.id),
            "levels": fw.levels or [],
            "orgs_using": await _orgs_using(db, fw.id),
            "last_updated": fw.updated_at.strftime("%b %d, %Y") if fw.updated_at else "—",
            **vis,
        })
    out.sort(key=lambda f: (f["type"] != "system", f["name"]))
    return {
        "frameworks": out,
        "client_scoped": False,
        "counts": {
            "system": sum(1 for f in out if f["type"] == "system"),
            "custom": sum(1 for f in out if f["type"] == "custom"),
        },
    }


@router.get("/{framework_id}")
async def framework_detail(
    framework_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang),
):
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Framework library requires admin access")
    try:
        fid = uuid.UUID(framework_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Framework not found")
    fw = (await db.execute(select(Framework).where(Framework.id == fid))).scalar_one_or_none()
    if not fw:
        raise HTTPException(status_code=404, detail="Framework not found")

    # Domain breakdown
    dom_rows = await db.execute(
        select(Control.domain, func.count(Control.id))
        .where(Control.framework_id == fid, Control.domain.isnot(None))
        .group_by(Control.domain)
        .order_by(func.count(Control.id).desc())
    )
    domains = [{"name": loc_domain(d, lang), "count": n} for d, n in dom_rows.all()]

    # Sample controls
    srows = (await db.execute(
        select(Control).where(Control.framework_id == fid).order_by(Control.sort_order).limit(6)
    )).scalars().all()
    samples = [{
        "ref": c.ref, "title": loc(c, "title", lang),
        "priority": c.priority.value if c.priority else "low",
        "priorityBadge": PRIORITY_BADGE.get(c.priority.value if c.priority else "low", "b-gray"),
    } for c in srows]

    total = await _controls_count(db, fid)
    vis = FW_VISUAL.get(fw.name, {"icon": "📋", "color": "#2563EB", "bg": "#EFF6FF"})
    return {
        "id": str(fw.id),
        "name": fw.name,
        "version": fw.version,
        "desc": loc(fw, "description", lang),
        "type": "system" if fw.is_system else "custom",
        "status": "active" if fw.is_active else "draft",
        "controls": total,
        "domains": domains,
        "domains_count": len(domains),
        "levels": fw.levels or [],
        "orgs_using": await _orgs_using(db, fid),
        "last_updated": fw.updated_at.strftime("%b %d, %Y") if fw.updated_at else "—",
        "samples": samples,
        **vis,
    }


# ════════════════ CSV / XLSX IMPORT ════════════════
TARGET_FIELDS = ["ref", "title", "domain", "level", "priority", "risk",
                 "description", "objective", "plain_language", "best_practices", "expected_evidence", "discussion", "mappings"]


def _parse_mappings(raw: str):
    """Cell holds a JSON object {family_label: [refs]}. Tolerate blanks/garbage."""
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        val = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(val, dict):
        return None
    out = {}
    for k, v in val.items():
        if isinstance(v, list):
            refs = [str(x).strip() for x in v if str(x).strip()]
        else:
            refs = [s.strip() for s in str(v).split(",") if s.strip()]
        if refs:
            out[str(k).strip()] = refs
    return out or None


def _parse_table(filename: str, data: bytes):
    """Return (headers, rows) from a CSV or XLSX file."""
    name = (filename or "").lower()
    if name.endswith((".xlsx", ".xlsm")):
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        ws = wb.active
        rows = [[("" if c is None else str(c)) for c in r] for r in ws.iter_rows(values_only=True)]
    else:
        text = data.decode("utf-8-sig", errors="replace")
        rows = list(csv.reader(io.StringIO(text)))
    rows = [r for r in rows if any(str(c).strip() for c in r)]
    if not rows:
        raise HTTPException(status_code=400, detail="File has no rows")
    headers = [str(h).strip() for h in rows[0]]
    return headers, rows[1:]


def _coerce(enum_cls, value):
    if not value:
        return None
    v = str(value).strip().lower()
    aliases = {"med": "medium", "info": "informational", "informational": "informational"}
    v = aliases.get(v, v)
    try:
        return enum_cls(v)
    except ValueError:
        return None


@router.post("/import/preview")
async def import_preview(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin access required")
    await ensure_feature(db, current_user, "import")
    headers, rows = _parse_table(file.filename, await file.read())
    # naive auto-mapping by header name
    auto = {}
    for tf in TARGET_FIELDS:
        for h in headers:
            if h.lower().replace(" ", "_") == tf or tf in h.lower():
                auto[tf] = h
                break
    sample = [dict(zip(headers, r)) for r in rows[:5]]
    return {"columns": headers, "row_count": len(rows), "sample": sample, "auto_mapping": auto, "fields": TARGET_FIELDS}


@router.post("/import")
async def import_framework(
    name: str = Form(...),
    version: str = Form("1.0"),
    mapping: str = Form(...),  # JSON: {target_field: column_name}
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin access required")
    await ensure_feature(db, current_user, "import")
    try:
        colmap = json.loads(mapping)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid mapping JSON")
    if not colmap.get("ref") or not colmap.get("title"):
        raise HTTPException(status_code=400, detail="'ref' and 'title' columns are required")

    headers, rows = _parse_table(file.filename, await file.read())
    idx = {h: i for i, h in enumerate(headers)}

    def cell(row, field):
        col = colmap.get(field)
        if not col or col not in idx or idx[col] >= len(row):
            return ""
        return str(row[idx[col]]).strip()

    fw = Framework(
        name=name, version=version,
        description=f"Imported from {file.filename}",
        is_system=False, imported_by=current_user.id, levels=[],
    )
    db.add(fw)
    await db.flush()

    created, errors, levels = 0, [], []
    for i, row in enumerate(rows):
        ref, title = cell(row, "ref"), cell(row, "title")
        if not ref or not title:
            errors.append({"row": i + 2, "error": "missing ref or title"})
            continue
        lvl = cell(row, "level") or None
        if lvl and lvl not in levels:
            levels.append(lvl)
        db.add(Control(
            framework_id=fw.id, sort_order=i, ref=ref, title=title,
            domain=cell(row, "domain") or None, level=lvl,
            description=cell(row, "description") or None,
            objective=cell(row, "objective") or None,
            plain_language=cell(row, "plain_language") or None,
            best_practices=cell(row, "best_practices") or None,
            evidence_best_practices=cell(row, "expected_evidence") or None,
            discussion=cell(row, "discussion") or None,
            mappings=_parse_mappings(cell(row, "mappings")),
            priority=_coerce(ControlPriority, cell(row, "priority")),
            risk_rating=_coerce(ControlRisk, cell(row, "risk")),
        ))
        created += 1

    fw.levels = levels
    await db.commit()
    return {"framework_id": str(fw.id), "name": fw.name, "created": created,
            "errors": errors, "total_rows": len(rows)}
