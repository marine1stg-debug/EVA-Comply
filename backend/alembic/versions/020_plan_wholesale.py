"""Plan wholesale price (MSP reseller margin)

Adds billing_plans.wholesale_monthly — the MSP's cost for a plan. The client is
billed the retail price (tenant.monthly_price) via EVA's Stripe; EVA keeps the
(volume-discounted) wholesale and pays the MSP the difference as margin.

Backfills existing plans at ~70% of retail so margins aren't zero out of the box.

Revision ID: 020
Revises: 019
Create Date: 2026-06-07
"""
from alembic import op
import sqlalchemy as sa


revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('billing_plans', sa.Column('wholesale_monthly', sa.Integer(), nullable=False, server_default='0'))
    # Backfill: wholesale = round(price_monthly * 0.7)
    op.execute("UPDATE billing_plans SET wholesale_monthly = ROUND(price_monthly * 0.7) WHERE wholesale_monthly = 0")


def downgrade() -> None:
    op.drop_column('billing_plans', 'wholesale_monthly')
