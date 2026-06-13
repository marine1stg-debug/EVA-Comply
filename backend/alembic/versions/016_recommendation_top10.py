"""Recommendation Top 10 flag

Adds recommendations.is_top10 so a curated/AI-picked Top 10 can be flagged and
highlighted in the recommendations report.

Revision ID: 016
Revises: 015
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa


revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('recommendations', sa.Column('is_top10', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column('recommendations', 'is_top10')
