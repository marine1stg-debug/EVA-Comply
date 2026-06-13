"""Signup promo codes + per-tenant billing mode

Revision ID: 008
Revises: 007
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None

# billingmode enum already created with platform_settings (migration 003)
_mode = postgresql.ENUM('no_card_trial', 'card_trial', 'charge_immediately',
                        name='billingmode', create_type=False)


def upgrade() -> None:
    op.add_column('tenants', sa.Column('billing_mode', sa.String(length=30), nullable=True))
    op.create_table(
        'promo_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(length=40), nullable=False),
        sa.Column('billing_mode', _mode, nullable=False),
        sa.Column('label', sa.String(length=120), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('uses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_promo_codes_code', 'promo_codes', ['code'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_promo_codes_code', table_name='promo_codes')
    op.drop_table('promo_codes')
    op.drop_column('tenants', 'billing_mode')
