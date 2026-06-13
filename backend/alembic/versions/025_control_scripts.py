"""Control video scripts (bilingual)

Pre-written recording scripts per control, in English and French, shown to the
person recording the explainer video.

Revision ID: 025
Revises: 024
Create Date: 2026-06-08
"""
from alembic import op
import sqlalchemy as sa


revision = '025'
down_revision = '024'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('controls', sa.Column('video_script_en', sa.Text(), nullable=True))
    op.add_column('controls', sa.Column('video_script_fr', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('controls', 'video_script_fr')
    op.drop_column('controls', 'video_script_en')
