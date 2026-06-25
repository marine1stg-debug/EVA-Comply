"""Small billing helpers shared by the API and (via the overview endpoint) the UI.

Stripe itself is imported lazily inside app/api/billing.py only when a secret key
is configured, so the app runs fine with no Stripe credentials.
"""
from app.models.billing import BillingPlan


def yearly_price(plan: BillingPlan) -> int:
    """Annual price in whole currency units = 12× monthly less the plan discount."""
    disc = max(0, min(100, plan.yearly_discount_pct or 0))
    return round((plan.price_monthly or 0) * 12 * (1 - disc / 100.0))


def monthly_price(plan: BillingPlan) -> int:
    return int(plan.price_monthly or 0)


def interval_amount(plan: BillingPlan, interval: str) -> int:
    """Whole-unit charge for the chosen interval ('year' or 'month')."""
    return yearly_price(plan) if interval == "year" else monthly_price(plan)
