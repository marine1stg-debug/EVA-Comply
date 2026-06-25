import uuid
import enum
from typing import Optional
from datetime import datetime, date
from sqlalchemy import String, Integer, Boolean, Enum, JSON, Text, DateTime, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
from app.models.base import TimestampMixin


class PlanTier(str, enum.Enum):
    single_client = "single_client"
    msp = "msp"


class BillingPlan(Base, TimestampMixin):
    __tablename__ = "billing_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tier: Mapped[PlanTier] = mapped_column(Enum(PlanTier), nullable=False)
    price_monthly: Mapped[int] = mapped_column(Integer, default=0)
    # MSP cost for this plan. Client pays retail (tenant.monthly_price); EVA keeps
    # the (volume-discounted) wholesale and pays the MSP retail − wholesale.
    wholesale_monthly: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # inclusions = {
    #   "frameworks": "all" | [framework_id, ...],
    #   "features": {"reports": bool, "import": bool, "msp_review": bool, "audit_logs": bool, "api": bool},
    #   "max_users": int,   # 0 = unlimited
    #   "max_clients": int, # 0 = unlimited (MSP plans only)
    # }
    inclusions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # Yearly billing: discount off 12× monthly. Cached Stripe Price ids per interval.
    yearly_discount_pct: Mapped[int] = mapped_column(Integer, default=0)
    stripe_price_monthly_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    stripe_price_yearly_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)


# Canonical feature keys used across the entitlements layer.
FEATURE_KEYS = ["reports", "import", "msp_review", "audit_logs", "api"]


class Invoice(Base, TimestampMixin):
    """A numbered invoice - Stripe subscription charges or MSP monthly consolidations."""
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    tenant_name: Mapped[str] = mapped_column(String(200), default="")
    kind: Mapped[str] = mapped_column(String(30), default="subscription")  # subscription | msp_consolidated | manual
    period_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    period_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    amount_cents: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(10), default="usd")
    status: Mapped[str] = mapped_column(String(20), default="open")  # draft | open | paid | void
    stripe_invoice_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    stripe_payment_intent: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    lines: Mapped[list] = mapped_column(JSONB, default=list)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now())
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
