"""Accounts & audit workflow

- tenants.activation_pending: MSP/Reseller accounts await Super Admin authorization
- tenants.audit_level: self | assisted | audited (engagement model)
- users.can_coach: auditor may challenge/coach (vs reviewer-only)
- org_controls.under_review / under_review_note: a coach put a control back under review

Revision ID: 026
Revises: 025
Create Date: 2026-06-08
"""
from alembic import op
import sqlalchemy as sa


revision = '026'
down_revision = '025'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tenants', sa.Column('activation_pending', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('tenants', sa.Column('audit_level', sa.String(length=20), nullable=False, server_default='self'))
    op.add_column('users', sa.Column('can_coach', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('org_controls', sa.Column('under_review', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('org_controls', sa.Column('under_review_note', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('org_controls', 'under_review_note')
    op.drop_column('org_controls', 'under_review')
    op.drop_column('users', 'can_coach')
    op.drop_column('tenants', 'audit_level')
    op.drop_column('tenants', 'activation_pending')
