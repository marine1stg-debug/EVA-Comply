"""Add expected_evidence.text_fr and backfill from the FR catalog lines

Expected-evidence rows are seeded per client from a control's English
`evidence_best_practices`, frozen at seed time. Add a French label column and
backfill catalog-origin rows from `controls.evidence_best_practices_fr`,
matched line-by-line via sort_order (EN and FR line counts are aligned 1:1
across all four catalogs).

Revision ID: 034
Revises: 033
Create Date: 2026-06-08
"""
import sqlalchemy as sa
from alembic import op

revision = '034'
down_revision = '033'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('expected_evidence', sa.Column('text_fr', sa.Text(), nullable=True))

    # Backfill catalog rows from the control's French evidence lines. Replicate
    # the seed logic exactly: split on newlines, strip, drop empty lines, then
    # index by position == sort_order.
    conn = op.get_bind()
    controls = conn.execute(sa.text(
        "SELECT id, evidence_best_practices_fr FROM controls "
        "WHERE evidence_best_practices_fr IS NOT NULL AND evidence_best_practices_fr <> ''"
    )).fetchall()
    upd = sa.text(
        "UPDATE expected_evidence SET text_fr = :t "
        "WHERE control_id = :c AND sort_order = :i AND origin = 'catalog' "
        "AND (text_fr IS NULL OR text_fr = '')"
    )
    for cid, fr in controls:
        lines = [ln.strip() for ln in (fr or '').split('\n') if ln.strip()]
        for i, line in enumerate(lines):
            conn.execute(upd, {"t": line, "c": cid, "i": i})


def downgrade() -> None:
    op.drop_column('expected_evidence', 'text_fr')
