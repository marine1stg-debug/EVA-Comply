"""Add expected_evidence table (per-client evidence requirements)

Revision ID: 006
Revises: 005
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None

# Reuse the existing evidencefrequency enum already created in 001; do NOT recreate it.
_freq = postgresql.ENUM(
    'once', 'monthly', 'quarterly', 'semi_annual', 'annual', 'continuous',
    name='evidencefrequency', create_type=False,
)


def upgrade() -> None:
    op.create_table(
        'expected_evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('control_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('controls.id'), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('frequency', _freq, nullable=False, server_default='annual'),
        sa.Column('evidence_type', sa.String(length=40), nullable=False, server_default='Document'),
        sa.Column('origin', sa.String(length=20), nullable=False, server_default='catalog'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('satisfied', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_expected_evidence_org_id', 'expected_evidence', ['org_id'])
    op.create_index('ix_expected_evidence_control_id', 'expected_evidence', ['control_id'])


def downgrade() -> None:
    op.drop_index('ix_expected_evidence_control_id', table_name='expected_evidence')
    op.drop_index('ix_expected_evidence_org_id', table_name='expected_evidence')
    op.drop_table('expected_evidence')
