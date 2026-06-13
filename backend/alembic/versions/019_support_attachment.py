"""Support case attachment (e.g. a screenshot)

Adds optional attachment fields to support_cases.

Revision ID: 019
Revises: 018
Create Date: 2026-06-07
"""
from alembic import op
import sqlalchemy as sa


revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('support_cases', sa.Column('attachment_key', sa.String(length=400), nullable=True))
    op.add_column('support_cases', sa.Column('attachment_name', sa.String(length=300), nullable=True))
    op.add_column('support_cases', sa.Column('attachment_type', sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column('support_cases', 'attachment_type')
    op.drop_column('support_cases', 'attachment_name')
    op.drop_column('support_cases', 'attachment_key')
