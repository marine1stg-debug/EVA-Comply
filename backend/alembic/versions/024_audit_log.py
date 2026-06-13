"""Append-only audit log

Revision ID: 024
Revises: 023
Create Date: 2026-06-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = '024'
down_revision = '023'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('actor_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('actor_name', sa.String(length=200), nullable=False, server_default=''),
        sa.Column('actor_role', sa.String(length=40), nullable=False, server_default=''),
        sa.Column('org_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('action', sa.String(length=60), nullable=False, index=True),
        sa.Column('target', sa.String(length=300), nullable=False, server_default=''),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('audit_logs')
