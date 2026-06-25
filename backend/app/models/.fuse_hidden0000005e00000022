import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.platform import BillingMode


class PromoCode(Base, TimestampMixin):
    """A signup code that grants a specific billing mode (no-card trial,
    card trial, or charge immediately). Reusable by default; cap with max_uses."""
    __tablename__ = "promo_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    billing_mode: Mapped[BillingMode] = mapped_column(Enum(BillingMode), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    max_uses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # null = unlimited
    uses: Mapped[int] = mapped_column(Integer, default=0)
