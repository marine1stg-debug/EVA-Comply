"""Seed control-specific maturity self-assessment questions.

Expert-authored, control-specific 5-rung ladder questions for the full NIST
SP 800-171r3 catalog (one question per control, keyed by ref). Each sets
controls.maturity_questions, which overrides the generic generated ladder for
that control. Controls without an entry keep the generic question.

SAFE: only sets the maturity_questions column on matched controls; touches
nothing else. Re-runnable (idempotent).

USAGE (inside the api container):
    docker compose exec api python -m app.seed_maturity_questions          # dry run
    docker compose exec api python -m app.seed_maturity_questions --yes
"""
import argparse
import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models import framework, evidence  # noqa: F401 - register mappers
from app.models.framework import Control
from app.maturity_banks import NIST_171R3
try:
    from app.maturity_banks_fr import NIST_171R3_FR  # ref -> (prompt_fr, [s5..s1])
except Exception:  # FR bank optional / may be partial
    NIST_171R3_FR = {}

_SHORT = {5: "Optimized", 4: "Managed", 3: "Defined", 2: "Initial", 1: "None"}
_SHORT_FR = {5: "Optimisé", 4: "Géré", 3: "Défini", 2: "Initial", 1: "Aucun"}


def bank(prompt: str, statements: list[str], fr: tuple | None = None) -> list[dict]:
    """statements: 5 entries, highest maturity (5) first → lowest (1) last.
    fr (optional): (prompt_fr, [s5_fr..s1_fr]) - adds prompt_fr / short_fr / label_fr."""
    prompt_fr, statements_fr = (fr or (None, []))
    opts = []
    for i, text in enumerate(statements):
        level = 5 - i
        o = {"key": f"l{level}", "level": level, "short": _SHORT[level], "label": text}
        if statements_fr and i < len(statements_fr):
            o["short_fr"] = _SHORT_FR[level]
            o["label_fr"] = statements_fr[i]
        opts.append(o)
    q = {"key": "default", "prompt": prompt, "options": opts}
    if prompt_fr:
        q["prompt_fr"] = prompt_fr
    return [q]


# Build the full ref → question-set map from the authored bank (+ FR when present).
QUESTIONS: dict[str, list[dict]] = {
    ref: bank(prompt, statements, NIST_171R3_FR.get(ref))
    for ref, (prompt, statements) in NIST_171R3.items()
}

# CMMC 2.0 L1/L2 practice IDs embed the 800-171 (r2) number, e.g.
# "AC.L2-3.1.1" → 3.1.1. We reuse the authored NIST (r3) bank: direct-pad the
# r2 number to the r3 ref (3.1.1 → 03.01.01), with this redirect table for the
# r2 practices that r3 consolidated/renumbered (mapped to the nearest topical
# r3 question). Practices with no good match fall back to the generic ladder.
CMMC_REDIRECT: dict[str, str] = {
    "3.1.13": "03.01.12", "3.1.14": "03.01.12", "3.1.15": "03.01.07",
    "3.1.17": "03.01.16", "3.1.19": "03.01.18", "3.1.21": "03.08.07",
    "3.2.3": "03.02.01",
    "3.3.9": "03.03.08",
    "3.4.7": "03.04.06", "3.4.9": "03.04.08",
    "3.5.6": "03.05.05", "3.5.8": "03.05.07", "3.5.9": "03.05.07", "3.5.10": "03.05.07",
    "3.7.2": "03.07.04", "3.7.3": "03.08.03",
    "3.8.6": "03.08.05", "3.8.8": "03.08.07",
    "3.10.3": "03.10.07", "3.10.4": "03.10.07", "3.10.5": "03.10.07",
    "3.11.3": "03.11.04",
    "3.12.4": "03.15.02",
    "3.13.2": "03.16.01", "3.13.3": "03.13.01", "3.13.5": "03.13.01",
    "3.13.7": "03.01.12", "3.13.14": "03.13.12", "3.13.16": "03.13.08",
    "3.14.4": "03.14.02", "3.14.5": "03.14.02", "3.14.7": "03.14.06",
}


def r3_for_cmmc(ref: str):
    """Map a CMMC practice ref (e.g. 'AC.L2-3.1.1') to an r3 bank ref, or None."""
    if "-" not in ref:
        return None
    tail = ref.split("-", 1)[1].strip()          # '3.1.1'
    if tail in CMMC_REDIRECT:
        return CMMC_REDIRECT[tail]
    parts = tail.split(".")
    if len(parts) != 3 or parts[0] != "3":
        return None
    try:
        return f"03.{int(parts[1]):02d}.{int(parts[2]):02d}"
    except ValueError:
        return None


async def run(commit: bool):
    """Apply authored questions to EVERY control whose ref matches (across all
    frameworks - NIST 800-171r3, ITSP.10.171, etc., which share the 03.xx.xx
    IDs). Reports coverage per framework and lists controls still on the generic
    ladder so any framework-specific gaps are visible."""
    from app.models.framework import Framework
    async with AsyncSessionLocal() as db:
        print(f"Mode: {'COMMIT' if commit else 'DRY RUN'}\n")
        fw_name = {f.id: f.name for f in (await db.execute(select(Framework))).scalars().all()}
        controls = (await db.execute(select(Control))).scalars().all()

        applied = 0
        by_fw: dict = {}
        for c in controls:
            qs = QUESTIONS.get(c.ref)
            if not qs:
                r3 = r3_for_cmmc(c.ref)   # CMMC practice → reuse the r3 bank
                if r3:
                    qs = QUESTIONS.get(r3)
            stat = by_fw.setdefault(c.framework_id, {"total": 0, "authored": 0, "generic": []})
            stat["total"] += 1
            if qs:
                stat["authored"] += 1
                applied += 1
                if commit:
                    c.maturity_questions = qs
            else:
                stat["generic"].append(c.ref)

        for fid, s in sorted(by_fw.items(), key=lambda kv: fw_name.get(kv[0], "")):
            name = fw_name.get(fid, str(fid))
            print(f"{name}: {s['authored']}/{s['total']} controls authored, "
                  f"{len(s['generic'])} on generic ladder")
            if s["generic"]:
                print(f"    generic: {', '.join(sorted(s['generic']))}")

        print(f"\nApplied authored questions to {applied} control rows.")
        if commit:
            await db.commit()
            print("Committed. Every other control keeps the generic ladder.")
        else:
            print("Dry run only - re-run with --yes to apply.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="write the question sets")
    args = ap.parse_args()
    asyncio.run(run(args.yes))
