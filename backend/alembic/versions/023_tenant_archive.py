"""Tenant archive

Archived tenants keep all history but disappear from selectors and listings.
They remain visible only in Tenant Management (Archived filter) for review.

Revision ID: 023
Revises: 022
Create Date: 2026-06-07
"""
from alembic import op
import sqlalchemy as sa


revision = '023'
down_revision = '022'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tenants', sa.Column('archived', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('tenants', sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('tenants', 'archived_at')
    op.drop_column('tenants', 'archived')
