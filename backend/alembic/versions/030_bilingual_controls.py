"""Bilingual content: French columns on controls + frameworks

Revision ID: 030
Revises: 029
Create Date: 2026-06-08
"""
from alembic import op
import sqlalchemy as sa

revision = '030'
down_revision = '029'
branch_labels = None
depends_on = None

_CONTROL_COLS = [
    "title_fr", "description_fr", "objective_fr",
    "plain_language_fr", "best_practices_fr", "evidence_best_practices_fr",
    "discussion_fr",
]


def upgrade() -> None:
    for c in _CONTROL_COLS:
        op.add_column('controls', sa.Column(c, sa.Text(), nullable=True))
    op.add_column('frameworks', sa.Column('description_fr', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('frameworks', 'description_fr')
    for c in _CONTROL_COLS:
        op.drop_column('controls', c)
