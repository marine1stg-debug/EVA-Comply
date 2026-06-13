"""Platform settings (billing mode + trial length)

Revision ID: 003
Revises: 002
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'platform_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('billing_mode', sa.Enum('no_card_trial', 'card_trial', 'charge_immediately', name='billingmode'), nullable=False, server_default='no_card_trial'),
        sa.Column('trial_days', sa.Integer(), nullable=False, server_default='14'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('platform_settings')
