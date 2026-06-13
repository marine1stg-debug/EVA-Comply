"""Dedupe expected_evidence and add a uniqueness guard

Removes duplicate expected-evidence rows (same org + control + text) created by
two endpoints seeding the catalog list concurrently, repoints any attached
evidence to the kept row, then adds a unique index to prevent recurrence.

Revision ID: 033
Revises: 032
Create Date: 2026-06-08
"""
from alembic import op

revision = '033'
down_revision = '032'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Repoint evidence items from duplicate rows to the kept (lowest-id) row.
    op.execute("""
        UPDATE evidence_items ei
        SET expected_evidence_id = m.keep_id
        FROM expected_evidence d
        JOIN (
            SELECT org_id, control_id, text, MIN(id::text)::uuid AS keep_id
            FROM expected_evidence
            GROUP BY org_id, control_id, text
        ) m ON m.org_id = d.org_id AND m.control_id = d.control_id AND m.text = d.text
        WHERE ei.expected_evidence_id = d.id AND d.id <> m.keep_id;
    """)
    # 2) Delete the duplicate rows, keeping the lowest id per (org, control, text).
    op.execute("""
        DELETE FROM expected_evidence d
        USING (
            SELECT org_id, control_id, text, MIN(id::text)::uuid AS keep_id
            FROM expected_evidence
            GROUP BY org_id, control_id, text
        ) m
        WHERE d.org_id = m.org_id AND d.control_id = m.control_id
          AND d.text = m.text AND d.id <> m.keep_id;
    """)
    # 3) Prevent recurrence.
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_ee_org_control_text
        ON expected_evidence (org_id, control_id, text);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_ee_org_control_text;")
