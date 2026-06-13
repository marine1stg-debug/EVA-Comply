"""Service provider marketplace

A registry of partners who can help clients implement controls. EVA authorizes
each provider, sets a priority weight, and the skills (control domains) they cover.

Revision ID: 027
Revises: 026
Create Date: 2026-06-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = '027'
down_revision = '026'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'service_providers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('contact_name', sa.String(length=200), nullable=False, server_default=''),
        sa.Column('contact_email', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('website', sa.String(length=300), nullable=False, server_default=''),
        sa.Column('skills', JSONB, nullable=False, server_default='[]'),
        sa.Column('priority_weight', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('service_providers')
