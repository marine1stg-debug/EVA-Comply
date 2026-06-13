"""Audit-status layer on org_controls

Adds an editable, audit-oriented status (Compliant / Non-Compliant /
In Progress / Not Applicable) on top of the legacy OrgControlStatus enum,
plus a status note and a per-control Previous Audit Notes field. Additive only —
the legacy `status` column is left in place so dashboard/MSP rollups are
unaffected.

Revision ID: 010
Revises: 009
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('org_controls', sa.Column('audit_status', sa.String(length=20), nullable=True))
    op.add_column('org_controls', sa.Column('status_mode', sa.String(length=10), server_default='auto', nullable=False))
    op.add_column('org_controls', sa.Column('status_note', sa.Text(), nullable=True))
    op.add_column('org_controls', sa.Column('previous_audit_notes', sa.Text(), nullable=True))

    # Backfill audit_status from the legacy enum so existing rows render sensibly.
    op.execute("""
        UPDATE org_controls SET audit_status = CASE
            WHEN status IN ('verified', 'implemented') THEN 'compliant'
            WHEN status = 'non_applicable' THEN 'not_applicable'
            ELSE 'in_progress'
        END
        WHERE audit_status IS NULL
    """)


def downgrade() -> None:
    op.drop_column('org_controls', 'previous_audit_notes')
    op.drop_column('org_controls', 'status_note')
    op.drop_column('org_controls', 'status_mode')
    op.drop_column('org_controls', 'audit_status')
