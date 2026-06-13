"""Add Control.best_practices

Revision ID: 004
Revises: 003
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('controls', sa.Column('best_practices', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('controls', 'best_practices')
