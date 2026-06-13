"""Custom marketplace skills

Skills shown to providers = canonical control domains + this editable list of
extra IT skills (e.g. Backup, DRP) managed by the Super Admin.

Revision ID: 028
Revises: 027
Create Date: 2026-06-08
"""
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = '028'
down_revision = '027'
branch_labels = None
depends_on = None

STARTER = [
    "Backup & Recovery", "Disaster Recovery (DRP)", "Business Continuity (BCP)",
    "Endpoint Protection (EDR)", "Firewall & Network Security", "Email Security",
    "Cloud Security", "Identity & Access Management (MFA/SSO)", "SIEM & Log Management",
    "Vulnerability Management & Patching", "Penetration Testing", "Security Awareness Training",
    "vCISO / Advisory", "Microsoft 365 Security", "Encryption & Key Management",
    "Mobile Device Management (MDM)",
]


def upgrade() -> None:
    t = op.create_table(
        'marketplace_skills',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.bulk_insert(t, [{"id": uuid.uuid4(), "name": n} for n in STARTER])


def downgrade() -> None:
    op.drop_table('marketplace_skills')
