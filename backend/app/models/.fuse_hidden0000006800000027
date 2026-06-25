import uuid
from typing import Optional
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin


class AuditLog(Base, TimestampMixin):
    """Append-only record of who did what. Never updated or deleted in normal use."""
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    actor_name: Mapped[str] = mapped_column(String(200), default="")
    actor_role: Mapped[str] = mapped_column(String(40), default="")
    # The tenant the action affected (nullable for platform-wide events).
    org_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(60), nullable=False, index=True)  # e.g. user.role_changed
    target: Mapped[str] = mapped_column(String(300), default="")                  # human label of the object
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)            # extra context
