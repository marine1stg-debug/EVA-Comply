import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Boolean, Enum, ForeignKey, JSON, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin
import enum


class TenantType(str, enum.Enum):
    msp = "msp"
    single_client = "single_client"
    eva_internal = "eva_internal"


class SubscriptionStatus(str, enum.Enum):
    active = "active"
    trialing = "trialing"
    past_due = "past_due"
    suspended = "suspended"
    cancelled = "cancelled"


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    tenant_type: Mapped[TenantType] = mapped_column(Enum(TenantType), nullable=False)
    parent_msp_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True
    )
    subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subscription_status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), default=SubscriptionStatus.trialing
    )
    msp_review_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("billing_plans.id"), nullable=True
    )
    plan_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    monthly_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Per-tenant billing mode (from the signup promo code). NULL → use the
    # platform default. Stored as a plain string to avoid enum coupling.
    billing_mode: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Archived tenants keep all history but vanish from selectors/listings.
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # MSP/Reseller self-registrations wait for a Super Admin to authorize them.
    activation_pending: Mapped[bool] = mapped_column(Boolean, default=False)
    # Engagement model for a client: self | assisted | audited.
    audit_level: Mapped[str] = mapped_column(String(20), default="self")
    # Stripe customer (for subscriptions / invoices).
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
