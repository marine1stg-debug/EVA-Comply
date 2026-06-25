import uuid
from typing import Optional
from sqlalchemy import String, Boolean, Text, Integer, Enum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin
import enum


class ControlPriority(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"


class ControlRisk(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    informational = "informational"


class ControlCategory(str, enum.Enum):
    technical = "technical"
    administrative = "administrative"
    physical = "physical"
    hybrid = "hybrid"


class Framework(Base, TimestampMixin):
    __tablename__ = "frameworks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_fr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=True)
    imported_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    levels: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Overview/training video: external link (Vimeo/YouTube/URL) or app-hosted file.
    intro_video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    intro_video_key: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)

    controls: Mapped[list["Control"]] = relationship("Control", lazy="select")


class Control(Base, TimestampMixin):
    __tablename__ = "controls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("frameworks.id"), nullable=False)
    ref: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    objective: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plain_language: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    best_practices: Mapped[Optional[str]] = mapped_column(Text, nullable=True)         # how to implement well
    evidence_best_practices: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # expected evidence (artifacts)
    discussion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)              # official standard discussion/guidance
    # French localization (EN columns above are the fallback when these are empty).
    title_fr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_fr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    objective_fr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plain_language_fr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    best_practices_fr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_best_practices_fr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    discussion_fr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    priority: Mapped[Optional[ControlPriority]] = mapped_column(Enum(ControlPriority), nullable=True)
    risk_rating: Mapped[Optional[ControlRisk]] = mapped_column(Enum(ControlRisk), nullable=True)
    control_category: Mapped[Optional[ControlCategory]] = mapped_column(Enum(ControlCategory), nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_key: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)  # app-hosted/recorded file
    # Pre-written explainer-video scripts, authored in advance, bilingual.
    video_script_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    video_script_fr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mappings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Optional control-specific maturity self-assessment questions. When present,
    # overrides the generic generated ladder. Shape: [{key, prompt, options:[{key,
    # level, short, label}]}]. None → fall back to the generic ladder.
    maturity_questions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
