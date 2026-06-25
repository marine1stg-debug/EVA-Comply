# -*- coding: utf-8 -*-
"""Subscription Agreement & Terms of Use shown at registration.

Bilingual (FR then EN), modular by account type:
  - direct      : client contracts and is billed directly by EVA
  - msp         : MSP / partner that resells EVA to its own clients
  - msp_client  : client that uses EVA through an MSP

Single source of truth for both the in-app acceptance gate and the exported
Word document. NOT legal advice - bracketed [À COMPLÉTER] markers must be filled
and the text reviewed by counsel before production use.
"""

# Bump when the wording changes; acceptance is tracked per version.
AGREEMENT_VERSION = "1.0 (2026-06-08)"

ACCOUNT_TYPES = ("direct", "msp", "msp_client")

_TYPE_LABEL = {
    "direct":     ("Client direct", "Direct client"),
    "msp":        ("Partenaire / MSP", "Partner / MSP"),
    "msp_client": ("Client géré par un MSP", "MSP-managed client"),
}


def account_type_for(user, tenant) -> str:
    """Map a user + their tenant to an agreement variant."""
    role = getattr(user, "role", None)
    role = getattr(role, "value", role)
    if role in ("msp_admin", "msp_analyst"):
        return "msp"
    if getattr(tenant, "parent_msp_id", None):
        return "msp_client"
    return "direct"


def account_type_for_tenant(tenant) -> str:
    """Variant from a tenant alone (no user) - used for billing/email."""
    ttype = getattr(getattr(tenant, "tenant_type", None), "value", None)
    if ttype == "msp":
        return "msp"
    if getattr(tenant, "parent_msp_id", None):
        return "msp_client"
    return "direct"


# ── relationship clause (differs by account type) ─────────────────────────────
_REL_FR = {
    "direct": (
        "<p>Vous vous abonnez à EVA Comply <strong>directement auprès de l’Éditeur</strong>. "
        "L’Éditeur vous facture selon le forfait choisi. Aucun fournisseur de services gérés "
        "(MSP) n’intervient dans votre compte et n’a accès à vos données, sauf si vous l’y "
        "autorisez explicitement par écrit.</p>"
    ),
    "msp": (
        "<p>Vous adhérez à titre de <strong>partenaire / fournisseur de services gérés (MSP)</strong>. "
        "Vous pouvez créer et gérer des comptes clients, revendre l’accès à EVA Comply et percevoir "
        "une marge selon les modalités convenues avec l’Éditeur. À ce titre :</p>"
        "<ul>"
        "<li>vous demeurez responsable de la relation contractuelle et de la facturation avec vos "
        "propres clients, ainsi que du respect par ceux-ci des présentes conditions;</li>"
        "<li>vous n’accédez aux données d’un client que dans la mesure nécessaire à la prestation de "
        "vos services et selon l’autorisation du client (incluant la pré-révision des preuves);</li>"
        "<li>vous garantissez disposer de l’autorité requise pour agir au nom de vos clients dans "
        "l’application;</li>"
        "<li>l’Éditeur vous facture la portion de gros (wholesale) et n’est pas partie à votre entente "
        "commerciale avec vos clients.</li>"
        "</ul>"
    ),
    "msp_client": (
        "<p>Vous utilisez EVA Comply <strong>par l’intermédiaire d’un fournisseur de services gérés "
        "(MSP)</strong> qui gère votre abonnement et vous facture. Vous reconnaissez que :</p>"
        "<ul>"
        "<li>votre MSP peut consulter, réviser et gérer les données de conformité de votre "
        "organisation dans l’application (incluant la pré-révision de vos preuves) afin de vous "
        "fournir ses services;</li>"
        "<li>la facturation et le soutien de premier niveau sont assurés par votre MSP, et non par "
        "l’Éditeur, sauf indication contraire;</li>"
        "<li>vous demeurez propriétaire de vos données et pouvez en demander l’export ou la "
        "suppression conformément aux présentes;</li>"
        "<li>l’Éditeur héberge le service et applique les mesures de sécurité décrites ci-dessous.</li>"
        "</ul>"
    ),
}
_REL_EN = {
    "direct": (
        "<p>You subscribe to EVA Comply <strong>directly with the Publisher</strong>. The Publisher "
        "bills you according to the selected plan. No managed service provider (MSP) is involved in "
        "your account or has access to your data unless you expressly authorize it in writing.</p>"
    ),
    "msp": (
        "<p>You are enrolling as a <strong>partner / managed service provider (MSP)</strong>. You may "
        "create and manage client accounts, resell access to EVA Comply, and earn a margin under the "
        "terms agreed with the Publisher. Accordingly:</p>"
        "<ul>"
        "<li>you remain responsible for the contractual relationship and billing with your own "
        "clients, and for their compliance with these terms;</li>"
        "<li>you access a client’s data only as needed to deliver your services and as authorized by "
        "the client (including evidence pre-review);</li>"
        "<li>you warrant that you have the authority to act on behalf of your clients in the "
        "application;</li>"
        "<li>the Publisher bills you the wholesale portion and is not a party to your commercial "
        "agreement with your clients.</li>"
        "</ul>"
    ),
    "msp_client": (
        "<p>You use EVA Comply <strong>through a managed service provider (MSP)</strong> that manages "
        "your subscription and bills you. You acknowledge that:</p>"
        "<ul>"
        "<li>your MSP may view, review and manage your organization’s compliance data in the "
        "application (including pre-review of your evidence) to provide its services;</li>"
        "<li>billing and first-line support are provided by your MSP, not the Publisher, unless stated "
        "otherwise;</li>"
        "<li>you remain the owner of your data and may request its export or deletion under these "
        "terms;</li>"
        "<li>the Publisher hosts the service and applies the security measures described below.</li>"
        "</ul>"
    ),
}

# ── shared body (FR) ──────────────────────────────────────────────────────────
_FR_BODY = """
<h3>1. Définitions</h3>
<p><strong>« Éditeur »</strong> désigne [À COMPLÉTER : raison sociale d’EVA], fournisseur de la
plateforme EVA Comply. <strong>« Abonné »</strong> ou <strong>« vous »</strong> désigne
l’organisation qui accepte les présentes. <strong>« MSP »</strong> désigne un fournisseur de
services gérés partenaire. <strong>« Utilisateur autorisé »</strong> désigne une personne à qui
vous donnez accès. <strong>« Données client »</strong> désigne le contenu, les preuves et
renseignements que vous téléversez ou générez dans le service.</p>

<h3>2. Description du service</h3>
<p>EVA Comply est une plateforme infonuagique multilocataire de gestion de la conformité en
cybersécurité. Elle offre notamment : des catalogues de référentiels (CMMC 2.0 niveaux 1 et 2,
NIST SP 800-171 r3, ITSP.10.171/PCCC), le suivi des contrôles, un dépôt de preuves, l’auto-évaluation
de maturité, des recommandations, des rapports, des vidéos et scripts de formation, un marché de
fournisseurs de services, et la facturation par abonnement. Le service est fourni « tel quel » et
peut évoluer.</p>

<h3>3. Relation entre les parties</h3>
{relationship}

<h3>4. Abonnement, prix et facturation</h3>
<p>L’accès est offert par abonnement selon le forfait choisi. Sauf indication contraire, les
abonnements se <strong>renouvellent automatiquement</strong> à échéance. Les prix, taxes applicables
et modalités de paiement sont ceux affichés au moment de la souscription [À COMPLÉTER : politique de
prix/renouvellement/remboursement]. En cas de non-paiement, l’accès peut être suspendu après préavis.</p>

<h3>5. Propriété et gouvernance des données</h3>
<p>Vous demeurez <strong>propriétaire de vos Données client</strong>. L’Éditeur agit comme
dépositaire / sous-traitant et ne traite vos données que pour fournir et améliorer le service. Mesures :
chiffrement en transit et au repos, sauvegardes, contrôle d’accès, et journalisation. À la résiliation,
vous disposez d’une fenêtre de [À COMPLÉTER : durée] pour exporter vos données, après quoi elles peuvent
être supprimées. L’hébergement est situé à [À COMPLÉTER : région d’hébergement].</p>

<h3>6. Protection des renseignements personnels</h3>
<p>L’Éditeur traite les renseignements personnels conformément à la <strong>Loi 25 (Québec)</strong>,
à la <em>LPRPDE</em> et, le cas échéant, au <em>RGPD</em>. Le responsable de la protection des
renseignements personnels est [À COMPLÉTER : nom/coordonnées]. Le consentement aux présentes est
consigné (utilisateur, rôle, version, date et adresse IP).</p>

<h3>7. Avertissements importants</h3>
<p>EVA Comply est un <strong>outil d’aide à la conformité</strong>. Il <strong>ne garantit ni la
certification ni la conformité réglementaire</strong>, ne remplace pas un audit indépendant, et ne
constitue pas un avis juridique. L’utilisation du service ne garantit pas la réussite d’un audit ou
d’une certification (p. ex. CMMC).</p>

<h3>8. Propriété intellectuelle</h3>
<p>L’Éditeur conserve tous les droits sur la plateforme, ses catalogues, modèles et contenus. Vous
conservez les droits sur vos Données client. Aucune licence n’est accordée au-delà de l’usage du
service prévu aux présentes.</p>

<h3>9. Obligations de l’Abonné</h3>
<p>Vous vous engagez à : utiliser le service de façon licite; sécuriser les comptes (notamment par
l’authentification multifacteur); ne pas tenter de contourner les mesures de sécurité; et veiller à
l’exactitude des renseignements fournis.</p>

<h3>10. Garanties, responsabilité et indemnisation</h3>
<p>Dans la mesure permise par la loi, le service est fourni sans garantie implicite. La responsabilité
de l’Éditeur est limitée à [À COMPLÉTER : plafond, p. ex. les sommes payées au cours des 12 derniers
mois]. Vous indemnisez l’Éditeur contre les réclamations découlant de votre usage non conforme du
service.</p>

<h3>11. Disponibilité et soutien</h3>
<p>L’Éditeur déploie des efforts raisonnables pour assurer la disponibilité du service [À COMPLÉTER :
SLA, fenêtres de maintenance, canaux de soutien].</p>

<h3>12. Durée, suspension et résiliation</h3>
<p>Les présentes s’appliquent tant que vous utilisez le service. Chaque partie peut résilier selon
[À COMPLÉTER : préavis]. L’Éditeur peut suspendre l’accès en cas de violation ou de non-paiement. La
résiliation déclenche la fenêtre d’export prévue à l’article 5.</p>

<h3>13. Modifications</h3>
<p>L’Éditeur peut mettre à jour les présentes; les changements importants vous seront présentés et une
nouvelle acceptation pourra être exigée.</p>

<h3>14. Droit applicable</h3>
<p>Les présentes sont régies par les lois de la province de <strong>Québec</strong> et du Canada. Les
tribunaux du district de [À COMPLÉTER] ont compétence exclusive.</p>
"""

# ── shared body (EN) ──────────────────────────────────────────────────────────
_EN_BODY = """
<h3>1. Definitions</h3>
<p><strong>“Publisher”</strong> means [À COMPLÉTER: EVA legal name], provider of the EVA Comply
platform. <strong>“Subscriber”</strong> or <strong>“you”</strong> means the organization accepting
these terms. <strong>“MSP”</strong> means a partner managed service provider. <strong>“Authorized
User”</strong> means a person you grant access to. <strong>“Client Data”</strong> means the content,
evidence and information you upload or generate in the service.</p>

<h3>2. Description of the service</h3>
<p>EVA Comply is a multi-tenant cloud platform for cybersecurity compliance management. It provides,
among other things: framework catalogs (CMMC 2.0 Levels 1 and 2, NIST SP 800-171 r3,
ITSP.10.171/CPCSC), control tracking, an evidence repository, maturity self-assessment,
recommendations, reports, training videos and scripts, a service-provider marketplace, and
subscription billing. The service is provided “as is” and may evolve.</p>

<h3>3. Relationship between the parties</h3>
{relationship}

<h3>4. Subscription, pricing and billing</h3>
<p>Access is offered by subscription based on the selected plan. Unless stated otherwise, subscriptions
<strong>renew automatically</strong> at term. Prices, applicable taxes and payment terms are those
shown at purchase [À COMPLÉTER: pricing/renewal/refund policy]. On non-payment, access may be
suspended after notice.</p>

<h3>5. Data ownership and governance</h3>
<p>You remain the <strong>owner of your Client Data</strong>. The Publisher acts as
custodian / processor and processes your data only to provide and improve the service. Measures:
encryption in transit and at rest, backups, access control, and logging. On termination you have a
window of [À COMPLÉTER: duration] to export your data, after which it may be deleted. Hosting is
located in [À COMPLÉTER: hosting region].</p>

<h3>6. Privacy</h3>
<p>The Publisher processes personal information in accordance with <strong>Quebec’s Law 25</strong>,
<em>PIPEDA</em> and, where applicable, the <em>GDPR</em>. The privacy officer is
[À COMPLÉTER: name/contact]. Consent to these terms is recorded (user, role, version, date and IP
address).</p>

<h3>7. Important disclaimers</h3>
<p>EVA Comply is a <strong>compliance-support tool</strong>. It <strong>does not guarantee
certification or regulatory compliance</strong>, does not replace an independent audit, and does not
constitute legal advice. Use of the service does not guarantee passing any audit or certification
(e.g. CMMC).</p>

<h3>8. Intellectual property</h3>
<p>The Publisher retains all rights in the platform, its catalogs, templates and content. You retain
rights in your Client Data. No license is granted beyond the use of the service contemplated here.</p>

<h3>9. Subscriber obligations</h3>
<p>You agree to: use the service lawfully; secure accounts (including multi-factor authentication);
not attempt to bypass security measures; and keep the information you provide accurate.</p>

<h3>10. Warranties, liability and indemnity</h3>
<p>To the extent permitted by law, the service is provided without implied warranties. The Publisher’s
liability is limited to [À COMPLÉTER: cap, e.g. amounts paid in the prior 12 months]. You indemnify
the Publisher against claims arising from your non-compliant use of the service.</p>

<h3>11. Availability and support</h3>
<p>The Publisher uses reasonable efforts to keep the service available [À COMPLÉTER: SLA, maintenance
windows, support channels].</p>

<h3>12. Term, suspension and termination</h3>
<p>These terms apply while you use the service. Either party may terminate per [À COMPLÉTER: notice].
The Publisher may suspend access on breach or non-payment. Termination starts the export window in
section 5.</p>

<h3>13. Changes</h3>
<p>The Publisher may update these terms; material changes will be presented to you and renewed
acceptance may be required.</p>

<h3>14. Governing law</h3>
<p>These terms are governed by the laws of the Province of <strong>Quebec</strong> and Canada. The
courts of the district of [À COMPLÉTER] have exclusive jurisdiction.</p>
"""

_DISCLAIMER_FR = ("<p style='font-style:italic'>Ce document est un modèle fourni à titre informatif "
                  "et ne constitue pas un avis juridique. Faites-le réviser par un conseiller "
                  "juridique avant toute utilisation en production.</p>")
_DISCLAIMER_EN = ("<p style='font-style:italic'>This document is a template provided for information "
                  "only and is not legal advice. Have it reviewed by legal counsel before any "
                  "production use.</p>")


def build_html(account_type: str) -> dict:
    """Return {version, title, account_type, label, body_html} for an account type."""
    at = account_type if account_type in ACCOUNT_TYPES else "direct"
    fr_label, en_label = _TYPE_LABEL[at]
    fr = _FR_BODY.format(relationship=_REL_FR[at])
    en = _EN_BODY.format(relationship=_REL_EN[at])
    body = (
        f"<div class='agreement'>"
        f"<h2>VERSION FRANÇAISE</h2>"
        f"<p><strong>Contrat d’abonnement et conditions d’utilisation - EVA Comply</strong><br>"
        f"Type de compte : {fr_label} · Version : {AGREEMENT_VERSION}</p>"
        f"{_DISCLAIMER_FR}{fr}"
        f"<hr><h2>ENGLISH VERSION</h2>"
        f"<p><strong>Subscription Agreement & Terms of Use - EVA Comply</strong><br>"
        f"Account type: {en_label} · Version: {AGREEMENT_VERSION}</p>"
        f"{_DISCLAIMER_EN}{en}"
        f"</div>"
    )
    return {
        "version": AGREEMENT_VERSION,
        "account_type": at,
        "label_fr": fr_label,
        "label_en": en_label,
        "title": "Contrat d’abonnement et conditions d’utilisation - EVA Comply",
        "body_html": body,
    }
