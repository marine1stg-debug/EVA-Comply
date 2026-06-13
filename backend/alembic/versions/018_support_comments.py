"""Support case comment thread

Each case becomes a thread: client, MSP and EVA each append their own comments.
Nobody edits anyone else's — replies are append-only.

Revision ID: 018
Revises: 017
Create Date: 2026-06-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'support_comments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('case_id', UUID(as_uuid=True), sa.ForeignKey('support_cases.id'), nullable=False),
        sa.Column('author_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('author_name', sa.String(length=200), nullable=False, server_default=''),
        sa.Column('author_role', sa.String(length=40), nullable=False, server_default=''),
        sa.Column('is_eva', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_support_comments_case_id', 'support_comments', ['case_id'])


def downgrade() -> None:
    op.drop_index('ix_support_comments_case_id', table_name='support_comments')
    op.drop_table('support_comments')
