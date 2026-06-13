"""LLM connector settings (single row)

Adds llm_settings: super-admin-managed connection to a private/hosted LLM API
used for AI-assisted evidence review and recommendation generation. The API
key is stored server-side only.

Revision ID: 014
Revises: 013
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'llm_settings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('provider', sa.String(length=20), nullable=False, server_default='openai'),
        sa.Column('base_url', sa.String(length=500), nullable=True),
        sa.Column('model', sa.String(length=200), nullable=True),
        sa.Column('api_key', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('extra_header_name', sa.String(length=100), nullable=True),
        sa.Column('extra_header_value', sa.Text(), nullable=True),
        sa.Column('last_tested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_test_ok', sa.Boolean(), nullable=True),
        sa.Column('last_test_msg', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('llm_settings')
