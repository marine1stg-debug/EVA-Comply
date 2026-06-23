from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import pyotp
import secrets

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_verification_token(email: str, code: str, minutes: int = 15) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return jwt.encode(
        {"email": email, "code": code, "type": "verify", "exp": expire},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )


def gen_verification_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def make_captcha(minutes: int = 20) -> tuple[str, str]:
    """Self-contained arithmetic CAPTCHA. Returns (question, signed_token).
    The expected answer is carried in a short-lived signed JWT, so no server
    state is needed and the answer can't be tampered with."""
    a, b = secrets.randbelow(8) + 1, secrets.randbelow(8) + 1
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    token = jwt.encode(
        {"ans": a + b, "type": "captcha", "exp": expire},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )
    return f"{a} + {b}", token


def verify_captcha(token: str, answer: str) -> bool:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return False
    if payload.get("type") != "captcha":
        return False
    try:
        return int(str(answer).strip()) == int(payload.get("ans"))
    except (ValueError, TypeError):
        return False


def create_invite_token(user_id, email: str, days: int = 7) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=days)
    return jwt.encode(
        {"sub": str(user_id), "email": email, "type": "invite", "exp": expire},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )


def create_unlock_token(user_id, email: str, minutes: int = 30) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return jwt.encode(
        {"sub": str(user_id), "email": email, "type": "unlock", "exp": expire},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )


def random_password() -> str:
    return secrets.token_urlsafe(24)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        # Unparseable hash (e.g. the "!locked!" placeholder set when a user is
        # restored from a backup without credentials) → always deny.
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def verify_totp(secret: str | None, code: str) -> bool:
    if not secret:
        return False
    try:
        return pyotp.TOTP(secret).verify(code, valid_window=1)
    except Exception:
        return False


def get_totp_uri(secret: str, email: str) -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name="EVA Portal")
