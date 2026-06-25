import uuid
from typing import Optional
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin


class Recommendation(Base, TimestampMixin):
    """A remediation recommendation for closing a control's maturity gap.

    Generated per client (org) + control from either the curated pre-made
    library (keyed by control ref) or a one-click LLM analysis of the client's
    self-assessment. Reviewers can also add/edit them manually.

    effort / impact ∈ {low, medium, high}. A 'quick win' = low effort + high
    impact (derived, not stored). current_level / target_level snapshot the
    maturity gap at generation time so the rollup can rank and explain it.
    """
    __tablename__ = "recommendations"
    __table_args__ = (
        Index("ix_reco_org_control", "org_id", "control_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    control_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("controls.id"), nullable=False, index=True)

    source: Mapped[str] = mapped_column(String(10), default="premade")  # premade | ai | manual
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # Canadian-French translation (served when X-Lang=fr; falls back to EN).
    title_fr: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    text_fr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    effort: Mapped[str] = mapped_column(String(10), default="medium")   # low | medium | high
    impact: Mapped[str] = mapped_column(String(10), default="medium")   # low | medium | high

    current_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(String(12), default="open")     # open | in_progress | done | dismissed
    is_top10: Mapped[bool] = mapped_column(Boolean, default=False)       # flagged for the Top 10 priorities report
