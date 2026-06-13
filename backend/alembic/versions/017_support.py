"""Support cases + Contact Support settings

Adds support_cases (user-raised requests reviewed in the Super Admin console)
and support_settings (single-row global config: enabled, categories, intro).

Revision ID: 017
Revises: 016
Create Date: 2026-06-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'support_cases',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=True),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('requester_name', sa.String(length=200), nullable=False, server_default=''),
        sa.Column('requester_email', sa.String(length=200), nullable=False, server_default=''),
        sa.Column('org_name', sa.String(length=200), nullable=False, server_default=''),
        sa.Column('category', sa.String(length=60), nullable=False, server_default='Question'),
        sa.Column('subject', sa.String(length=300), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='open'),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_support_cases_org_id', 'support_cases', ['org_id'])
    op.create_index('ix_support_cases_status', 'support_cases', ['status'])

    op.create_table(
        'support_settings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('categories', sa.Text(), nullable=False,
                  server_default='Question,Bug,Billing,Feature request,Other'),
        sa.Column('intro', sa.Text(), nullable=False,
                  server_default="Need help? Send the EVA team a request and we'll get back to you."),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('support_settings')
    op.drop_index('ix_support_cases_status', table_name='support_cases')
    op.drop_index('ix_support_cases_org_id', table_name='support_cases')
    op.drop_table('support_cases')
