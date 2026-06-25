"""Add maturity_snapshots.is_baseline so a reviewer can pin which dated
snapshot drives the 'Previous' comparison (instead of always the latest).

Existing rows default to False; the maturity service falls back to the most
recent snapshot when none is pinned, so behavior is unchanged on upgrade.

Revision ID: 038
Revises: 037
Create Date: 2026-06-25
"""
import sqlalchemy as sa
from alembic import op

revision = '038'
down_revision = '037'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('maturity_snapshots', sa.Column('is_baseline', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column('maturity_snapshots', 'is_baseline')
