"""Create policies table and seed from the built-in policy library.

Replaces the hardcoded _FAMILY_POLICY mapping with an admin-managed registry:
each policy carries a category (control family), keywords used to match a
control's domain, an Available flag, and a file reference (built-in .docx).

Revision ID: 036
Revises: 035
Create Date: 2026-06-23
"""
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from alembic import op

revision = '036'
down_revision = '035'
branch_labels = None
depends_on = None

# (name, name_fr, category, category_fr, keywords, slug)
SEED = [
    ("Access Control Policy","Politique de contrôle d'accès","Access Control","Contrôle d'accès","access,control","Access_Control_Policy"),
    ("Audit & Accountability Policy","Politique d'audit et de responsabilisation","Audit & Accountability","Audit et responsabilisation","audit","Audit_Accountability_Policy"),
    ("Configuration Management Policy","Politique de gestion de la configuration","Configuration Management","Gestion de la configuration","configuration","Configuration_Management_Policy"),
    ("Identification & Authentication Policy","Politique d'identification et d'authentification","Identification & Authentication","Identification et authentification","identification","Identification_Authentication_Policy"),
    ("Incident Response Policy & Plan","Politique et plan de réponse aux incidents","Incident Response","Réponse aux incidents","incident","Incident_Response_Policy_Plan"),
    ("System Maintenance Policy","Politique de maintenance des systèmes","Maintenance","Maintenance","maintenance","System_Maintenance_Policy"),
    ("Media Protection Policy","Politique de protection des supports","Media Protection","Protection des supports","media","Media_Protection_Policy"),
    ("Personnel Security Policy","Politique de sécurité du personnel","Personnel Security","Sécurité du personnel","personnel","Personnel_Security_Policy"),
    ("Physical Protection Policy","Politique de protection physique","Physical Protection","Protection physique","physical","Physical_Protection_Policy"),
    ("Risk Assessment Policy","Politique d'évaluation des risques","Risk Assessment","Évaluation des risques","risk,assessment","Risk_Assessment_Policy"),
    ("Security Assessment & Continuous Monitoring Policy","Politique d'évaluation de la sécurité et de surveillance continue","Security Assessment","Évaluation de la sécurité","security,assessment","Security_Assessment_Continuous_Monitoring_Policy"),
    ("Security Awareness & Training Policy","Politique de sensibilisation et de formation en sécurité","Awareness & Training","Sensibilisation et formation","awareness","Security_Awareness_Training_Policy"),
    ("System & Communications Protection Policy","Politique de protection des systèmes et des communications","System & Communications Protection","Protection des systèmes et des communications","communications","System_Communications_Protection_Policy"),
    ("System & Information Integrity Policy","Politique d'intégrité des systèmes et de l'information","System & Information Integrity","Intégrité des systèmes et de l'information","information,integrity","System_Information_Integrity_Policy"),
    ("Information Security Program Plan (SSP)","Plan du programme de sécurité de l'information (SSP)","Planning (SSP)","Planification (SSP)","planning","Information_Security_Program_Plan_SSP"),
    ("System & Services Acquisition Policy","Politique d'acquisition des systèmes et des services","System & Services Acquisition","Acquisition des systèmes et des services","services,acquisition","System_Services_Acquisition_Policy"),
    ("Supply Chain Risk Management Policy","Politique de gestion des risques liés à la chaîne d'approvisionnement","Supply Chain Risk Management","Gestion des risques de la chaîne d'approvisionnement","supply,chain","Supply_Chain_Risk_Management_Policy"),
    ("Information Security Policy","Politique de sécurité de l'information","General","Général","","Information_Security_Policy"),
]


def upgrade() -> None:
    t = op.create_table(
        'policies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('name_fr', sa.String(300), nullable=True),
        sa.Column('category', sa.String(120), nullable=False, server_default='General'),
        sa.Column('category_fr', sa.String(120), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('description_fr', sa.Text(), nullable=True),
        sa.Column('keywords', sa.String(300), nullable=False, server_default=''),
        sa.Column('slug', sa.String(200), nullable=False),
        sa.Column('source', sa.String(10), nullable=False, server_default='builtin'),
        sa.Column('has_fr', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    import uuid as _uuid
    rows = []
    for i, (name, name_fr, cat, cat_fr, kw, slug) in enumerate(SEED):
        rows.append({
            "id": _uuid.uuid4(), "name": name, "name_fr": name_fr,
            "category": cat, "category_fr": cat_fr, "keywords": kw, "slug": slug,
            "source": "builtin", "has_fr": True, "is_active": True, "sort_order": i,
        })
    op.bulk_insert(t, rows)


def downgrade() -> None:
    op.drop_table('policies')
