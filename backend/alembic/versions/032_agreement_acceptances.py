"""Agreement acceptances (consent audit trail)

Revision ID: 032
Revises: 031
Create Date: 2026-06-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '032'
down_revision = '031'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'agreement_acceptances',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('account_type', sa.String(), nullable=False, server_default=''),
        sa.Column('version', sa.String(), nullable=False, server_default='', index=True),
        sa.Column('user_name', sa.String(), nullable=False, server_default=''),
        sa.Column('user_role', sa.String(), nullable=False, server_default=''),
        sa.Column('org_name', sa.String(), nullable=False, server_default=''),
        sa.Column('ip_address', sa.String(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('agreement_acceptances')
