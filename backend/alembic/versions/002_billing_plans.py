"""Billing plans (configurable packages)

Revision ID: 002
Revises: 001
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('billing_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('tier', sa.Enum('single_client', 'msp', name='plantier'), nullable=False),
        sa.Column('price_monthly', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('inclusions', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.add_column('tenants', sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_tenants_plan_id', 'tenants', 'billing_plans', ['plan_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_tenants_plan_id', 'tenants', type_='foreignkey')
    op.drop_column('tenants', 'plan_id')
    op.drop_table('billing_plans')
