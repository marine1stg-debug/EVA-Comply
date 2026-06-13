"""User account lockout

Adds failed_attempts + locked_until to users for the 3-strike lockout policy.

Revision ID: 021
Revises: 020
Create Date: 2026-06-07
"""
from alembic import op
import sqlalchemy as sa


revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('failed_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_attempts')
