"""Add recommendations.title_fr/text_fr and backfill premade rows.

Recommendations were generated/stored in English only. Add French columns
(served when X-Lang=fr, EN fallback) and backfill existing premade rows by
matching their English title against the bilingual curated library.

Revision ID: 035
Revises: 034
Create Date: 2026-06-22
"""
import sqlalchemy as sa
from alembic import op

from app.recommendation_banks import NIST_171R3_RECS

revision = '035'
down_revision = '034'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('recommendations', sa.Column('title_fr', sa.String(length=300), nullable=True))
    op.add_column('recommendations', sa.Column('text_fr', sa.Text(), nullable=True))

    # Backfill existing rows by matching English title -> FR pair from the bank.
    by_title: dict[str, tuple[str, str]] = {}
    for recs in NIST_171R3_RECS.values():
        for r in recs:
            if r.get('title_fr'):
                by_title[r['title']] = (r['title_fr'], r.get('text_fr'))

    conn = op.get_bind()
    upd = sa.text(
        "UPDATE recommendations SET title_fr = :tf, text_fr = :xf "
        "WHERE title = :t AND (title_fr IS NULL OR title_fr = '')"
    )
    for title, (tf, xf) in by_title.items():
        conn.execute(upd, {"tf": tf, "xf": xf, "t": title})


def downgrade() -> None:
    op.drop_column('recommendations', 'text_fr')
    op.drop_column('recommendations', 'title_fr')
