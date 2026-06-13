"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-06-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tenants
    op.create_table('tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('tenant_type', sa.Enum('msp','single_client','eva_internal', name='tenanttype'), nullable=False),
        sa.Column('parent_msp_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('subscription_id', sa.String(255), nullable=True),
        sa.Column('subscription_status', sa.Enum('active','trialing','past_due','suspended','cancelled', name='subscriptionstatus'), nullable=False, server_default='trialing'),
        sa.Column('msp_review_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('plan_name', sa.String(100), nullable=True),
        sa.Column('monthly_price', sa.Integer(), nullable=True),
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['parent_msp_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # Users
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('super_admin','eva_auditor','msp_admin','msp_analyst','client_admin','contributor','viewer', name='userrole'), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('mfa_secret', sa.String(255), nullable=True),
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])

    # Frameworks
    op.create_table('frameworks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('imported_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('levels', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Controls
    op.create_table('controls',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('framework_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ref', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('objective', sa.Text(), nullable=True),
        sa.Column('plain_language', sa.Text(), nullable=True),
        sa.Column('evidence_best_practices', sa.Text(), nullable=True),
        sa.Column('level', sa.String(50), nullable=True),
        sa.Column('domain', sa.String(200), nullable=True),
        sa.Column('priority', sa.Enum('high','medium','low', name='controlpriority'), nullable=True),
        sa.Column('risk_rating', sa.Enum('critical','high','medium','low','informational', name='controlrisk'), nullable=True),
        sa.Column('control_category', sa.Enum('technical','administrative','physical','hybrid', name='controlcategory'), nullable=True),
        sa.Column('video_url', sa.String(500), nullable=True),
        sa.Column('mappings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['framework_id'], ['frameworks.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_controls_ref', 'controls', ['ref'])

    # Org controls
    op.create_table('org_controls',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('control_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('not_started','in_progress','implemented','verified','non_applicable', name='orgcontrolstatus'), nullable=False, server_default='not_started'),
        sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('coverage_pct', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('client_response', sa.Text(), nullable=True),
        sa.Column('msp_response', sa.Text(), nullable=True),
        sa.Column('remediation_notes', sa.Text(), nullable=True),
        sa.Column('audit_decision', sa.Enum('accepted','rejected','needs_more_evidence','not_applicable', name='auditdecision'), nullable=True),
        sa.Column('auditor_notes', sa.Text(), nullable=True),
        sa.Column('auditor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['control_id'], ['controls.id']),
        sa.ForeignKeyConstraint(['org_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_org_controls_org_id', 'org_controls', ['org_id'])

    # Evidence items
    op.create_table('evidence_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_control_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_key', sa.String(500), nullable=True),
        sa.Column('file_name', sa.String(300), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('file_type', sa.String(100), nullable=True),
        sa.Column('checksum_sha256', sa.String(64), nullable=True),
        sa.Column('scan_status', sa.Enum('pending','clean','infected','error', name='scanstatus'), nullable=False, server_default='pending'),
        sa.Column('source', sa.Enum('upload','link','manual', name='evidencesource'), nullable=False, server_default='upload'),
        sa.Column('status', sa.Enum('draft','client_submitted','msp_pending','msp_approved','msp_flagged','eva_pending','accepted','rejected','needs_more','not_applicable', name='evidencestatus'), nullable=False, server_default='draft'),
        sa.Column('msp_pre_status', sa.String(50), nullable=True),
        sa.Column('msp_reviewer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('msp_reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('collected_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('frequency', sa.Enum('once','monthly','quarterly','semi_annual','annual','continuous', name='evidencefrequency'), nullable=False, server_default='once'),
        sa.Column('expires_at', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['org_control_id'], ['org_controls.id']),
        sa.ForeignKeyConstraint(['org_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_evidence_items_org_id', 'evidence_items', ['org_id'])


def downgrade() -> None:
    op.drop_table('evidence_items')
    op.drop_table('org_controls')
    op.drop_table('controls')
    op.drop_table('frameworks')
    op.drop_table('users')
    op.drop_table('tenants')
