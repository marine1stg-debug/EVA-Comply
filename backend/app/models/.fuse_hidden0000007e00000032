import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, Float, JSON, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin

# Generic 0–5 maturity scale shared across frameworks.
MATURITY_MIN = 0
MATURITY_MAX = 5


class MaturityAssessment(Base, TimestampMixin):
    """Per-client, per-framework, per-domain maturity rating.

    current_level is the auditor's effective rating (auto-seeded from compliance
    when left NULL); target_level is the goal. One row per (org, framework, domain)."""
    __tablename__ = "maturity_assessments"
    __table_args__ = (
        UniqueConstraint("org_id", "framework_id", "domain", name="uq_maturity_org_fw_domain"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    framework_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("frameworks.id"), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(200), nullable=False)
    current_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class MaturitySnapshot(Base, TimestampMixin):
    """A dated baseline of per-domain current levels, used to draw the
    'Previous Maturity' series and trend. payload = [{domain, level}, ...]."""
    __tablename__ = "maturity_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    framework_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("frameworks.id"), nullable=False, index=True)
    taken_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    label: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    payload: Mapped[list] = mapped_column(JSON, default=list)
    overall: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
