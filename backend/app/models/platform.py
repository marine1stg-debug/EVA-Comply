import uuid
import enum
from sqlalchemy import Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin


class BillingMode(str, enum.Enum):
    no_card_trial = "no_card_trial"          # sign up free, trial, then lock until paid
    card_trial = "card_trial"                # card at signup, Stripe trial, auto-charge
    charge_immediately = "charge_immediately"  # must pay at signup, no trial


class PlatformSettings(Base, TimestampMixin):
    """Single-row global configuration for monetization behavior."""
    __tablename__ = "platform_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    billing_mode: Mapped[BillingMode] = mapped_column(Enum(BillingMode), default=BillingMode.no_card_trial)
    trial_days: Mapped[int] = mapped_column(Integer, default=14)
