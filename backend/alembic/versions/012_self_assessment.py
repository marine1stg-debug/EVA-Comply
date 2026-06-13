"""Maturity self-assessment responses

Per-client, per-control maturity self-rating (answers JSON + comment).

Revision ID: 012
Revises: 011
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'maturity_self_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('control_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('controls.id'), nullable=False),
        sa.Column('answers', sa.JSON(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('org_id', 'control_id', name='uq_self_assess_org_control'),
    )
    op.create_index('ix_self_assess_org', 'maturity_self_assessments', ['org_id'])
    op.create_index('ix_self_assess_control', 'maturity_self_assessments', ['control_id'])


def downgrade() -> None:
    op.drop_table('maturity_self_assessments')
