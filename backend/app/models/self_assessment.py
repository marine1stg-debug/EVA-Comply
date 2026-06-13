import uuid
from typing import Optional
from sqlalchemy import Text, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin


class SelfAssessment(Base, TimestampMixin):
    """A client's maturity self-rating for one control.

    answers = {question_key: level(1–5)}. v1 ships one generated question per
    control (key 'default'); the JSON column supports multiple/bespoke questions
    later without a schema change. comment is the single control-level
    'Comments / Additional info' note."""
    __tablename__ = "maturity_self_assessments"
    __table_args__ = (
        UniqueConstraint("org_id", "control_id", name="uq_self_assess_org_control"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    control_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("controls.id"), nullable=False, index=True)
    answers: Mapped[dict] = mapped_column(JSON, default=dict)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
