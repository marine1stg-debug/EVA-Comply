"""Maturity self-assessment question generation.

v1: one deterministic 5-rung ladder question per control, derived from the
control itself. The ladder (None→Optimized) maps 1:1 onto the 0–5 maturity
radar. Authored bespoke question sets (and an XLS override column) will later
take precedence over the generated default for specific controls; the
`question_key` keeps client answers stable across that change.
"""

# Shared maturity ladder. level → (short label, generic statement, short_fr, statement_fr).
LADDER = [
    (5, "Optimized",  "Formal, organization-wide, and continuously improved, fully implemented across all systems and reviewed regularly.",
        "Optimisé", "Formel, à l’échelle de l’organisation et amélioré en continu; entièrement mis en œuvre sur tous les systèmes et révisé régulièrement."),
    (4, "Managed",    "Implemented and monitored for critical systems; nearly complete, with minor gaps.",
        "Géré", "Mis en œuvre et surveillé pour les systèmes critiques; presque complet, avec des lacunes mineures."),
    (3, "Defined",    "Documented and applied consistently for key systems and areas.",
        "Défini", "Documenté et appliqué de façon cohérente pour les systèmes et les domaines clés."),
    (2, "Initial",    "Informal or ad-hoc; partial and inconsistent coverage.",
        "Initial", "Informel ou ponctuel; couverture partielle et incohérente."),
    (1, "None",       "No process or capability in place for this control.",
        "Aucun", "Aucun processus ni aucune capacité en place pour ce contrôle."),
]


def generate_questions(control) -> list[dict]:
    """Return the self-assessment question(s) for a control.

    If the control carries authored, control-specific questions
    (control.maturity_questions), those win. Otherwise fall back to a single
    generic bilingual ladder question. Shape is a list so multiple questions
    are supported."""
    authored = getattr(control, "maturity_questions", None)
    if isinstance(authored, list) and authored:
        return authored
    topic = (control.title or "this control").strip()
    topic_fr = (getattr(control, "title_fr", None) or topic).strip()
    return [{
        "key": "default",
        "prompt": f"How would you rate your maturity for: {topic}",
        "prompt_fr": f"Comment évalueriez-vous votre maturité pour : {topic_fr}",
        "options": [
            {"key": f"l{level}", "level": level, "short": short, "label": text,
             "short_fr": short_fr, "label_fr": text_fr}
            for (level, short, text, short_fr, text_fr) in LADDER
        ],
    }]


def perceived_level(answers: dict) -> float | None:
    """Mean of answered question levels (1–5), or None if nothing answered."""
    if not answers:
        return None
    vals = [v for v in answers.values() if isinstance(v, (int, float)) and v]
    if not vals:
        return None
    return round(sum(vals) / len(vals), 2)
