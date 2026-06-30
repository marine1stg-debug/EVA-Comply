"""In-app deployment configuration (single row) - General, Storage, Payments,
Security. Secrets (R2 secret, Stripe keys) are encrypted at rest. Every field
falls back to the server .env when blank, so an empty value never changes
current behavior.
"""
import uuid
from typing import Optional

from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin


class PlatformSettings(Base, TimestampMixin):
    __tablename__ = "platform_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # General
    site_url: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    app_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    support_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    from_noreply: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    from_cases: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    from_invoicing: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Storage
    storage_backend: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)   # local | r2 | s3
    r2_account_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    r2_access_key_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    r2_secret_access_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)     # encrypted
    r2_bucket: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    # Payments
    stripe_secret_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)        # encrypted
    stripe_webhook_secret: Mapped[Optional[str]] = mapped_column(Text, nullable=True)    # encrypted

    # Security (None = use .env / built-in default)
    session_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_password_length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
