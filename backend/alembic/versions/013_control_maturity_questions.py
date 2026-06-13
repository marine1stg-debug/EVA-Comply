"""Control-specific maturity question override

Adds controls.maturity_questions (JSON) so a control can carry bespoke,
control-specific self-assessment questions that override the generic ladder.

Revision ID: 013
Revises: 012
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa

revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('controls', sa.Column('maturity_questions', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('controls', 'maturity_questions')
