from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token, generate_totp_secret,
    verify_totp, get_totp_uri, create_verification_token, gen_verification_code,
    create_unlock_token, make_captcha, verify_captcha,
)
from app.core.email import send_email
from app.core.audit import record as audit_record
from app.core.secrets_crypto import encrypt, decrypt
from app.core import ratelimit
from app.core.provisioning import assign_frameworks
from app.core.entitlements import get_entitlements, tenant_usage, filter_frameworks, trial_state
from app.core.platform import get_settings
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantType, SubscriptionStatus
from app.models.framework import Framework, Control
from app.models.billing import BillingPlan

router = APIRouter()
security = HTTPBearer()

MFA_REQUIRED_ROLES = {UserRole.super_admin, UserRole.eva_auditor, UserRole.msp_admin}

MIN_PASSWORD_LENGTH = 12


def _validate_password(pw: str) -> None:
    if len(pw or "") < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters",
        )


# ── Schemas ───────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class MFAVerifyRequest(BaseModel):
    code: str
    temp_token: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str
    org_name: str
    tenant_type: str = "single_client"
    plan: str = "professional"
    framework_ids: list[str] = []
    verification_token: Optional[str] = None
    code: Optional[str] = None
    promo_code: Optional[str] = None
    captcha_token: Optional[str] = None
    captcha_answer: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    requires_mfa: bool = False
    temp_token: Optional[str] = None
    user: Optional[dict] = None

class RefreshRequest(BaseModel):
    refresh_token: str

class MFASetupResponse(BaseModel):
    secret: str
    qr_uri: str


# ── Helper ────────────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id or payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate token")

    # SECURITY: the pre-MFA temp token carries mfa_pending=True and must
    # never be accepted as a session token — only /auth/mfa/verify may use it.
    if payload.get("mfa_pending"):
        raise HTTPException(status_code=401, detail="MFA verification required")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Check tenant suspension
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    if tenant and tenant.subscription_status.value == "suspended":
        raise HTTPException(status_code=402, detail="Account suspended — please update payment")

    return user


# ── Session helpers ───────────────────────────────────
def _user_dict(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role.value,
        "tenant_id": str(user.tenant_id),
    }

def _session_tokens(user: User) -> TokenResponse:
    """Issue a short-lived access token + a long-lived refresh token."""
    return TokenResponse(
        access_token=create_access_token({"sub": str(user.id)}),
        refresh_token=create_refresh_token({"sub": str(user.id)}),
        user=_user_dict(user),
    )


# ── Routes ────────────────────────────────────────────
LOCKOUT_THRESHOLD = 3
LOCKOUT_MINUTES = 15


async def _send_unlock_email(user: User):
    token = create_unlock_token(user.id, user.email)
    link = f"{settings.FRONTEND_URL}/unlock?token={token}"
    send_email(user.email, "Your EVA account is locked",
               f"Your account was locked after too many sign-in attempts.\n"
               f"It will unlock automatically in {LOCKOUT_MINUTES} minutes, or unlock it now:\n{link}")
    if settings.ENVIRONMENT == "development":
        print(f"[unlock] {user.email} -> /unlock?token={token}")


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, http_request: Request, db: AsyncSession = Depends(get_db)):
    ratelimit.enforce(http_request, "login", limit=10, window_seconds=300)
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    # Currently locked? Bounce before checking the password.
    if user and user.locked_until and user.locked_until > now:
        mins = max(1, int((user.locked_until - now).total_seconds() // 60) + 1)
        raise HTTPException(status_code=423,
                            detail=f"Account locked. Try again in {mins} min or use the unlock link emailed to you.")

    if not user or not verify_password(request.password, user.password_hash):
        if user:
            # A lapsed lock that hasn't been cleared yet → reset the counter first.
            if user.locked_until and user.locked_until <= now:
                user.failed_attempts = 0
                user.locked_until = None
            user.failed_attempts = (user.failed_attempts or 0) + 1
            if user.failed_attempts >= LOCKOUT_THRESHOLD:
                user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
                user.failed_attempts = 0
                await audit_record(db, user, "auth.account_locked", target=user.email)
                await db.commit()
                await _send_unlock_email(user)
            else:
                await db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account deactivated")

    # MSP/Reseller accounts can't sign in until EVA authorizes them.
    tenant = (await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))).scalar_one_or_none()
    if tenant and tenant.activation_pending:
        raise HTTPException(status_code=403, detail="Your account is awaiting authorization by EVA. You'll be notified once it's approved.")

    # Successful auth → clear any lockout state and update last login.
    user.failed_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    await audit_record(db, user, "auth.login", target=user.email)
    await db.commit()

    # MFA check
    if user.role in MFA_REQUIRED_ROLES and user.mfa_enabled:
        temp_token = create_access_token(
            {"sub": str(user.id), "type": "access", "mfa_pending": True},
        )
        return TokenResponse(requires_mfa=True, temp_token=temp_token)

    return _session_tokens(user)


@router.post("/mfa/verify", response_model=TokenResponse)
async def verify_mfa(request: MFAVerifyRequest, http_request: Request, db: AsyncSession = Depends(get_db)):
    ratelimit.enforce(http_request, "mfa_verify", limit=10, window_seconds=300)
    try:
        payload = decode_token(request.temp_token)
        if not payload.get("mfa_pending"):
            raise HTTPException(status_code=400, detail="Invalid token")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_totp(decrypt(user.mfa_secret), request.code):
        raise HTTPException(status_code=401, detail="Invalid MFA code")

    return _session_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_session(request: RefreshRequest, http_request: Request, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a fresh access + refresh token pair
    (rotation). Lets the SPA renew silently without re-login."""
    ratelimit.enforce(http_request, "refresh", limit=60, window_seconds=300)
    try:
        payload = decode_token(request.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = (await db.execute(select(User).where(User.id == uuid.UUID(user_id)))).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return _session_tokens(user)


class EmailBody(BaseModel):
    email: EmailStr


class TokenBody(BaseModel):
    token: str


@router.post("/request-unlock")
async def request_unlock(body: EmailBody, http_request: Request, db: AsyncSession = Depends(get_db)):
    """Email a one-time unlock link. Always returns success to avoid leaking
    which addresses have accounts."""
    ratelimit.enforce(http_request, "request_unlock", limit=5, window_seconds=900)
    user = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if user:
        await _send_unlock_email(user)
    return {"ok": True}


@router.post("/unlock")
async def unlock_account(body: TokenBody, db: AsyncSession = Depends(get_db)):
    try:
        p = decode_token(body.token)
    except Exception:
        raise HTTPException(status_code=400, detail="This unlock link is invalid or has expired")
    if p.get("type") != "unlock":
        raise HTTPException(status_code=400, detail="Invalid unlock link")
    user = (await db.execute(select(User).where(User.id == uuid.UUID(p["sub"])))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Account not found")
    user.failed_attempts = 0
    user.locked_until = None
    await db.commit()
    return {"ok": True}


@router.get("/signup-options")
async def signup_options(db: AsyncSession = Depends(get_db)):
    """Public — active plans (from the configurable catalog) and frameworks."""
    # All active frameworks — both built-in and imported (custom) — so plans and
    # signup can include catalogs you've imported, not just the seeded ones.
    fw_rows = (await db.execute(
        select(Framework).where(Framework.is_active == True)  # noqa: E712
    )).scalars().all()
    frameworks = []
    for fw in fw_rows:
        n = (await db.execute(
            select(func.count(Control.id)).where(Control.framework_id == fw.id)
        )).scalar_one()
        frameworks.append({"id": str(fw.id), "name": fw.name, "desc": fw.description or "",
                           "version": fw.version, "controls": n})

    plan_rows = (await db.execute(
        select(BillingPlan).where(BillingPlan.is_active == True)  # noqa: E712
    )).scalars().all()
    plans = [{"key": str(p.id), "name": p.name, "price": p.price_monthly, "tenant_type": p.tier.value,
              "frameworks": (p.inclusions or {}).get("frameworks", "all")}
             for p in plan_rows]
    ps = await get_settings(db)
    return {"plans": plans, "frameworks": frameworks, "stripe_enabled": bool(settings.STRIPE_SECRET_KEY),
            "billing_mode": ps.billing_mode.value, "trial_days": ps.trial_days}


class VerifyRequestBody(BaseModel):
    email: EmailStr


@router.get("/captcha")
async def get_captcha():
    """Public — issue a fresh arithmetic CAPTCHA challenge for signup."""
    question, token = make_captcha()
    return {"question": question, "captcha_token": token}


@router.post("/request-verification")
async def request_verification(body: VerifyRequestBody, http_request: Request, db: AsyncSession = Depends(get_db)):
    """Public — issue an email verification code. In dev (console email) the
    code is returned so the flow is testable without an email service."""
    ratelimit.enforce(http_request, "request_verification", limit=5, window_seconds=900)
    exists = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="That email already has an account — please sign in")
    code = gen_verification_code()
    token = create_verification_token(body.email, code)
    dev = settings.EMAIL_BACKEND == "console" or settings.ENVIRONMENT == "development"
    # Only echo the code to logs in development; in production it is emailed.
    if dev:
        print(f"[verification] {body.email} -> {code}")
    return {"verification_token": token, "dev_code": code if dev else None}


@router.post("/register")
async def register(request: RegisterRequest, http_request: Request, db: AsyncSession = Depends(get_db)):
    ratelimit.enforce(http_request, "register", limit=5, window_seconds=3600)
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    _validate_password(request.password)

    # Require a valid CAPTCHA answer (challenge issued by /captcha).
    if not request.captcha_token or not verify_captcha(request.captcha_token, request.captcha_answer or ""):
        raise HTTPException(status_code=400, detail="Incorrect or expired CAPTCHA — please try again")

    # Require a valid email-verification code (token issued by /request-verification).
    if not request.verification_token or not request.code:
        raise HTTPException(status_code=400, detail="Email verification required")
    try:
        vp = decode_token(request.verification_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Verification expired — request a new code")
    if vp.get("type") != "verify" or vp.get("email") != request.email or vp.get("code") != request.code:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    # Resolve the chosen plan from the configurable catalog (request.plan = plan id).
    plan = None
    try:
        plan = (await db.execute(
            select(BillingPlan).where(BillingPlan.id == uuid.UUID(request.plan))
        )).scalar_one_or_none()
    except (ValueError, TypeError):
        plan = None
    if not plan:
        plan = (await db.execute(
            select(BillingPlan).where(BillingPlan.is_active == True).limit(1)  # noqa: E712
        )).scalar_one_or_none()

    # The plan's tier decides whether this is an MSP master account or a client.
    is_msp = bool(plan and plan.tier.value == "msp")
    tenant_type = TenantType.msp if is_msp else TenantType.single_client
    admin_role = UserRole.msp_admin if is_msp else UserRole.client_admin

    # Resolve a signup promo code → per-tenant billing mode. No/invalid code
    # leaves billing_mode NULL, so the platform default applies.
    from app.core.promo import resolve_promo
    promo = await resolve_promo(db, request.promo_code)

    tenant = Tenant(
        name=request.org_name,
        tenant_type=tenant_type,
        # New accounts begin in trial; the (per-tenant or platform) billing mode governs access.
        subscription_status=SubscriptionStatus.trialing,
        plan_id=plan.id if plan else None,
        plan_name=plan.name if plan else None,
        monthly_price=plan.price_monthly if plan else None,
        msp_review_enabled=is_msp,
        billing_mode=promo.billing_mode.value if promo else None,
        # MSP/Reseller self-registrations must be authorized by a Super Admin.
        activation_pending=is_msp,
    )
    db.add(tenant)
    await db.flush()
    if promo:
        promo.uses = (promo.uses or 0) + 1

    user = User(
        tenant_id=tenant.id,
        email=request.email,
        password_hash=hash_password(request.password),
        display_name=request.display_name,
        role=admin_role,
    )
    db.add(user)
    await db.flush()

    # MSP master tenants don't track their own controls — frameworks are
    # assigned to each client. Only provision frameworks for single clients.
    assigned = 0
    if not is_msp:
        ent = await get_entitlements(db, tenant)
        allowed = filter_frameworks(ent, request.framework_ids)
        assigned = await assign_frameworks(db, tenant.id, allowed)
    await db.commit()

    # MSP/Reseller accounts can't sign in until a Super Admin authorizes them.
    if is_msp:
        recipients = (await db.execute(select(User.email).where(User.role == UserRole.super_admin))).scalars().all()
        send_email(list(recipients), "New MSP/Reseller awaiting authorization",
                   f"{request.org_name} signed up as an MSP/Reseller and is awaiting authorization in Tenant Management.")
        return {
            "message": "Account created — awaiting EVA authorization",
            "pending": True,
            "tenant_id": str(tenant.id),
        }

    # Auto-login the new admin (clients only)
    access_token = create_access_token({"sub": str(user.id)})
    return {
        "message": "Account created",
        "tenant_id": str(tenant.id),
        "controls_assigned": assigned,
        "access_token": access_token,
        "user": {
            "id": str(user.id), "email": user.email, "display_name": user.display_name,
            "role": user.role.value, "tenant_id": str(user.tenant_id),
        },
    }


@router.get("/promo/{code}")
async def check_promo(code: str, db: AsyncSession = Depends(get_db)):
    """Public — validate a signup promo code and report the billing behavior it grants."""
    from app.core.promo import resolve_promo, MODE_HINT
    p = await resolve_promo(db, code)
    if not p:
        return {"valid": False}
    return {"valid": True, "billing_mode": p.billing_mode.value,
            "label": p.label, "hint": MODE_HINT.get(p.billing_mode.value)}


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    secret = generate_totp_secret()
    current_user.mfa_secret = encrypt(secret)  # stored encrypted at rest
    await db.commit()
    return MFASetupResponse(secret=secret, qr_uri=get_totp_uri(secret, current_user.email))


class MfaCodeBody(BaseModel):
    code: str


@router.post("/mfa/enable")
async def enable_mfa(
    body: MfaCodeBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.mfa_secret:
        raise HTTPException(status_code=400, detail="Run /mfa/setup first")
    if not verify_totp(decrypt(current_user.mfa_secret), body.code):
        raise HTTPException(status_code=401, detail="Invalid code")
    current_user.mfa_enabled = True
    await db.commit()
    return {"message": "MFA enabled", "mfa_enabled": True}


@router.post("/mfa/disable")
async def disable_mfa(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    await db.commit()
    return {"message": "MFA disabled", "mfa_enabled": False}


class ChangePasswordBody(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
async def change_password(
    body: ChangePasswordBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    _validate_password(body.new_password)
    current_user.password_hash = hash_password(body.new_password)
    await db.commit()
    return {"message": "Password updated"}


@router.get("/entitlements")
async def entitlements(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """What the current user's tenant is allowed to do — drives UI gating."""
    t = (await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))).scalar_one()
    ent = await get_entitlements(db, t)
    usage = await tenant_usage(db, t)
    ps = await get_settings(db)
    from app.core.entitlements import effective_mode
    trial = trial_state(t, ps.trial_days, effective_mode(t, ps))
    return {**ent, "usage": usage, "role": current_user.role.value,
            "tenant_type": t.tenant_type.value, "trial": trial, "org_name": t.name}


@router.get("/invite-info")
async def invite_info(token: str, db: AsyncSession = Depends(get_db)):
    """Public — describe an invite so the accept page can show who/what."""
    try:
        p = decode_token(token)
    except Exception:
        raise HTTPException(status_code=400, detail="This invite link is invalid or has expired")
    if p.get("type") != "invite":
        raise HTTPException(status_code=400, detail="Invalid invite")
    u = (await db.execute(select(User).where(User.id == uuid.UUID(p["sub"])))).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="Invite no longer valid")
    t = (await db.execute(select(Tenant).where(Tenant.id == u.tenant_id))).scalar_one()
    return {"email": u.email, "display_name": u.display_name, "org_name": t.name,
            "role": u.role.value, "already_active": u.is_active}


class AcceptInviteBody(BaseModel):
    token: str
    password: str


@router.post("/accept-invite")
async def accept_invite(body: AcceptInviteBody, db: AsyncSession = Depends(get_db)):
    try:
        p = decode_token(body.token)
    except Exception:
        raise HTTPException(status_code=400, detail="This invite link is invalid or has expired")
    if p.get("type") != "invite":
        raise HTTPException(status_code=400, detail="Invalid invite")
    _validate_password(body.password)
    u = (await db.execute(select(User).where(User.id == uuid.UUID(p["sub"])))).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="Invite no longer valid")
    u.password_hash = hash_password(body.password)
    u.is_active = True
    u.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    access_token = create_access_token({"sub": str(u.id)})
    return {"access_token": access_token, "user": {
        "id": str(u.id), "email": u.email, "display_name": u.display_name,
        "role": u.role.value, "tenant_id": str(u.tenant_id),
    }}


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "display_name": current_user.display_name,
        "role": current_user.role.value,
        "tenant_id": str(current_user.tenant_id),
        "mfa_enabled": current_user.mfa_enabled,
    }
