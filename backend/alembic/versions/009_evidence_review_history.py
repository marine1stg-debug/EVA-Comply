"""Evidence review note + control event history

Revision ID: 009
Revises: 008
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('evidence_items', sa.Column('review_note', sa.Text(), nullable=True))
    op.create_table(
        'control_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('control_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('controls.id'), nullable=False),
        sa.Column('evidence_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_name', sa.String(length=200), nullable=True),
        sa.Column('action', sa.String(length=40), nullable=False),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_control_events_org_id', 'control_events', ['org_id'])
    op.create_index('ix_control_events_control_id', 'control_events', ['control_id'])


def downgrade() -> None:
    op.drop_index('ix_control_events_control_id', table_name='control_events')
    op.drop_index('ix_control_events_org_id', table_name='control_events')
    op.drop_table('control_events')
    op.drop_column('evidence_items', 'review_note')
