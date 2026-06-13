"""Billing: invoices, yearly pricing, Stripe references

Revision ID: 029
Revises: 028
Create Date: 2026-06-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = '029'
down_revision = '028'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Plans: yearly discount + cached Stripe price ids
    op.add_column('billing_plans', sa.Column('yearly_discount_pct', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('billing_plans', sa.Column('stripe_price_monthly_id', sa.String(length=120), nullable=True))
    op.add_column('billing_plans', sa.Column('stripe_price_yearly_id', sa.String(length=120), nullable=True))
    # Tenant: Stripe customer
    op.add_column('tenants', sa.Column('stripe_customer_id', sa.String(length=120), nullable=True))

    op.create_table(
        'invoices',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('number', sa.String(length=40), nullable=False, unique=True),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=True, index=True),
        sa.Column('tenant_name', sa.String(length=200), nullable=False, server_default=''),
        sa.Column('kind', sa.String(length=30), nullable=False, server_default='subscription'),
        sa.Column('period_start', sa.Date(), nullable=True),
        sa.Column('period_end', sa.Date(), nullable=True),
        sa.Column('amount_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='usd'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
        sa.Column('stripe_invoice_id', sa.String(length=120), nullable=True),
        sa.Column('stripe_payment_intent', sa.String(length=120), nullable=True),
        sa.Column('lines', JSONB, nullable=False, server_default='[]'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('issued_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('invoices')
    op.drop_column('tenants', 'stripe_customer_id')
    op.drop_column('billing_plans', 'stripe_price_yearly_id')
    op.drop_column('billing_plans', 'stripe_price_monthly_id')
    op.drop_column('billing_plans', 'yearly_discount_pct')
