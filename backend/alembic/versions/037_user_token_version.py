"""Add users.token_version for refresh-token revocation.

Refresh tokens now carry the token_version they were issued at; changing a
password increments this counter, which invalidates every outstanding refresh
token for that user. Existing rows default to 0 (matching tokens already issued,
so no forced logout on deploy).

Revision ID: 037
Revises: 036
Create Date: 2026-06-23
"""
import sqlalchemy as sa
from alembic import op

revision = '037'
down_revision = '036'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('token_version', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('users', 'token_version')
