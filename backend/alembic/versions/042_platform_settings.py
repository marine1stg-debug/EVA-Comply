"""In-app deployment configuration (single row): General, Storage, Payments,
Security. Secrets encrypted at rest; blank fields fall back to .env.

Revision ID: 042
Revises: 041
Create Date: 2026-06-25
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = '042'
down_revision = '041'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Idempotent: skip if the table already exists (defensive against a
    # half-applied state or a stray create_all).
    bind = op.get_bind()
    if sa.inspect(bind).has_table('deployment_config'):
        return
    op.create_table(
        'deployment_config',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('site_url', sa.String(length=300), nullable=True),
        sa.Column('app_name', sa.String(length=120), nullable=True),
        sa.Column('support_email', sa.String(length=255), nullable=True),
        sa.Column('from_noreply', sa.String(length=255), nullable=True),
        sa.Column('from_cases', sa.String(length=255), nullable=True),
        sa.Column('from_invoicing', sa.String(length=255), nullable=True),
        sa.Column('storage_backend', sa.String(length=20), nullable=True),
        sa.Column('r2_account_id', sa.String(length=120), nullable=True),
        sa.Column('r2_access_key_id', sa.String(length=255), nullable=True),
        sa.Column('r2_secret_access_key', sa.Text(), nullable=True),
        sa.Column('r2_bucket', sa.String(length=120), nullable=True),
        sa.Column('stripe_secret_key', sa.Text(), nullable=True),
        sa.Column('stripe_webhook_secret', sa.Text(), nullable=True),
        sa.Column('session_minutes', sa.Integer(), nullable=True),
        sa.Column('min_password_length', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('deployment_config')
