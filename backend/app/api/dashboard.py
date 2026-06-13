"""
Dashboard summary endpoint — real, DB-backed aggregates scoped to the
current user's role:
  • client roles  → their own tenant
  • MSP roles      → all client tenants under their MSP
  • EVA roles      → all client tenants (portfolio-wide)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantType
from app.models.framework import Framework, Control, ControlRisk
from app.models.evidence import (
    OrgControl, OrgControlStatus, EvidenceItem, EvidenceStatus,
)

router = APIRouter()

DONE_STATUSES = {OrgControlStatus.implemented, OrgControlStatus.verified}
OPEN_STATUSES = {OrgControlStatus.not_started, OrgControlStatus.in_progress}
HIGH_RISK = {ControlRisk.critical, ControlRisk.high}
PENDING_EVIDENCE = {
    EvidenceStatus.client_submitted,
    EvidenceStatus.msp_pending,
    EvidenceStatus.eva_pending,
}

# Visual metadata for framework cards (icon/colour), keyed by framework name.
FW_VISUAL = {
    "CMMC 2.0":     {"icon": "🛡", "color": "#2563EB", "bg": "#EFF6FF"},
    "NIST CSF":     {"icon": "⎇",  "color": "#7C3AED", "bg": "#EDE9FE"},
    "ITSP.10.171 (CPCSC)": {"icon": "⚑",  "color": "#D97706", "bg": "#FFFBEB"},
}
STATUS_VISUAL = [
    (OrgControlStatus.verified,    "Verified",    "#059669"),
    (OrgControlStatus.implemented, "Implemented", "#16A34A"),
    (OrgControlStatus.in_progress, "In Progress", "#D97706"),
    (OrgControlStatus.not_started, "Not Started", "#EF4444"),
]


async def _scope_org_ids(db: AsyncSession, user: User) -> list:
    """Tenant IDs this user's dashboard aggregates over. If a reviewer has a
    client selected (X-Client-Id), scope to just that client; otherwise roll up
    across all clients in scope."""
    from app.core.client_context import resolve_org, CLIENT_ROLES, client_id_ctx
    if user.role in CLIENT_ROLES:
        return [user.tenant_id]
    if client_id_ctx.get():
        one = await resolve_org(db, user)
        return [one] if one else []
    if user.role in (UserRole.super_admin, UserRole.eva_auditor):
        rows = await db.execute(
            select(Tenant.id).where(Tenant.tenant_type == TenantType.single_client, Tenant.archived == False)  # noqa: E712
        )
        return list(rows.scalars().all())
    if user.role in (UserRole.msp_admin, UserRole.msp_analyst):
        rows = await db.execute(
            select(Tenant.id).where(Tenant.parent_msp_id == user.tenant_id, Tenant.archived == False)  # noqa: E712
        )
        return list(rows.scalars().all())
    return [user.tenant_id]


@router.get("/summary")
async def dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_ids = await _scope_org_ids(db, current_user)

    # ── Headline stats ────────────────────────────────────────────────
    total = done = gaps = evid_pending = 0
    status_counts = {s: 0 for s in OrgControlStatus}

    if org_ids:
        rows = await db.execute(
            select(OrgControl.status, Control.risk_rating)
            .join(Control, Control.id == OrgControl.control_id)
            .where(OrgControl.org_id.in_(org_ids))
        )
        for status, risk in rows.all():
            total += 1
            status_counts[status] = status_counts.get(status, 0) + 1
            if status in DONE_STATUSES:
                done += 1
            if risk in HIGH_RISK and status in OPEN_STATUSES:
                gaps += 1

        evid_pending = (await db.execute(
            select(func.count(EvidenceItem.id)).where(
                EvidenceItem.org_id.in_(org_ids),
                EvidenceItem.status.in_(PENDING_EVIDENCE),
            )
        )).scalar_one()

    pct = round(done / total * 100) if total else 0
    stats = {
        "pct": pct,
        "done": done,
        "total": total,
        "evid": evid_pending,
        "gaps": gaps,
    }

    # ── Framework cards ───────────────────────────────────────────────
    # Only show frameworks the in-scope client(s) actually have assigned — never
    # the whole library. No client in scope → no cards.
    fw_q = select(Framework).where(Framework.is_active == True)  # noqa: E712
    if org_ids:
        assigned = (
            select(Control.framework_id)
            .join(OrgControl, OrgControl.control_id == Control.id)
            .where(OrgControl.org_id.in_(org_ids))
            .distinct()
        )
        fw_q = fw_q.where(Framework.id.in_(assigned))
        fw_rows = (await db.execute(fw_q)).scalars().all()
    else:
        fw_rows = []

    frameworks = []
    for fw in fw_rows:
        ctrl_count = (await db.execute(
            select(func.count(Control.id)).where(Control.framework_id == fw.id)
        )).scalar_one()
        domain_count = (await db.execute(
            select(func.count(func.distinct(Control.domain))).where(
                Control.framework_id == fw.id, Control.domain.isnot(None)
            )
        )).scalar_one()

        fw_total = fw_done = 0
        if org_ids:
            frows = await db.execute(
                select(OrgControl.status)
                .join(Control, Control.id == OrgControl.control_id)
                .where(Control.framework_id == fw.id, OrgControl.org_id.in_(org_ids))
            )
            for (st,) in frows.all():
                fw_total += 1
                if st in DONE_STATUSES:
                    fw_done += 1
        fw_pct = round(fw_done / fw_total * 100) if fw_total else 0
        badge = ("Active" if fw_pct >= 60 else "In Progress" if fw_pct > 0 else "Just Started")
        vis = FW_VISUAL.get(fw.name, {"icon": "📋", "color": "#2563EB", "bg": "#EFF6FF"})
        frameworks.append({
            "key": fw.name.lower().replace(" ", "_"),
            "name": fw.name,
            "desc": fw.description or "",
            "tier": (fw.levels[0] if fw.levels else "—"),
            "controls": ctrl_count,
            "domains": domain_count,
            "pct": fw_pct,
            "badge": badge,
            **vis,
        })

    # ── Priority controls (high/med risk, still open) ─────────────────
    priority = []
    if org_ids:
        prows = await db.execute(
            select(Control.ref, Control.title, Control.domain, Control.risk_rating)
            .join(OrgControl, OrgControl.control_id == Control.id)
            .where(
                OrgControl.org_id.in_(org_ids),
                OrgControl.status.in_(OPEN_STATUSES),
            )
            .order_by(Control.sort_order)
            .limit(5)
        )
        for ref, title, domain, risk in prows.all():
            high = risk in HIGH_RISK
            priority.append({
                "ref": ref,
                "name": title,
                "domain": domain or "—",
                "risk": "b-red" if high else "b-amber",
                "riskLabel": "High" if high else "Med",
            })

    # ── Status breakdown ──────────────────────────────────────────────
    by_status = [
        {"label": label, "count": status_counts.get(st, 0), "col": col}
        for st, label, col in STATUS_VISUAL
    ]

    # ── Recent activity (derived from latest evidence) ────────────────
    activity = []
    if org_ids:
        Collector = User
        arows = await db.execute(
            select(EvidenceItem.title, EvidenceItem.status, EvidenceItem.created_at,
                   Control.ref, Collector.display_name)
            .join(OrgControl, OrgControl.id == EvidenceItem.org_control_id)
            .join(Control, Control.id == OrgControl.control_id)
            .join(Collector, Collector.id == EvidenceItem.collected_by)
            .where(EvidenceItem.org_id.in_(org_ids))
            .order_by(EvidenceItem.created_at.desc())
            .limit(5)
        )
        now = datetime.now(timezone.utc)
        dot_for = {
            EvidenceStatus.accepted: "#16A34A",
            EvidenceStatus.eva_pending: "#2563EB",
            EvidenceStatus.client_submitted: "#D97706",
            EvidenceStatus.rejected: "#DC2626",
            EvidenceStatus.needs_more: "#DC2626",
        }
        for title, status, created, ref, who in arows.all():
            delta = now - (created or now)
            hrs = int(delta.total_seconds() // 3600)
            when = "just now" if hrs < 1 else f"{hrs}h ago" if hrs < 24 else f"{hrs // 24}d ago"
            activity.append({
                "dot": dot_for.get(status, "#7C3AED"),
                # Structured (not HTML) so the client renders user-controlled
                # values as text — avoids stored XSS via evidence title / name.
                "who": who,
                "title": title,
                "ref": ref,
                "status": status.value.replace('_', ' '),
                "time": when,
            })

    return {
        "user": {"name": current_user.display_name, "role": current_user.role.value},
        "stats": stats,
        "frameworks": frameworks,
        "priorityControls": priority,
        "byStatus": by_status,
        "activity": activity,
    }
