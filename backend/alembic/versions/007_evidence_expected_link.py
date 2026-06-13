"""Link evidence items to a specific expected-evidence requirement

Revision ID: 007
Revises: 006
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'evidence_items',
        sa.Column('expected_evidence_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('expected_evidence.id'), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('evidence_items', 'expected_evidence_id')
