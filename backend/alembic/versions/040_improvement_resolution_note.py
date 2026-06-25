"""Add improvement_requests.resolution_note (closing/implementation note).

Lets a request be marked Implemented with a note explaining how it was resolved,
instead of being deleted.

Revision ID: 040
Revises: 039
Create Date: 2026-06-25
"""
import sqlalchemy as sa
from alembic import op

revision = '040'
down_revision = '039'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('improvement_requests', sa.Column('resolution_note', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('improvement_requests', 'resolution_note')
