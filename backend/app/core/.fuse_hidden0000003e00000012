# -*- coding: utf-8 -*-
"""Selective backup / restore engine.

Serializes chosen data CATEGORIES (optionally narrowed to specific client
tenants) into a JSON bundle, and restores a bundle by UPSERTing rows (merge —
never deletes). Generic: works off SQLAlchemy column introspection so it covers
every model without per-field code.

Bundle shape:
    {
      "version": 1,
      "created_at": "<iso>",
      "categories": ["frameworks", ...],
      "client_ids": ["<uuid>", ...],          # [] = all / not client-scoped
      "tables": { "<tablename>": [ {col: val, ...}, ... ] }
    }
"""
import uuid
import hmac
import json
import hashlib
import datetime as dt
from typing import Optional

from sqlalchemy import select, inspect as sa_inspect
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import Enum as SAEnum, DateTime, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.framework import Framework, Control
from app.models.billing import BillingPlan, Invoice
from app.models.platform import PlatformSettings
from app.models.promo import PromoCode
from app.models.marketplace import MarketplaceSkill, ServiceProvider
from app.models.tenant import Tenant
from app.models.user import User
from app.models.support import SupportCase, SupportComment, SupportSettings
from app.models.evidence import (
    OrgControl, ExpectedEvidence, EvidenceItem, ControlEvent,
)
from app.models.recommendation import Recommendation
from app.models.maturity import MaturityAssessment, MaturitySnapshot
from app.models.self_assessment import SelfAssessment
from app.models.audit import AuditLog
from app.models.policy import Policy
from app.core.config import settings

BUNDLE_VERSION = 1

# category key -> (FR label, client_scoped?, [(Model, client_field|None), ...])
# Model list is in FK-safe order (parents first).
CATEGORIES: dict = {
    "frameworks": ("Frameworks et contrôles", False, [(Framework, None), (Control, None)]),
    "plans":      ("Forfaits, paramètres et promos", False,
                   [(BillingPlan, None), (PlatformSettings, None), (PromoCode, None)]),
    "providers":  ("Fournisseurs et compétences", False,
                   [(MarketplaceSkill, None), (ServiceProvider, None)]),
    "tenants":    ("Organisations et utilisateurs", True,
                   [(Tenant, "id"), (User, "tenant_id")]),
    "compliance": ("Conformité (contrôles, preuves, maturité)", True,
                   [(OrgControl, "org_id"), (ExpectedEvidence, "org_id"),
                    (EvidenceItem, "org_id"), (ControlEvent, "org_id"),
                    (Recommendation, "org_id"), (MaturityAssessment, "org_id"),
                    (MaturitySnapshot, "org_id"), (SelfAssessment, "org_id")]),
    "support":    ("Cas de support", True,
                   [(SupportCase, "org_id"), (SupportComment, None), (SupportSettings, None)]),
    "billing":    ("Factures", True, [(Invoice, "tenant_id")]),
    "audit":      ("Journal d'audit", True, [(AuditLog, "org_id")]),
    "policies":   ("Bibliothèque de politiques", False, [(Policy, None)]),
}

# Global restore order across every model (parents before children).
TABLE_ORDER = [
    Framework, Control, BillingPlan, PlatformSettings, PromoCode,
    MarketplaceSkill, ServiceProvider, Tenant, User,
    OrgControl, ExpectedEvidence, EvidenceItem, ControlEvent, Recommendation,
    MaturityAssessment, MaturitySnapshot, SelfAssessment,
    SupportCase, SupportComment, SupportSettings, Invoice, AuditLog, Policy,
]
_BY_TABLE = {m.__tablename__: m for m in TABLE_ORDER}


# ── serialization ────────────────────────────────────────────────────────────
def _to_jsonable(v):
    if v is None:
        return None
    if isinstance(v, uuid.UUID):
        return str(v)
    if isinstance(v, (dt.datetime, dt.date)):
        return v.isoformat()
    if hasattr(v, "value"):           # enum member
        return v.value
    return v                           # str / int / float / bool / dict / list


# SECURITY: credential material must never leave the database via backups,
# and must never be writable via a restored bundle.
SENSITIVE_COLUMNS = {"password_hash", "mfa_secret"}


def serialize_row(obj) -> dict:
    cols = sa_inspect(obj.__class__).columns
    return {
        c.key: _to_jsonable(getattr(obj, c.key))
        for c in cols
        if c.key not in SENSITIVE_COLUMNS
    }


def _coerce(col, value):
    if value is None:
        return None
    t = col.type
    try:
        if isinstance(t, PG_UUID):
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        if isinstance(t, SAEnum):
            ec = getattr(t, "enum_class", None)
            return ec(value) if ec is not None else value
        if isinstance(t, DateTime):
            return dt.datetime.fromisoformat(value) if isinstance(value, str) else value
        if isinstance(t, Date):
            return dt.date.fromisoformat(value) if isinstance(value, str) else value
    except (ValueError, TypeError):
        return value
    return value


def _pk_col(model):
    pk = list(sa_inspect(model).primary_key)
    return pk[0] if pk else None


# ── integrity signing ─────────────────────────────────────────────────────────
# An HMAC over the bundle content lets restore distinguish a file produced by
# THIS system (trusted — safe to restore in full) from a hand-crafted one (which
# could otherwise flip a user to super_admin or rewrite another tenant's rows).
def _bundle_digest(bundle: dict) -> str:
    payload = {k: bundle.get(k) for k in ("version", "created_at", "categories", "client_ids", "tables")}
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), canonical, hashlib.sha256).hexdigest()


def sign_bundle(bundle: dict) -> dict:
    bundle["signature"] = _bundle_digest(bundle)
    return bundle


def verify_bundle(bundle: dict) -> bool:
    sig = bundle.get("signature")
    if not sig or not isinstance(sig, str):
        return False
    return hmac.compare_digest(sig, _bundle_digest(bundle))


# ── export ───────────────────────────────────────────────────────────────────
async def export_bundle(db: AsyncSession, categories: list, client_ids: list) -> dict:
    cid = [uuid.UUID(str(c)) for c in (client_ids or [])]
    tables: dict = {}
    for cat in categories:
        spec = CATEGORIES.get(cat)
        if not spec:
            continue
        _label, scoped, models = spec
        for model, field in models:
            q = select(model)
            if scoped and cid and field:
                q = q.where(getattr(model, field).in_(cid))
            rows = (await db.execute(q)).scalars().all()
            tables.setdefault(model.__tablename__, [])
            tables[model.__tablename__].extend(serialize_row(r) for r in rows)
    return sign_bundle({
        "version": BUNDLE_VERSION,
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
        "categories": list(categories),
        "client_ids": [str(c) for c in cid],
        "tables": tables,
    })


# ── import (merge / upsert) ──────────────────────────────────────────────────
async def import_bundle(db: AsyncSession, bundle: dict, only_categories: Optional[list] = None) -> dict:
    """Upsert every row in the bundle by primary key. Never deletes. Returns
    per-table {inserted, updated} counts. Caller commits."""
    tables = bundle.get("tables", {})
    wanted_tables = None
    if only_categories:
        wanted_tables = set()
        for cat in only_categories:
            for model, _f in CATEGORIES.get(cat, ("", False, []))[2]:
                wanted_tables.add(model.__tablename__)

    counts: dict = {}
    for model in TABLE_ORDER:
        tname = model.__tablename__
        if tname not in tables:
            continue
        if wanted_tables is not None and tname not in wanted_tables:
            continue
        pk = _pk_col(model)
        if pk is None:
            continue
        cols = {c.key: c for c in sa_inspect(model).columns}
        ins = upd = 0
        for raw in tables[tname]:
            # SECURITY: never accept credential columns from an uploaded bundle
            # (blocks password/MFA injection via restore).
            data = {
                k: _coerce(cols[k], v)
                for k, v in raw.items()
                if k in cols and k not in SENSITIVE_COLUMNS
            }
            pk_val = data.get(pk.key)
            existing = await db.get(model, pk_val) if pk_val is not None else None
            if existing is None:
                if tname == "users" and not data.get("password_hash"):
                    # Restored users get an unusable hash — they must use the
                    # password-reset flow before they can log in.
                    data["password_hash"] = "!locked!"
                db.add(model(**data))
                ins += 1
            else:
                for k, v in data.items():
                    if k != pk.key:
                        setattr(existing, k, v)
                upd += 1
        await db.flush()
        counts[tname] = {"inserted": ins, "updated": upd}
    return counts


def bundle_summary(bundle: dict) -> dict:
    """Lightweight description of a bundle for the UI."""
    tables = bundle.get("tables", {})
    return {
        "version": bundle.get("version"),
        "created_at": bundle.get("created_at"),
        "categories": bundle.get("categories", []),
        "client_ids": bundle.get("client_ids", []),
        "rows": {t: len(rows) for t, rows in tables.items()},
        "total_rows": sum(len(r) for r in tables.values()),
    }
