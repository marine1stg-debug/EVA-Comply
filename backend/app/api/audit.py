"""
Audit log API - a chronological activity feed.

Sources merged here: (1) the real append-only `audit_logs` table (logins,
role/plan/archive changes, unlocks, resets, deletes), and (2) evidence activity
derived from evidence timestamps. Both are scoped to what the caller owns.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantType
from app.models.framework import Control
from app.models.evidence import OrgControl, EvidenceItem
from app.models.audit import AuditLog

router = APIRouter()

ACTION_ICON = {
    "auth.login": "🔑", "auth.account_locked": "🔒",
    "user.role_changed": "🛡", "user.deleted": "🗑", "user.unlocked": "🔓",
    "user.password_reset": "🔑", "user.mfa_reset": "🔑",
    "user.activated": "✅", "user.deactivated": "🚫",
    "tenant.suspended": "🚫", "tenant.reactivated": "✅",
    "tenant.archived": "🗄", "tenant.restored": "♻", "tenant.plan_changed": "🏷",
}
ACTION_TEXT = {
    "auth.login": "Signed in", "auth.account_locked": "Account locked (failed logins)",
    "user.role_changed": "Changed role", "user.deleted": "Deleted account",
    "user.unlocked": "Unlocked account", "user.password_reset": "Sent password reset",
    "user.mfa_reset": "Reset MFA", "user.activated": "Activated account",
    "user.deactivated": "Deactivated account", "tenant.suspended": "Suspended tenant",
    "tenant.reactivated": "Reactivated tenant", "tenant.archived": "Archived tenant",
    "tenant.restored": "Restored tenant", "tenant.plan_changed": "Changed plan",
}


async def _scope_org_ids(db: AsyncSession, user: User):
    if user.role in (UserRole.super_admin, UserRole.eva_auditor):
        rows = await db.execute(select(Tenant.id).where(Tenant.tenant_type == TenantType.single_client, Tenant.archived == False))  # noqa: E712
        return list(rows.scalars().all())
    if user.role in (UserRole.msp_admin, UserRole.msp_analyst):
        rows = await db.execute(select(Tenant.id).where(Tenant.parent_msp_id == user.tenant_id, Tenant.archived == False))  # noqa: E712
        return list(rows.scalars().all())
    return [user.tenant_id]


@router.get("/logs")
async def audit_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Every authenticated role may see the audit trail for what belongs to them:
    # EVA → all clients, MSP → its clients, client roles → their own tenant.
    org_ids = await _scope_org_ids(db, current_user)
    entries = []
    if org_ids:
        rows = await db.execute(
            select(EvidenceItem, Control.ref, User.display_name, Tenant.name)
            .join(OrgControl, OrgControl.id == EvidenceItem.org_control_id)
            .join(Control, Control.id == OrgControl.control_id)
            .join(User, User.id == EvidenceItem.collected_by)
            .join(Tenant, Tenant.id == EvidenceItem.org_id)
            .where(EvidenceItem.org_id.in_(org_ids))
            .order_by(EvidenceItem.created_at.desc())
            .limit(100)
        )
        icon = {"accepted": "✅", "rejected": "❌", "needs_more": "❌",
                "eva_pending": "📤", "msp_pending": "📤", "draft": "📝"}
        for ev, ref, who, tenant in rows.all():
            st = ev.status.value
            entries.append({
                "icon": icon.get(st, "📄"),
                "type": "evidence",
                "actor": who,
                "tenant": tenant,
                "text": f"Evidence “{ev.title}” for {ref} - {st.replace('_', ' ')}",
                "time": ev.created_at.strftime("%b %d, %Y %H:%M") if ev.created_at else "-",
                "ts": ev.created_at.isoformat() if ev.created_at else "",
            })
    # ── Real audit-log rows (logins, admin actions) ──
    aq = select(AuditLog)
    if current_user.role in (UserRole.super_admin, UserRole.eva_auditor):
        pass  # all rows
    elif current_user.role in (UserRole.msp_admin, UserRole.msp_analyst):
        ids = list(org_ids) + [current_user.tenant_id]
        aq = aq.where(or_(AuditLog.org_id.in_(ids), AuditLog.actor_id == current_user.id))
    else:
        aq = aq.where(AuditLog.org_id == current_user.tenant_id)
    arows = (await db.execute(aq.order_by(AuditLog.created_at.desc()).limit(200))).scalars().all()

    # Resolve tenant names for the rows we have.
    org_id_set = {r.org_id for r in arows if r.org_id}
    names = {}
    if org_id_set:
        nrows = await db.execute(select(Tenant.id, Tenant.name).where(Tenant.id.in_(org_id_set)))
        names = {tid: nm for tid, nm in nrows.all()}
    for r in arows:
        label = ACTION_TEXT.get(r.action, r.action)
        text = label + (f" - {r.target}" if r.target else "") + (f" ({r.detail})" if r.detail else "")
        entries.append({
            "icon": ACTION_ICON.get(r.action, "📋"),
            "type": "audit",
            "actor": r.actor_name or "-",
            "tenant": names.get(r.org_id, ""),
            "text": text,
            "time": r.created_at.strftime("%b %d, %Y %H:%M") if r.created_at else "-",
            "ts": r.created_at.isoformat() if r.created_at else "",
        })

    entries.sort(key=lambda e: e["ts"], reverse=True)
    return {"entries": entries, "total": len(entries)}
