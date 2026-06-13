"""Per-request 'which client am I viewing' context.

Reviewer roles (EVA super admin / auditor, MSP admin / analyst) work across many
client orgs. The frontend sends the selected client via the `X-Client-Id` header;
middleware stashes it in a ContextVar, and `resolve_org()` turns it into a scoped
org id (validating that the reviewer is allowed to see that client). Client-role
users always resolve to their own tenant and ignore the header.
"""
import uuid
from contextvars import ContextVar
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantType

# Set by middleware from the X-Client-Id request header (may be None).
client_id_ctx: ContextVar[Optional[str]] = ContextVar("client_id", default=None)

CLIENT_ROLES = {UserRole.client_admin, UserRole.contributor, UserRole.viewer}
EVA_ROLES = {UserRole.super_admin, UserRole.eva_auditor}
MSP_ROLES = {UserRole.msp_admin, UserRole.msp_analyst}


async def _in_scope(db: AsyncSession, user: User, tid: uuid.UUID) -> bool:
    t = (await db.execute(select(Tenant).where(Tenant.id == tid))).scalar_one_or_none()
    if not t or t.archived:
        return False
    if user.role in EVA_ROLES:
        return t.tenant_type == TenantType.single_client
    if user.role in MSP_ROLES:
        return t.parent_msp_id == user.tenant_id
    return False


async def resolve_org(db: AsyncSession, user: User) -> Optional[uuid.UUID]:
    """The org a request should act on. Client users → own tenant; reviewers →
    the selected client from X-Client-Id (if in scope), else None (no client
    chosen → the caller shows an empty 'pick a client' state)."""
    if user.role in CLIENT_ROLES:
        return user.tenant_id
    raw = client_id_ctx.get()
    if raw:
        try:
            tid = uuid.UUID(raw)
        except (ValueError, TypeError):
            return None
        if await _in_scope(db, user, tid):
            return tid
    return None
