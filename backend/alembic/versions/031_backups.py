"""Backup snapshots metadata table

Revision ID: 031
Revises: 030
Create Date: 2026-06-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '031'
down_revision = '030'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'backups',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('label', sa.String(), nullable=False, server_default=''),
        sa.Column('created_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_by_name', sa.String(), nullable=False, server_default=''),
        sa.Column('categories', sa.JSON(), nullable=True),
        sa.Column('client_ids', sa.JSON(), nullable=True),
        sa.Column('scope', sa.String(), nullable=False, server_default=''),
        sa.Column('total_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('size_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('filename', sa.String(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('backups')
