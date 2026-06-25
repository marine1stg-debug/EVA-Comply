import uuid
from typing import Optional
from datetime import datetime, date
from sqlalchemy import String, Boolean, Text, BigInteger, Enum, ForeignKey, DateTime, Date, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin
import enum


class OrgControlStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    implemented = "implemented"
    verified = "verified"
    non_applicable = "non_applicable"


class AuditDecision(str, enum.Enum):
    accepted = "accepted"
    rejected = "rejected"
    needs_more_evidence = "needs_more_evidence"
    not_applicable = "not_applicable"


class ControlStatus:
    """User-facing audit status vocabulary (stored as a plain string in
    org_controls.audit_status - kept separate from the legacy OrgControlStatus
    enum so dashboard/MSP rollups stay unchanged)."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    IN_PROGRESS = "in_progress"
    NOT_APPLICABLE = "not_applicable"
    ALL = ("compliant", "non_compliant", "in_progress", "not_applicable")


class EvidenceStatus(str, enum.Enum):
    draft = "draft"
    client_submitted = "client_submitted"
    msp_pending = "msp_pending"
    msp_approved = "msp_approved"
    msp_flagged = "msp_flagged"
    eva_pending = "eva_pending"
    accepted = "accepted"
    rejected = "rejected"
    needs_more = "needs_more"
    not_applicable = "not_applicable"


class EvidenceFrequency(str, enum.Enum):
    once = "once"
    monthly = "monthly"
    quarterly = "quarterly"
    semi_annual = "semi_annual"
    annual = "annual"
    continuous = "continuous"


class EvidenceSource(str, enum.Enum):
    upload = "upload"
    link = "link"
    manual = "manual"


class ScanStatus(str, enum.Enum):
    pending = "pending"
    clean = "clean"
    infected = "infected"
    error = "error"


class OrgControl(Base, TimestampMixin):
    __tablename__ = "org_controls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    control_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("controls.id"), nullable=False)
    status: Mapped[OrgControlStatus] = mapped_column(Enum(OrgControlStatus), default=OrgControlStatus.not_started)
    owner_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    coverage_pct: Mapped[int] = mapped_column(Integer, default=0)
    client_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    msp_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remediation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audit_decision: Mapped[Optional[AuditDecision]] = mapped_column(Enum(AuditDecision), nullable=True)
    auditor_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    auditor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Audit-status layer (see ControlStatus). audit_status drives the control
    # header; status_mode 'auto' re-derives it from evidence, 'manual' pins it.
    audit_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status_mode: Mapped[str] = mapped_column(String(10), default="auto")
    status_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    previous_audit_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # A coach (auditor) can re-open a control to challenge its evidence.
    under_review: Mapped[bool] = mapped_column(Boolean, default=False)
    under_review_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Simple relationships - no back_populates to avoid cross-file circular issues
    evidence_items: Mapped[list["EvidenceItem"]] = relationship("EvidenceItem", lazy="select")


class ExpectedEvidence(Base, TimestampMixin):
    """A single evidence requirement for a control, per client org.

    Seeded from the catalog's authored expected-evidence list (origin='catalog')
    and extendable per client (origin='custom'). `satisfied` drives the control's
    coverage %  (= satisfied / total).
    """
    __tablename__ = "expected_evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    control_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("controls.id"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_fr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # French label (catalog rows)
    frequency: Mapped[EvidenceFrequency] = mapped_column(Enum(EvidenceFrequency), default=EvidenceFrequency.annual)
    evidence_type: Mapped[str] = mapped_column(String(40), default="Document")
    origin: Mapped[str] = mapped_column(String(20), default="catalog")  # catalog | custom
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    satisfied: Mapped[bool] = mapped_column(Boolean, default=False)


class EvidenceItem(Base, TimestampMixin):
    __tablename__ = "evidence_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_control_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("org_controls.id"), nullable=False)
    expected_evidence_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("expected_evidence.id"), nullable=True)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    file_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    scan_status: Mapped[ScanStatus] = mapped_column(Enum(ScanStatus), default=ScanStatus.pending)
    source: Mapped[EvidenceSource] = mapped_column(Enum(EvidenceSource), default=EvidenceSource.upload)
    status: Mapped[EvidenceStatus] = mapped_column(Enum(EvidenceStatus), default=EvidenceStatus.draft)
    msp_pre_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    msp_reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    msp_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    frequency: Mapped[EvidenceFrequency] = mapped_column(Enum(EvidenceFrequency), default=EvidenceFrequency.once)
    expires_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # Reviewer's comment when accepting or returning the evidence.
    review_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ControlEvent(Base, TimestampMixin):
    """Append-only history of actions on a control's evidence (collected,
    accepted, returned, deleted, status change). Actor name is denormalized so
    the trail survives even if the user or evidence row is later removed."""
    __tablename__ = "control_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    control_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("controls.id"), nullable=False, index=True)
    evidence_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)  # no FK: survives deletes
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    actor_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False)   # collected | accepted | returned | deleted | status
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
