"""Internal Improvement/Request log + user.is_developer flag.

Adds improvement_requests and improvement_attachments (an internal issue log the
EVA team uses to record fixes/ideas, with screenshots), plus a developer label
on users.

Revision ID: 039
Revises: 038
Create Date: 2026-06-25
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = '039'
down_revision = '038'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_developer', sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        'improvement_requests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('author_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True, index=True),
        sa.Column('author_name', sa.String(length=200), nullable=False),
        sa.Column('author_role', sa.String(length=40), nullable=True),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=30), nullable=False, server_default='bug'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
        sa.Column('page_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'improvement_attachments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('request_id', UUID(as_uuid=True), sa.ForeignKey('improvement_requests.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False, server_default='image/png'),
        sa.Column('original_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('improvement_attachments')
    op.drop_table('improvement_requests')
    op.drop_column('users', 'is_developer')
