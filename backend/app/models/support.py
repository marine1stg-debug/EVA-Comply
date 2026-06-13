import uuid
import enum
from typing import Optional
from sqlalchemy import String, Text, Boolean, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin


class SupportStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class SupportCase(Base, TimestampMixin):
    """A support request raised by any user, reviewed in the Super Admin console."""
    __tablename__ = "support_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    requester_name: Mapped[str] = mapped_column(String(200), default="")
    requester_email: Mapped[str] = mapped_column(String(200), default="")
    org_name: Mapped[str] = mapped_column(String(200), default="")
    category: Mapped[str] = mapped_column(String(60), default="Question")
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # native_enum=False → plain VARCHAR (matches the migration); avoids needing a
    # Postgres ENUM type named "supportstatus".
    status: Mapped[SupportStatus] = mapped_column(
        Enum(SupportStatus, native_enum=False, length=16), default=SupportStatus.open)
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attachment_key: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)
    attachment_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    attachment_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)


class SupportComment(Base, TimestampMixin):
    """One reply in a support case thread. Append-only — authors don't edit each other."""
    __tablename__ = "support_comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("support_cases.id"), nullable=False, index=True)
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    author_name: Mapped[str] = mapped_column(String(200), default="")
    author_role: Mapped[str] = mapped_column(String(40), default="")
    is_eva: Mapped[bool] = mapped_column(Boolean, default=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)


class SupportSettings(Base, TimestampMixin):
    """Single-row global config for the Contact Support feature."""
    __tablename__ = "support_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    # comma-separated category list
    categories: Mapped[str] = mapped_column(Text, default="Question,Bug,Billing,Feature request,Other")
    intro: Mapped[str] = mapped_column(Text, default="Need help? Send the EVA team a request and we'll get back to you.")
