import uuid
from typing import Optional
from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
from app.models.base import TimestampMixin


class MarketplaceSkill(Base, TimestampMixin):
    """Editable extra skills (beyond control domains) offered for selection."""
    __tablename__ = "marketplace_skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)


class ServiceProvider(Base, TimestampMixin):
    """A marketplace partner who can help clients implement controls.

    `skills` is a list of control-domain names the provider covers (the skill
    taxonomy is derived from control domains). `priority_weight` orders providers
    in listings (higher = shown first). `status`: pending | active | suspended.
    """
    __tablename__ = "service_providers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(200), default="")
    contact_email: Mapped[str] = mapped_column(String(255), default="")
    website: Mapped[str] = mapped_column(String(300), default="")
    skills: Mapped[list] = mapped_column(JSONB, default=list)
    priority_weight: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
