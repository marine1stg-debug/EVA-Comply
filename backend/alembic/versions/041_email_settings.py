"""In-app email/SMTP settings (single row, encrypted secrets).

Revision ID: 041
Revises: 040
Create Date: 2026-06-25
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = '041'
down_revision = '040'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'email_settings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('backend', sa.String(length=20), nullable=False, server_default='smtp'),
        sa.Column('from_email', sa.String(length=255), nullable=True),
        sa.Column('smtp_host', sa.String(length=255), nullable=True),
        sa.Column('smtp_port', sa.Integer(), nullable=False, server_default='587'),
        sa.Column('smtp_user', sa.String(length=255), nullable=True),
        sa.Column('smtp_password', sa.Text(), nullable=True),
        sa.Column('smtp_tls', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('sendgrid_api_key', sa.Text(), nullable=True),
        sa.Column('configured', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('email_settings')
