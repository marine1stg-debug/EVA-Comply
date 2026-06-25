# -*- coding: utf-8 -*-
"""Email the subscription agreement to a tenant's admins once payment is
confirmed. Best-effort: logs and swallows errors (never blocks billing)."""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.agreement import AgreementAcceptance
from app.core.agreement_text import AGREEMENT_VERSION, account_type_for_tenant, build_html
from app.core.email import send_email

log = logging.getLogger("eva.agreement")

_ADMIN_ROLES = (UserRole.client_admin, UserRole.msp_admin, UserRole.super_admin)


def _full_html(doc: dict) -> bytes:
    page = (
        f"<html><head><meta charset='utf-8'><title>{doc['title']}</title>"
        f"<style>body{{font-family:Arial,Helvetica,sans-serif;max-width:820px;margin:28px auto;"
        f"line-height:1.55;color:#111;padding:0 16px}} h2{{margin-top:30px}} h3{{margin-top:18px}} "
        f"hr{{margin:34px 0;border:none;border-top:1px solid #ccc}} ul{{margin:6px 0 6px 18px}}</style>"
        f"</head><body>{doc['body_html']}</body></html>"
    )
    return page.encode("utf-8")


async def send_contract_email(db: AsyncSession, tenant) -> bool:
    """Send the agreement (HTML attachment + summary body) to the tenant's admins."""
    try:
        if tenant is None:
            return False
        at = account_type_for_tenant(tenant)
        doc = build_html(at)

        admins = (await db.execute(
            select(User).where(User.tenant_id == tenant.id, User.role.in_(_ADMIN_ROLES))
        )).scalars().all()
        recipients = [u.email for u in admins if u.email]
        if not recipients:
            return False

        acc = (await db.execute(
            select(AgreementAcceptance).where(
                AgreementAcceptance.tenant_id == tenant.id,
                AgreementAcceptance.version == AGREEMENT_VERSION,
            ).order_by(AgreementAcceptance.created_at.desc())
        )).scalars().first()
        accepted_line = ""
        if acc:
            when = acc.created_at.strftime("%Y-%m-%d %H:%M") if acc.created_at else ""
            accepted_line = (f"\nAccepté par : {acc.user_name} ({acc.user_role}) le {when} "
                             f"— IP {acc.ip_address}.")

        org = getattr(tenant, "name", "")
        subject = f"Votre contrat EVA Comply — {org} / Your EVA Comply agreement"
        body = (
            f"Bonjour,\n\nMerci — votre paiement pour EVA Comply est confirmé. "
            f"Vous trouverez ci-joint votre contrat d’abonnement et conditions d’utilisation "
            f"(version {doc['version']}, type de compte : {doc['label_fr']}).{accepted_line}\n\n"
            f"Conservez ce document pour vos dossiers.\n\n— L’équipe EVA Comply\n"
            f"------------------------------------------------------------\n"
            f"Hello,\n\nThank you — your EVA Comply payment is confirmed. Attached is your "
            f"subscription agreement and terms of use (version {doc['version']}, "
            f"account type: {doc['label_en']}). Please keep it for your records.\n\n— The EVA Comply team"
        )
        attachments = [("EVA_Comply_Agreement.html", _full_html(doc), "text/html")]
        ok = send_email(recipients, subject, body, sender="invoicing",
                        html=doc["body_html"], attachments=attachments)
        log.info("Contract email to %s (tenant %s): %s", recipients, org, "sent" if ok else "skipped")
        return ok
    except Exception as e:  # pragma: no cover - best effort
        log.warning("send_contract_email failed: %s", e)
        return False
