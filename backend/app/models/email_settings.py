"""In-app email / SMTP configuration (single row).

Lets a Super Admin set the mail provider from the Administration UI instead of
editing the server .env. Secrets (SMTP password, SendGrid key) are encrypted at
rest. When `configured` is False, the mailer falls back to the .env settings.
"""
import uuid
from typing import Optional

from sqlalchemy import String, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin


class EmailSettings(Base, TimestampMixin):
    __tablename__ = "email_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    backend: Mapped[str] = mapped_column(String(20), nullable=False, default="smtp")   # smtp | sendgrid | console
    from_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    smtp_host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    smtp_port: Mapped[int] = mapped_column(Integer, nullable=False, default=587)
    smtp_user: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    smtp_password: Mapped[Optional[str]] = mapped_column(Text, nullable=True)          # encrypted
    smtp_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sendgrid_api_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)       # encrypted
    # False = not set up in-app yet → the mailer uses the .env values instead.
    configured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
