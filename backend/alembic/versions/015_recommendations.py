"""Recommendations engine

Adds recommendations: per-client, per-control remediation actions for closing
maturity gaps. Generated from the curated pre-made library or one-click LLM
analysis of the client's self-assessment, plus manual entries.

Revision ID: 015
Revises: 014
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'recommendations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('control_id', UUID(as_uuid=True), sa.ForeignKey('controls.id'), nullable=False),
        sa.Column('source', sa.String(length=10), nullable=False, server_default='premade'),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('effort', sa.String(length=10), nullable=False, server_default='medium'),
        sa.Column('impact', sa.String(length=10), nullable=False, server_default='medium'),
        sa.Column('current_level', sa.Integer(), nullable=True),
        sa.Column('target_level', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=12), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_recommendations_org_id', 'recommendations', ['org_id'])
    op.create_index('ix_recommendations_control_id', 'recommendations', ['control_id'])
    op.create_index('ix_reco_org_control', 'recommendations', ['org_id', 'control_id'])


def downgrade() -> None:
    op.drop_index('ix_reco_org_control', table_name='recommendations')
    op.drop_index('ix_recommendations_control_id', table_name='recommendations')
    op.drop_index('ix_recommendations_org_id', table_name='recommendations')
    op.drop_table('recommendations')
