"""Server-side localization for framework/control content.

English columns are the source of truth; *_fr columns are optional French
overrides. The frontend sends the chosen content language in the `X-Lang`
header. `loc()` returns French when asked and available, else English, so
nothing ever renders blank.
"""
from fastapi import Request


def get_lang(request: Request) -> str:
    raw = (request.headers.get("X-Lang")
           or request.query_params.get("lang")
           or request.headers.get("Accept-Language", "")
           or "en")
    return "fr" if str(raw).lower().startswith("fr") else "en"


def loc(obj, field: str, lang: str) -> str:
    base = getattr(obj, field, None) or ""
    if lang == "fr":
        fr = getattr(obj, field + "_fr", None)
        if fr:
            return fr
    return base


def has_fr(obj, field: str) -> bool:
    return bool(getattr(obj, field + "_fr", None))


def lines(text: str) -> list:
    return [ln.strip() for ln in (text or "").split("\n") if ln.strip()]


# Control-family (domain) labels → French. Matched case-insensitively;
# unknown domains pass through unchanged.
DOMAIN_FR = {
    "access control": "Contrôle d’accès",
    "audit & accountability": "Audit et responsabilisation",
    "audit and accountability": "Audit et responsabilisation",
    "awareness & training": "Sensibilisation et formation",
    "awareness and training": "Sensibilisation et formation",
    "configuration management": "Gestion des configurations",
    "config management": "Gestion des configurations",
    "identification & authentication": "Identification et authentification",
    "identification & auth": "Identification et authentification",
    "identification and authentication": "Identification et authentification",
    "incident response": "Réponse aux incidents",
    "maintenance": "Maintenance",
    "media protection": "Protection des supports",
    "personnel security": "Sécurité du personnel",
    "physical protection": "Protection physique",
    "planning": "Planification",
    "risk assessment": "Évaluation des risques",
    "security assessment": "Évaluation de la sécurité",
    "security assessment and monitoring": "Évaluation et surveillance de la sécurité",
    "security assessment & monitoring": "Évaluation et surveillance de la sécurité",
    "system & communications protection": "Protection des systèmes et des communications",
    "system and communications protection": "Protection des systèmes et des communications",
    "system & information integrity": "Intégrité des systèmes et de l’information",
    "system and information integrity": "Intégrité des systèmes et de l’information",
    "system integrity": "Intégrité des systèmes",
    "system & services acquisition": "Acquisition des systèmes et des services",
    "system and services acquisition": "Acquisition des systèmes et des services",
    "supply chain risk management": "Gestion des risques de la chaîne d’approvisionnement",
    # NIST SP 800-53 families
    "assessment, authorization, and monitoring": "Évaluation, autorisation et surveillance",
    "contingency planning": "Planification des mesures d’urgence",
    "program management": "Gestion du programme",
    "pii processing and transparency": "Traitement des RP et transparence",
    "physical and environmental protection": "Protection physique et environnementale",
    # CyberSecure Canada domains
    "patch management": "Gestion des correctifs",
    "malware defences": "Défense contre les maliciels",
    "malware defenses": "Défense contre les maliciels",
    "data backup & recovery": "Sauvegarde et récupération des données",
    "data recovery": "Récupération des données",
    "mobile security": "Sécurité mobile",
    "network security": "Sécurité réseau",
    "network monitoring": "Surveillance du réseau",
    "cloud & outsourcing": "Infonuagique et impartition",
    "web security": "Sécurité Web",
    "application security": "Sécurité applicative",
    "vulnerability management": "Gestion des vulnérabilités",
    "data protection": "Protection des données",
    "organizational": "Contrôles organisationnels",
    # CIS Controls v8.1 — control families
    "cis 1: inventory and control of enterprise assets": "CIS 1 : Inventaire et contrôle des actifs de l’entreprise",
    "cis 2: inventory and control of software assets": "CIS 2 : Inventaire et contrôle des actifs logiciels",
    "cis 3: data protection": "CIS 3 : Protection des données",
    "cis 4: secure configuration of enterprise assets and software": "CIS 4 : Configuration sécurisée des actifs et des logiciels",
    "cis 5: account management": "CIS 5 : Gestion des comptes",
    "cis 6: access control management": "CIS 6 : Gestion du contrôle d’accès",
    "cis 7: continuous vulnerability management": "CIS 7 : Gestion continue des vulnérabilités",
    "cis 8: audit log management": "CIS 8 : Gestion des journaux d’audit",
    "cis 9: email and web browser protections": "CIS 9 : Protections de la messagerie et des navigateurs Web",
    "cis 10: malware defenses": "CIS 10 : Défenses contre les maliciels",
    "cis 11: data recovery": "CIS 11 : Récupération des données",
    "cis 12: network infrastructure management": "CIS 12 : Gestion de l’infrastructure réseau",
    "cis 13: network monitoring and defense": "CIS 13 : Surveillance et défense du réseau",
    "cis 14: security awareness and skills training": "CIS 14 : Sensibilisation à la sécurité et formation",
    "cis 15: service provider management": "CIS 15 : Gestion des fournisseurs de services",
    "cis 16: application software security": "CIS 16 : Sécurité des logiciels applicatifs",
    "cis 17: incident response management": "CIS 17 : Gestion de la réponse aux incidents",
    "cis 18: penetration testing": "CIS 18 : Tests d’intrusion",
}


def loc_domain(domain: str, lang: str) -> str:
    if lang != "fr" or not domain:
        return domain or ""
    return DOMAIN_FR.get(domain.strip().lower(), domain)
