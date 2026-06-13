"""Maturity assessments + snapshots

Per-client, per-framework, per-domain maturity ratings (0–5) with target, plus
dated snapshots for the 'Previous Maturity' series.

Revision ID: 011
Revises: 010
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'maturity_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('framework_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('frameworks.id'), nullable=False),
        sa.Column('domain', sa.String(length=200), nullable=False),
        sa.Column('current_level', sa.Integer(), nullable=True),
        sa.Column('target_level', sa.Integer(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('org_id', 'framework_id', 'domain', name='uq_maturity_org_fw_domain'),
    )
    op.create_index('ix_maturity_assessments_org_id', 'maturity_assessments', ['org_id'])
    op.create_index('ix_maturity_assessments_framework_id', 'maturity_assessments', ['framework_id'])

    op.create_table(
        'maturity_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('framework_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('frameworks.id'), nullable=False),
        sa.Column('taken_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('label', sa.String(length=120), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('overall', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_maturity_snapshots_org_id', 'maturity_snapshots', ['org_id'])
    op.create_index('ix_maturity_snapshots_framework_id', 'maturity_snapshots', ['framework_id'])


def downgrade() -> None:
    op.drop_table('maturity_snapshots')
    op.drop_table('maturity_assessments')
