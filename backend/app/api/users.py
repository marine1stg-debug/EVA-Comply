"""
Users & roles API - list users in scope + activate/deactivate.
Scope: super_admin → all; MSP admin → own MSP + client tenants;
client_admin → own tenant only.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.core.security import hash_password, random_password, create_invite_token
from app.core.email import send_email
from app.core.audit import record as audit_record
from app.core.entitlements import get_entitlements, tenant_usage
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantType

FRONTEND_URL = settings.FRONTEND_URL
INVITABLE_ROLES = {
    UserRole.super_admin: ["super_admin", "eva_auditor"],
    UserRole.msp_admin: ["msp_admin", "msp_analyst"],
    UserRole.client_admin: ["client_admin", "contributor", "viewer"],
}

# A role must also fit the target tenant's tier: EVA roles belong on the EVA
# internal org, MSP roles on an MSP org, client roles on a client org. This
# stops e.g. an MSP admin from granting an MSP role to a client-org user.
ROLE_TENANT_FIT = {
    UserRole.super_admin: {TenantType.eva_internal},
    UserRole.eva_auditor: {TenantType.eva_internal},
    UserRole.msp_admin: {TenantType.msp},
    UserRole.msp_analyst: {TenantType.msp},
    UserRole.client_admin: {TenantType.single_client},
    UserRole.contributor: {TenantType.single_client},
    UserRole.viewer: {TenantType.single_client},
}

router = APIRouter()

ROLE_LABEL = {
    "super_admin": "Super Admin", "eva_auditor": "EVA Auditor", "msp_admin": "MSP Admin",
    "msp_analyst": "MSP Analyst", "client_admin": "Client Admin",
    "contributor": "Contributor", "viewer": "Viewer",
}
ROLE_COLOR = {
    "super_admin": "#7C3AED", "eva_auditor": "#2563EB", "msp_admin": "#0D9488",
    "msp_analyst": "#0891B2", "client_admin": "#D97706", "contributor": "#16A34A", "viewer": "#64748B",
}
ADMIN_ROLES = {UserRole.super_admin, UserRole.msp_admin, UserRole.client_admin}


async def _scope_tenant_ids(db: AsyncSession, user: User):
    if user.role == UserRole.super_admin:
        return None  # all
    if user.role == UserRole.msp_admin:
        rows = await db.execute(
            select(Tenant.id).where(
                (Tenant.id == user.tenant_id) | (Tenant.parent_msp_id == user.tenant_id)
            )
        )
        return list(rows.scalars().all())
    return [user.tenant_id]


@router.get("/")
async def list_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin access required")

    scope = await _scope_tenant_ids(db, current_user)
    q = select(User, Tenant.name).join(Tenant, Tenant.id == User.tenant_id).where(Tenant.archived == False)  # noqa: E712
    if scope is not None:
        q = q.where(User.tenant_id.in_(scope))
    rows = await db.execute(q.order_by(Tenant.name, User.display_name))

    now = datetime.now(timezone.utc)
    out = []
    for u, tenant_name in rows.all():
        out.append({
            "id": str(u.id),
            "name": u.display_name,
            "email": u.email,
            "role": u.role.value,
            "roleLabel": ROLE_LABEL.get(u.role.value, u.role.value),
            "roleColor": ROLE_COLOR.get(u.role.value, "#64748B"),
            "tenant": tenant_name,
            "tenant_id": str(u.tenant_id),
            "mfa_enabled": u.mfa_enabled,
            "is_active": u.is_active,
            "can_coach": u.can_coach,
            "is_developer": u.is_developer,
            "locked": bool(u.locked_until and u.locked_until > now),
            "last_login": u.last_login_at.strftime("%b %d, %Y") if u.last_login_at else "Never",
            "is_self": u.id == current_user.id,
        })
    return {"users": out, "total": len(out), "is_super": current_user.role == UserRole.super_admin}


class InviteBody(BaseModel):
    email: str
    display_name: str
    role: str
    is_developer: bool = False


@router.get("/invitable-roles")
async def invitable_roles(current_user: User = Depends(get_current_user)):
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin access required")
    return {"roles": INVITABLE_ROLES.get(current_user.role, [])}


@router.post("/invite")
async def invite_user(
    body: InviteBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin access required")
    allowed = INVITABLE_ROLES.get(current_user.role, [])
    if body.role not in allowed:
        raise HTTPException(status_code=400, detail="You can't assign that role")

    exists = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="That email is already in use")

    # Seat limit from the tenant's plan.
    tenant = (await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))).scalar_one()
    ent = await get_entitlements(db, tenant)
    usage = await tenant_usage(db, tenant)
    if ent["max_users"] and usage["users"] >= ent["max_users"]:
        raise HTTPException(status_code=403, detail=f"Your plan's seat limit ({ent['max_users']}) is reached. Upgrade to add more.")

    u = User(
        tenant_id=current_user.tenant_id, email=body.email,
        password_hash=hash_password(random_password()),
        display_name=body.display_name, role=UserRole(body.role), is_active=False,
        # Dev/tester tag only applies to Super Admin accounts (it grants no extra
        # rights - it just labels the account). Ignored for any other role.
        is_developer=bool(body.is_developer) and body.role == "super_admin",
    )
    db.add(u)
    await db.flush()
    token = create_invite_token(u.id, u.email)
    await db.commit()
    dev = settings.ENVIRONMENT == "development" or settings.EMAIL_BACKEND == "console"
    print(f"[invite] {u.email} -> /accept-invite?token={token}")
    return {"id": str(u.id), "email": u.email,
            "invite_link": f"{FRONTEND_URL}/accept-invite?token={token}" if dev else None}


class ActiveBody(BaseModel):
    active: bool


@router.patch("/{user_id}/active")
async def set_user_active(
    user_id: str,
    body: ActiveBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")
    if uid == current_user.id:
        raise HTTPException(status_code=400, detail="You can't change your own active status")

    u = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    scope = await _scope_tenant_ids(db, current_user)
    if scope is not None and u.tenant_id not in scope:
        raise HTTPException(status_code=403, detail="Out of scope")

    u.is_active = body.active
    await audit_record(db, current_user, "user.activated" if body.active else "user.deactivated",
                       target=u.email, org_id=u.tenant_id)
    await db.commit()
    return {"id": str(u.id), "is_active": u.is_active}


class DevBody(BaseModel):
    is_developer: bool


@router.patch("/{user_id}/developer")
async def set_user_developer(
    user_id: str,
    body: DevBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Tag/untag a Super Admin as a dev/tester (label only; grants no extra rights)."""
    if current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin only")
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")
    u = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if u.role != UserRole.super_admin:
        raise HTTPException(status_code=400, detail="The developer tag applies only to Super Admin accounts")
    u.is_developer = bool(body.is_developer)
    await db.commit()
    return {"id": str(u.id), "is_developer": u.is_developer}


async def _target_in_scope(db: AsyncSession, current_user: User, user_id: str, allow_self: bool = True) -> User:
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")
    if not allow_self and uid == current_user.id:
        raise HTTPException(status_code=400, detail="You can't do that to your own account")
    u = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    scope = await _scope_tenant_ids(db, current_user)
    if scope is not None and u.tenant_id not in scope:
        raise HTTPException(status_code=403, detail="Out of scope")
    return u


class EditBody(BaseModel):
    display_name: str | None = None
    role: str | None = None
    can_coach: bool | None = None


@router.patch("/{user_id}")
async def edit_user(user_id: str, body: EditBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    u = await _target_in_scope(db, current_user, user_id)
    if body.display_name is not None and body.display_name.strip():
        u.display_name = body.display_name.strip()[:200]
    if body.role is not None and body.role != u.role.value:
        if u.id == current_user.id:
            raise HTTPException(status_code=400, detail="You can't change your own role")
        allowed = INVITABLE_ROLES.get(current_user.role, [])
        if body.role not in allowed:
            raise HTTPException(status_code=400, detail="You can't assign that role")
        new_role = UserRole(body.role)
        # The new role must also be valid for the target user's organization tier.
        target_tenant = (await db.execute(select(Tenant).where(Tenant.id == u.tenant_id))).scalar_one_or_none()
        if target_tenant is not None and target_tenant.tenant_type not in ROLE_TENANT_FIT.get(new_role, set()):
            raise HTTPException(status_code=400, detail="That role isn't valid for this user's organization")
        await audit_record(db, current_user, "user.role_changed", target=u.email,
                           detail=f"{u.role.value} → {body.role}", org_id=u.tenant_id)
        u.role = new_role
    if body.can_coach is not None:
        u.can_coach = body.can_coach
    await db.commit()
    return {"id": str(u.id), "name": u.display_name, "role": u.role.value, "can_coach": u.can_coach}


@router.post("/{user_id}/unlock")
async def unlock_user(user_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    u = await _target_in_scope(db, current_user, user_id)
    u.failed_attempts = 0
    u.locked_until = None
    await audit_record(db, current_user, "user.unlocked", target=u.email, org_id=u.tenant_id)
    await db.commit()
    return {"id": str(u.id), "locked": False}


@router.post("/{user_id}/reset-mfa")
async def reset_mfa(user_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    u = await _target_in_scope(db, current_user, user_id)
    u.mfa_enabled = False
    u.mfa_secret = None
    await audit_record(db, current_user, "user.mfa_reset", target=u.email, org_id=u.tenant_id)
    await db.commit()
    return {"id": str(u.id), "mfa_enabled": False}


@router.post("/{user_id}/reset-password")
async def reset_password(user_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Issue a password-reset link (reuses the accept-invite flow). The user sets
    a fresh password and any lockout is cleared on next successful sign-in."""
    u = await _target_in_scope(db, current_user, user_id)
    u.failed_attempts = 0
    u.locked_until = None
    await audit_record(db, current_user, "user.password_reset", target=u.email, org_id=u.tenant_id)
    await db.commit()
    token = create_invite_token(u.id, u.email)
    link = f"{FRONTEND_URL}/accept-invite?token={token}"
    send_email(u.email, "Reset your EVA password",
               f"A password reset was requested for your account. Set a new password here:\n{link}")
    print(f"[reset] {u.email} -> /accept-invite?token={token}")
    dev = settings.ENVIRONMENT == "development" or settings.EMAIL_BACKEND == "console"
    return {"id": str(u.id), "reset_link": link if dev else None}


@router.delete("/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Hard delete - Super Admin only. Prefer deactivating instead; this is for
    GDPR-style erasure. Blocked if the account is still referenced by records."""
    if current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Only the Super Admin can delete accounts")
    u = await _target_in_scope(db, current_user, user_id, allow_self=False)
    try:
        await audit_record(db, current_user, "user.deleted", target=u.email, org_id=u.tenant_id)
        await db.delete(u)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=409,
                            detail="This account is referenced by existing records. Deactivate it instead.")
    return {"deleted": user_id}
