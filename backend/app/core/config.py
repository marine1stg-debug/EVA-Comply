from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # App
    ENVIRONMENT: Literal["development", "production"] = "development"
    # Public base URL of the frontend - used to build invite/reset/unlock links.
    FRONTEND_URL: str = "http://localhost:3000"
    SECRET_KEY: str = "dev_secret_key_change_in_production_min_32_chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://eva_user:eva_secret_change_in_prod@db:5432/eva_db"

    # Redis
    REDIS_URL: str = "redis://redis:6379"

    # LLM connector SSRF guard. Default False blocks the connector from calling
    # private/loopback/link-local addresses. Set True only if you run a trusted
    # internal LLM (e.g. Ollama on localhost or an internal vLLM endpoint).
    LLM_ALLOW_PRIVATE_NETWORKS: bool = False

    # Storage
    STORAGE_BACKEND: Literal["local", "s3", "r2", "azure", "gcs"] = "local"
    STORAGE_LOCAL_PATH: str = "/app/uploads"
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "eva-uploads"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Email
    EMAIL_BACKEND: Literal["console", "sendgrid", "ses", "smtp"] = "console"
    FROM_EMAIL: str = "noreply@eva-technologies.com"
    SENDGRID_API_KEY: str = ""
    # SMTP (used when EMAIL_BACKEND=smtp)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    # Three configurable sender addresses (fall back to FROM_EMAIL if blank).
    EMAIL_FROM_INVOICING: str = ""
    EMAIL_FROM_CASES: str = ""
    EMAIL_FROM_NOREPLY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# ── production safety guard ──────────────────────────────────────────────────
# Refuse to start in production with development defaults. Every JWT in the app
# is signed with SECRET_KEY, so a default key means anyone can forge tokens.
_DEV_SECRET = "dev_secret_key_change_in_production_min_32_chars"
_DEV_DB_PASSWORD = "eva_secret_change_in_prod"

if settings.ENVIRONMENT == "production":
    _problems = []
    if settings.SECRET_KEY == _DEV_SECRET or len(settings.SECRET_KEY) < 32:
        _problems.append("SECRET_KEY is the dev default or shorter than 32 chars")
    if _DEV_DB_PASSWORD in settings.DATABASE_URL:
        _problems.append("DATABASE_URL still uses the dev default password")
    if settings.EMAIL_BACKEND == "console":
        _problems.append(
            "EMAIL_BACKEND=console leaks verification codes/links in API responses"
        )
    if _problems:
        raise RuntimeError(
            "Refusing to start with ENVIRONMENT=production and insecure settings: "
            + "; ".join(_problems)
        )
