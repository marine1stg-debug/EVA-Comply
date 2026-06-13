"""Append-only audit helper.

Call `record(...)` to stage an audit row; the caller's existing commit persists it.
Best-effort: a logging failure must never break the underlying action.
"""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def record(db: AsyncSession, actor, action: str, target: str = "",
                 detail: str = "", org_id: Optional[uuid.UUID] = None) -> None:
    try:
        role = ""
        if actor is not None and getattr(actor, "role", None) is not None:
            role = getattr(actor.role, "value", str(actor.role))
        db.add(AuditLog(
            actor_id=getattr(actor, "id", None),
            actor_name=(getattr(actor, "display_name", "") or "")[:200],
            actor_role=role,
            org_id=org_id if org_id is not None else getattr(actor, "tenant_id", None),
            action=action,
            target=(target or "")[:300],
            detail=(detail or "")[:500] or None,
        ))
    except Exception:
        pass  # never let auditing break the action
