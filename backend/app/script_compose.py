"""Shared composer for conversational, teleprompter-friendly recording scripts.

Builds a beginner-friendly narration from whatever a control exposes — plain
language, best practices and expected evidence when present, otherwise the
control's own requirement text and discussion. Jargon and standards boilerplate
(e.g. "[Assignment: organization-defined ...]", lettered a./b./c. lists) are
humanized so the script reads smoothly out loud. EN and FR are faithful mirrors.

Used by seed_scripts_all. No signature change: compose(control, lang) reads the
control's fields directly, so it works across every framework.
"""
import re

DOMAIN_FR = {
    "access control": "contrôle d'accès",
    "awareness and training": "sensibilisation et formation",
    "audit and accountability": "audit et responsabilisation",
    "assessment, authorization, and monitoring": "évaluation, autorisation et surveillance",
    "configuration management": "gestion des configurations",
    "contingency planning": "planification des mesures d'urgence",
    "identification and authentication": "identification et authentification",
    "incident response": "réponse aux incidents",
    "maintenance": "maintenance",
    "media protection": "protection des supports",
    "personnel security": "sécurité du personnel",
    "physical protection": "protection physique",
    "physical and environmental protection": "protection physique et environnementale",
    "planning": "planification",
    "program management": "gestion du programme",
    "pii processing and transparency": "traitement des RP et transparence",
    "risk assessment": "évaluation des risques",
    "security assessment": "évaluation de la sécurité",
    "security assessment and monitoring": "évaluation et surveillance de la sécurité",
    "system and communications protection": "protection des systèmes et des communications",
    "system and information integrity": "intégrité des systèmes et de l'information",
    "system and services acquisition": "acquisition de systèmes et de services",
    "supply chain risk management": "gestion des risques de la chaîne d'approvisionnement",
    "malware defences": "défense contre les maliciels",
    "patch management": "gestion des correctifs",
    "data backup & recovery": "sauvegarde et récupération des données",
    "data recovery": "récupération des données",
    "mobile security": "sécurité mobile",
    "network security": "sécurité réseau",
    "cloud & outsourcing": "infonuagique et impartition",
    "web security": "sécurité web",
    "application security": "sécurité applicative",
    "vulnerability management": "gestion des vulnérabilités",
    "organizational": "contrôles organisationnels",
    "data protection": "protection des données",
}


# ── helpers ───────────────────────────────────────────────────────────────────
def _lines(val):
    if not val:
        return []
    return [re.sub(r"\s+", " ", l).strip(" -•\t") for l in str(val).split("\n") if l.strip()]


def _lower1(s):
    return s[:1].lower() + s[1:] if s else s


def _humanize_en(text):
    """Make standards text speakable: drop bracketed placeholders and labels."""
    if not text:
        return ""
    t = str(text)
    t = re.sub(r"\[Assignment:[^\]]*\]", "the values your organization defines", t, flags=re.I)
    t = re.sub(r"\[Selection[^\]]*\]", "an approved option", t, flags=re.I)
    t = re.sub(r"\[[^\]]*\]", "", t)            # any remaining brackets
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _humanize_fr(text):
    if not text:
        return ""
    t = str(text)
    t = re.sub(r"\[Assignment:[^\]]*\]", "les valeurs définies par votre organisation", t, flags=re.I)
    t = re.sub(r"\[Affectation[ :][^\]]*\]", "les valeurs définies par votre organisation", t, flags=re.I)
    t = re.sub(r"\[(Selection|Sélection)[^\]]*\]", "une option approuvée", t, flags=re.I)
    t = re.sub(r"\[[^\]]*\]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


# Abbreviations whose internal periods must NOT be treated as sentence ends.
_ABBR = re.compile(
    r"(i\.e|e\.g|etc|cf|vs|approx|incl|no|al|fig|art|min|max|"
    r"p\.\s?ex|c\.-?à-?d|c\.\s?-\s?à\s?-\s?d|réf|p\.\s?j)\.",
    re.I,
)
_SENT = re.compile(r"(?<=[.!?])\s+")


def _protect_abbr(t):
    return _ABBR.sub(lambda m: m.group(0).replace(".", ""), t)


def _restore_abbr(t):
    return t.replace("", ".")


def _sentences(t):
    """Sentence split that doesn't break on common abbreviations (i.e., c.-à-d., …)."""
    return [_restore_abbr(s).strip() for s in _SENT.split(_protect_abbr(t)) if s.strip()]


def _split_requirement(text):
    """Split a 'a. … b. … c. …' or numbered requirement into clean clauses."""
    if not text:
        return []
    t = re.sub(r"\s+", " ", str(text)).strip()
    # Split on lettered/numbered list markers like "a.", "b.", "1.", "(1)"
    parts = re.split(r"(?:^|\s)(?:[a-z]\.|\d{1,2}\.|\(\d{1,2}\))\s+", t)
    parts = [p.strip(" .;,") for p in parts if p and len(p.strip()) > 2]
    # If no list structure, fall back to (abbreviation-aware) sentences.
    if len(parts) <= 1:
        parts = [s for s in _sentences(t) if len(s) > 2]
    return parts


def _first_sentences(text, n=2, cap=420):
    if not text:
        return ""
    t = re.sub(r"\s+", " ", str(text)).strip()
    sents = _sentences(t)[:n]
    # Keep whole sentences: drop the last one(s) if the join is too long, rather
    # than cutting mid-sentence. Only hard-trim a single over-long sentence.
    while len(sents) > 1 and len(" ".join(sents)) > cap:
        sents = sents[:-1]
    out = " ".join(sents).strip()
    if len(out) > cap:
        out = out[:cap].rsplit(" ", 1)[0].rstrip(" ([«,;:") + "…"
    return out


def _join_en(items):
    items = [_lower1(i.rstrip(". ")) for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + ", and " + items[-1]


def _join_fr(items):
    items = [_lower1(i.rstrip(". ")) for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " et " + items[-1]


# ── English script ────────────────────────────────────────────────────────────
def _en(title, domain, kp, ev, plain, desc, disc):
    p = []
    # 1) What it is, in plain words
    if plain:
        plain_txt = plain.strip()
    else:
        clauses = _split_requirement(desc)
        plain_txt = _humanize_en(clauses[0]) if clauses else ""
        if len(plain_txt) > 240:
            plain_txt = plain_txt[:240].rsplit(" ", 1)[0] + "…"
    opener = (f"Let’s walk through the control “{title}”. It’s part of {domain}. "
              f"In plain language, here’s the idea: ")
    p.append(opener + (plain_txt or f"put “{_lower1(title)}” into practice in a deliberate, consistent way.").rstrip(".") + ".")

    # 2) Why it matters (use the standard's discussion when we have it)
    why = _humanize_en(_first_sentences(disc, 2, 300))
    if why:
        p.append("Why does it matter? " + why)
    else:
        p.append("Why does it matter? It directly strengthens how you protect your sensitive "
                 "information and lowers the chance of a costly mistake or breach.")

    # 3) What to actually do
    actions = list(kp)
    if not actions and desc:
        actions = [_humanize_en(a) for a in _split_requirement(desc)]
    actions = [a for a in actions if a][:5]
    if actions:
        more = " — and a few related steps" if len(_split_requirement(desc)) > 5 and not kp else ""
        p.append("So what do you actually do? In practice: " + _join_en(actions) + more + ".")
    else:
        p.append("So what do you actually do? Write the rule down, give someone clear "
                 "ownership of it, apply it the same way every time, and keep a record.")

    # 4) What an auditor wants to see
    ev_s = _join_en(ev)
    if ev_s:
        p.append("When you’re audited, an assessor will typically want to see " + ev_s + ".")
    else:
        p.append("When you’re audited, an assessor will typically want three things: a short "
                 "written policy or procedure, records or logs showing it actually happens, and a "
                 "recent date so it’s clearly still current.")

    # 5) Beginner tip
    p.append("New to this? Don’t overthink it. Get it written down, do the thing consistently, "
             "and keep dated proof — that covers most of what an auditor checks.")

    # 6) Takeaway
    p.append(f"Key takeaway: {title} — do it deliberately, apply it consistently, and keep the evidence.")
    return "\n\n".join(p)


# ── French script (faithful mirror) ────────────────────────────────────────────
def _fr(title, domain_fr, kp, ev, plain, desc, disc):
    p = []
    if plain:
        plain_txt = plain.strip()
    else:
        clauses = _split_requirement(desc)
        plain_txt = _humanize_fr(clauses[0]) if clauses else ""
        if len(plain_txt) > 240:
            plain_txt = plain_txt[:240].rsplit(" ", 1)[0] + "…"
    opener = (f"Voyons ensemble le contrôle « {title} ». Il fait partie du domaine {domain_fr}. "
              f"En clair, voici l’idée : ")
    p.append(opener + (plain_txt or f"mettre « {_lower1(title)} » en pratique de façon délibérée et constante.").rstrip(".") + ".")

    why = _humanize_fr(_first_sentences(disc, 2, 300))
    if why:
        p.append("Pourquoi est-ce important ? " + why)
    else:
        p.append("Pourquoi est-ce important ? Cela renforce directement la protection de vos "
                 "informations sensibles et réduit le risque d’erreur coûteuse ou de violation de données.")

    actions = list(kp)
    if not actions and desc:
        actions = [_humanize_fr(a) for a in _split_requirement(desc)]
    actions = [a for a in actions if a][:5]
    if actions:
        more = " — et quelques étapes connexes" if len(_split_requirement(desc)) > 5 and not kp else ""
        p.append("Concrètement, que faut-il faire ? En pratique : " + _join_fr(actions) + more + ".")
    else:
        p.append("Concrètement, que faut-il faire ? Mettez la règle par écrit, confiez-en la "
                 "responsabilité à quelqu’un, appliquez-la de la même façon chaque fois, et gardez une trace.")

    ev_s = _join_fr(ev)
    if ev_s:
        p.append("Lors d’un audit, un évaluateur voudra généralement voir " + ev_s + ".")
    else:
        p.append("Lors d’un audit, un évaluateur voudra généralement trois choses : une courte "
                 "politique ou procédure écrite, des registres ou journaux montrant que c’est réellement "
                 "appliqué, et une date récente prouvant que c’est toujours à jour.")

    p.append("Vous débutez ? Ne vous compliquez pas la vie. Mettez-le par écrit, faites-le de façon "
             "constante, et conservez une preuve datée — c’est l’essentiel de ce que vérifie un évaluateur.")

    p.append(f"À retenir : {title} — faites-le délibérément, appliquez-le de façon constante, "
             f"et conservez les preuves.")
    return "\n\n".join(p)


def _g(control, attr):
    return getattr(control, attr, None)


def _narrative_disc(disc):
    """Drop discussion fields that are really metadata (e.g. the CIS catalog's
    'Asset type: … · Security function: …'), which don't read as a 'why'."""
    d = (disc or "").strip()
    if d.lower().startswith(("asset type", "type d'actif", "type d’actif")):
        return ""
    return d


def compose(control, lang: str) -> str:
    domain = (control.domain or "security").strip() or "security"
    if lang == "fr":
        title_fr = (_g(control, "title_fr") or control.title or "").strip()
        kp = _lines(_g(control, "best_practices_fr"))
        ev = _lines(_g(control, "evidence_best_practices_fr"))
        plain = (_g(control, "plain_language_fr") or "").strip()
        # Fall back to English source text when no French value exists (e.g. NIST 800-53).
        desc = (_g(control, "description_fr") or _g(control, "description") or "")
        disc = _narrative_disc(_g(control, "discussion_fr") or _g(control, "discussion") or "")
        # Keep original case for unmapped domains (e.g. "CIS 1: …").
        dom_fr = DOMAIN_FR.get(domain.lower(), domain)
        return _fr(title_fr, dom_fr, kp, ev, plain, desc, disc)
    return _en(control.title, domain,
               _lines(control.best_practices), _lines(control.evidence_best_practices),
               (control.plain_language or ""), (control.description or ""),
               _narrative_disc(getattr(control, "discussion", "") or ""))
