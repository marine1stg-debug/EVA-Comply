"""Framework & control training videos

Frameworks get an intro/overview video; controls already have video_url — add a
video_key for app-hosted (recorded/uploaded) files alongside external links.

Revision ID: 022
Revises: 021
Create Date: 2026-06-07
"""
from alembic import op
import sqlalchemy as sa


revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('frameworks', sa.Column('intro_video_url', sa.String(length=500), nullable=True))
    op.add_column('frameworks', sa.Column('intro_video_key', sa.String(length=400), nullable=True))
    op.add_column('controls', sa.Column('video_key', sa.String(length=400), nullable=True))


def downgrade() -> None:
    op.drop_column('controls', 'video_key')
    op.drop_column('frameworks', 'intro_video_key')
    op.drop_column('frameworks', 'intro_video_url')
