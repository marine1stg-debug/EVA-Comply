"""Recommendations engine — turn maturity gaps into remediation actions.

A control is "gapped" when its current maturity (the client's self-assessment
level, else a status-derived proxy) sits below its target. For each gapped
control we generate one or more recommendations, from either:

  - the curated pre-made library (``app.recommendation_banks``), keyed by control
    ref and reused for ITSP / CMMC; falls back to a recommendation derived from
    the control's maturity ladder so coverage is universal; or
  - a one-click LLM analysis of the client's self-assessment answers + comment
    (uses the configured connector via ``app.core.llm.chat``).

effort/impact ∈ {low, medium, high}. Quick win = low effort + high impact.
"""
from __future__ import annotations

import json
import re

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.framework import Control
from app.models.evidence import OrgControl
from app.models.maturity import MaturityAssessment
from app.models.self_assessment import SelfAssessment
from app.core.maturity_questions import perceived_level
from app.core.llm import chat, LlmError, LlmSettings
from app.recommendation_banks import NIST_171R3_RECS
from app.seed_maturity_questions import r3_for_cmmc

DEFAULT_TARGET = 4
EFFORT_W = {"low": 1, "medium": 2, "high": 3}
IMPACT_W = {"low": 1, "medium": 2, "high": 3}
RISK_W = {"informational": 1, "low": 1, "medium": 2, "high": 3, "critical": 4}
_STATUS_LEVEL = {"compliant": 5, "in_progress": 3, "non_compliant": 1}
_ALLOWED = {"low", "medium", "high"}


def _risk_value(r) -> str:
    return r.value if hasattr(r, "value") else (r or "low")


def is_quick_win(effort: str, impact: str) -> bool:
    return effort == "low" and impact == "high"


def priority_score(effort: str, impact: str, gap: int | None, risk: str) -> int:
    """Higher = address sooner. Impact × gap × control risk, lightly de-weighted
    by effort so cheap high-value items rank above expensive ones."""
    base = IMPACT_W.get(impact, 2) * max(1, gap or 1) * RISK_W.get(risk, 2)
    return round(base * (1.15 if effort == "low" else 1.0 if effort == "medium" else 0.85), 2)


def _control_level(perceived: float | None, audit_status: str | None) -> int | None:
    """Client's current maturity for a control. Self-assessment wins; otherwise
    a coarse proxy from audit status. Returns None when not applicable."""
    if perceived is not None:
        return int(round(perceived))
    st = (audit_status or "").lower()
    if st == "not_applicable":
        return None
    return _STATUS_LEVEL.get(st, 1)


def _fill_effort_impact(rec: dict, gap: int, risk: str) -> dict:
    if rec.get("impact") not in _ALLOWED:
        rec["impact"] = "high" if risk in ("high", "critical") else ("medium" if risk == "medium" else "low")
    if rec.get("effort") not in _ALLOWED:
        rec["effort"] = "high" if gap >= 3 else ("medium" if gap == 2 else "low")
    return rec


def _derive_from_ladder(control: Control, target: int) -> dict | None:
    """Build a recommendation from the control's maturity ladder: aim for the
    statement at the target level."""
    qs = control.maturity_questions
    if not qs:
        return None
    opts = (qs[0] or {}).get("options", []) if isinstance(qs, list) else []
    if not opts:
        return None
    tgt = next((o for o in opts if o.get("level") == target), None) or opts[0]
    label = tgt.get("label", "").strip()
    if not label:
        return None
    short = tgt.get("short", "target")
    # Use the ladder's French label/short when present, else fall back to EN.
    short_fr = tgt.get("short_fr", short)
    label_fr = (tgt.get("label_fr") or label).strip()
    return {
        "title": f"Advance to '{short}' maturity",
        "text": f"To close the gap on {control.ref}, work toward: {label}",
        "title_fr": f"Atteindre le niveau de maturité « {short_fr} »",
        "text_fr": f"Pour combler l'écart sur {control.ref}, visez : {label_fr}",
        "effort": None, "impact": None,
    }


def premade_for_control(control: Control, gap: int, target: int = DEFAULT_TARGET) -> list[dict]:
    """Curated recommendations for a control, with ladder-derived fallback."""
    recs = NIST_171R3_RECS.get(control.ref)
    if not recs:
        r3 = r3_for_cmmc(control.ref)   # CMMC practice → reuse the r3 bank
        if r3:
            recs = NIST_171R3_RECS.get(r3)
    risk = _risk_value(control.risk_rating)
    if recs:
        return [_fill_effort_impact(dict(r), gap, risk) for r in recs]
    derived = _derive_from_ladder(control, target)
    if derived:
        return [_fill_effort_impact(derived, gap, risk)]
    return []


async def gather_gaps(db: AsyncSession, org_id) -> list[dict]:
    """Every control in the client's subscribed frameworks whose current maturity
    is below target. Subscription = frameworks the org has any OrgControl in; we
    then consider ALL controls of those frameworks (not only the ones already
    provisioned), so a brand-new client with everything Not Started still gets a
    recommendation per gapped control."""
    sub_fws = list((await db.execute(
        select(Control.framework_id)
        .join(OrgControl, OrgControl.control_id == Control.id)
        .where(OrgControl.org_id == org_id)
        .distinct()
    )).scalars().all())
    if not sub_fws:
        return []
    controls = (await db.execute(
        select(Control).where(Control.framework_id.in_(sub_fws)).order_by(Control.sort_order)
    )).scalars().all()
    oc_status = {
        oc.control_id: oc.audit_status
        for oc in (await db.execute(
            select(OrgControl).where(OrgControl.org_id == org_id)
        )).scalars().all()
    }
    rows = [(c, oc_status.get(c.id)) for c in controls]

    sa_map = {
        sa.control_id: sa
        for sa in (await db.execute(
            select(SelfAssessment).where(SelfAssessment.org_id == org_id)
        )).scalars().all()
    }
    # Domain target overrides, keyed (framework_id, domain).
    tgt_map = {
        (m.framework_id, m.domain): m.target_level
        for m in (await db.execute(
            select(MaturityAssessment).where(MaturityAssessment.org_id == org_id)
        )).scalars().all()
        if m.target_level is not None
    }

    gaps = []
    for control, audit_status in rows:
        sa = sa_map.get(control.id)
        perceived = perceived_level(sa.answers or {}) if sa else None
        current = _control_level(perceived, audit_status)
        if current is None:
            continue  # not applicable
        target = tgt_map.get((control.framework_id, control.domain or "General"), DEFAULT_TARGET)
        gap = target - current
        if gap <= 0:
            continue
        gaps.append({
            "control": control, "current": current, "target": target, "gap": gap,
            "perceived": perceived, "audit_status": audit_status,
            "sa_comment": (sa.comment if sa else None),
            "sa_answers": (sa.answers if sa else None),
        })
    # Biggest, riskiest gaps first.
    gaps.sort(key=lambda g: g["gap"] * RISK_W.get(_risk_value(g["control"].risk_rating), 2), reverse=True)
    return gaps


def _strip_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


async def ai_for_control(s: LlmSettings, gap: dict) -> dict:
    """One LLM call → a single recommendation dict for a gapped control.

    Raises LlmError on connection/parse failure (caller decides how to surface).
    """
    c: Control = gap["control"]
    answers = gap.get("sa_answers") or {}
    comment = (gap.get("sa_comment") or "").strip()
    guidance = (c.discussion or c.best_practices or c.description or "").strip()[:800]

    system = (
        "You are a cybersecurity compliance advisor. A client self-assessed their "
        "maturity on a control and scored below their target. Recommend the single "
        "most valuable remediation action to close the gap. Be concrete and specific "
        "to the control. Respond ONLY with a JSON object: "
        '{"title": str (<=80 chars), "text": str (2-4 sentences, actionable), '
        '"effort": "low"|"medium"|"high", "impact": "low"|"medium"|"high"}.'
    )
    user = (
        f"Control {c.ref}: {c.title}\n"
        f"Domain: {c.domain or 'General'}\n"
        f"Guidance: {guidance or '(none)'}\n"
        f"Client current maturity level: {gap['current']}/5; target: {gap['target']}/5.\n"
        f"Self-assessment answers: {json.dumps(answers)}\n"
        f"Client comment: {comment or '(none)'}\n"
        "Return the JSON recommendation now."
    )
    reply = await chat(s, [{"role": "system", "content": system},
                           {"role": "user", "content": user}], max_tokens=500)
    try:
        data = json.loads(_strip_json(reply))
    except (ValueError, TypeError):
        raise LlmError(f"Model did not return valid JSON for {c.ref}.")
    title = str(data.get("title") or f"Close the gap on {c.ref}").strip()[:300]
    text = str(data.get("text") or "").strip()
    if not text:
        raise LlmError(f"Model returned an empty recommendation for {c.ref}.")
    rec = {"title": title, "text": text,
           "effort": str(data.get("effort", "")).lower(),
           "impact": str(data.get("impact", "")).lower()}
    return _fill_effort_impact(rec, gap["gap"], _risk_value(c.risk_rating))
