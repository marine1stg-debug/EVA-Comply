import uuid
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin


class AgreementAcceptance(Base, TimestampMixin):
    """Record that a user read and accepted a version of the subscription
    agreement. Append-only audit trail of consent."""
    __tablename__ = "agreement_acceptances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    account_type: Mapped[str] = mapped_column(String, default="")
    version: Mapped[str] = mapped_column(String, default="", index=True)
    user_name: Mapped[str] = mapped_column(String, default="")
    user_role: Mapped[str] = mapped_column(String, default="")
    org_name: Mapped[str] = mapped_column(String, default="")
    ip_address: Mapped[str] = mapped_column(String, default="")
