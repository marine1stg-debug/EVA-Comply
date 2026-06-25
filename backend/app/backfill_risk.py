"""Backfill expert risk ratings onto NIST 800-171r3 / ITSP.10.171 controls that
are already in the database (so you don't have to re-import the catalog).

Matches by control `ref` (03.xx.xx); CMMC controls already carry risk and are
untouched. Dry run by default - add --yes to commit.

USAGE (inside the api container):
    docker compose exec api python -m app.backfill_risk            # dry run
    docker compose exec api python -m app.backfill_risk --yes
"""
import argparse
import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models import evidence  # noqa: F401 - registers relationships
from app.models.framework import Control, ControlRisk

# Same map authored in the catalog build (NIST r3 IDs, reused by ITSP + 03.14.09).
RISK = {
    "03.01.01": "high", "03.01.02": "critical", "03.01.03": "high", "03.01.04": "medium",
    "03.01.05": "high", "03.01.06": "high", "03.01.07": "high", "03.01.08": "medium",
    "03.01.09": "low", "03.01.10": "medium", "03.01.11": "medium", "03.01.12": "high",
    "03.01.16": "medium", "03.01.18": "medium", "03.01.20": "high", "03.01.22": "medium",
    "03.02.01": "medium", "03.02.02": "medium",
    "03.03.01": "high", "03.03.02": "medium", "03.03.03": "high", "03.03.04": "medium",
    "03.03.05": "high", "03.03.06": "low", "03.03.07": "medium", "03.03.08": "high",
    "03.04.01": "high", "03.04.02": "high", "03.04.03": "medium", "03.04.04": "low",
    "03.04.05": "medium", "03.04.06": "high", "03.04.08": "high", "03.04.10": "medium",
    "03.04.11": "medium", "03.04.12": "medium",
    "03.05.01": "critical", "03.05.02": "medium", "03.05.03": "critical", "03.05.04": "high",
    "03.05.05": "medium", "03.05.07": "high", "03.05.11": "low", "03.05.12": "high",
    "03.06.01": "high", "03.06.02": "high", "03.06.03": "medium", "03.06.04": "medium",
    "03.06.05": "high",
    "03.07.04": "medium", "03.07.05": "high", "03.07.06": "medium",
    "03.08.01": "medium", "03.08.02": "medium", "03.08.03": "high", "03.08.04": "low",
    "03.08.05": "medium", "03.08.07": "medium", "03.08.09": "high",
    "03.09.01": "medium", "03.09.02": "high",
    "03.10.01": "medium", "03.10.02": "medium", "03.10.06": "low", "03.10.07": "medium",
    "03.10.08": "medium",
    "03.11.01": "high", "03.11.02": "high", "03.11.04": "medium",
    "03.12.01": "medium", "03.12.02": "low", "03.12.03": "high", "03.12.05": "medium",
    "03.13.01": "critical", "03.13.04": "medium", "03.13.06": "high", "03.13.08": "critical",
    "03.13.09": "low", "03.13.10": "high", "03.13.11": "high", "03.13.12": "low",
    "03.13.13": "medium", "03.13.15": "medium",
    "03.14.01": "critical", "03.14.02": "critical", "03.14.03": "medium", "03.14.06": "high",
    "03.14.08": "low", "03.14.09": "high",
    "03.15.01": "medium", "03.15.02": "medium", "03.15.03": "low",
    "03.16.01": "medium", "03.16.02": "high", "03.16.03": "high",
    "03.17.01": "medium", "03.17.02": "medium", "03.17.03": "medium",
}

# CMMC L1/L2 aligned to the same requirements via the 800-171 mapping
# (direct slot match, or the r3 'incorporated into' redirect, or family baseline).
CMMC_RISK = {
    "AC.L1-3.1.1": "high", "AC.L1-3.1.2": "critical", "AC.L1-3.1.20": "high", "AC.L1-3.1.22": "medium",
    "IA.L1-3.5.1": "critical", "IA.L1-3.5.2": "medium", "MP.L1-3.8.3": "high",
    "PE.L1-3.10.1": "medium", "PE.L1-3.10.3": "medium", "PE.L1-3.10.4": "medium", "PE.L1-3.10.5": "medium",
    "SC.L1-3.13.1": "critical", "SC.L1-3.13.5": "critical",
    "SI.L1-3.14.1": "critical", "SI.L1-3.14.2": "critical", "SI.L1-3.14.4": "critical", "SI.L1-3.14.5": "critical",
    "AC.L2-3.1.1": "high", "AC.L2-3.1.2": "critical", "AC.L2-3.1.3": "high", "AC.L2-3.1.4": "medium",
    "AC.L2-3.1.5": "high", "AC.L2-3.1.6": "high", "AC.L2-3.1.7": "high", "AC.L2-3.1.8": "medium",
    "AC.L2-3.1.9": "low", "AC.L2-3.1.10": "medium", "AC.L2-3.1.11": "medium", "AC.L2-3.1.12": "high",
    "AC.L2-3.1.13": "critical", "AC.L2-3.1.14": "high", "AC.L2-3.1.15": "high", "AC.L2-3.1.16": "medium",
    "AC.L2-3.1.17": "medium", "AC.L2-3.1.18": "medium", "AC.L2-3.1.19": "medium", "AC.L2-3.1.20": "high",
    "AC.L2-3.1.21": "high", "AC.L2-3.1.22": "medium",
    "AT.L2-3.2.1": "medium", "AT.L2-3.2.2": "medium", "AT.L2-3.2.3": "medium",
    "AU.L2-3.3.1": "high", "AU.L2-3.3.2": "medium", "AU.L2-3.3.3": "high", "AU.L2-3.3.4": "medium",
    "AU.L2-3.3.5": "high", "AU.L2-3.3.6": "low", "AU.L2-3.3.7": "medium", "AU.L2-3.3.8": "high", "AU.L2-3.3.9": "high",
    "CM.L2-3.4.1": "high", "CM.L2-3.4.2": "high", "CM.L2-3.4.3": "medium", "CM.L2-3.4.4": "low",
    "CM.L2-3.4.5": "medium", "CM.L2-3.4.6": "high", "CM.L2-3.4.7": "high", "CM.L2-3.4.8": "high", "CM.L2-3.4.9": "high",
    "IA.L2-3.5.1": "critical", "IA.L2-3.5.2": "medium", "IA.L2-3.5.3": "critical", "IA.L2-3.5.4": "high",
    "IA.L2-3.5.5": "medium", "IA.L2-3.5.6": "high", "IA.L2-3.5.7": "high", "IA.L2-3.5.8": "high",
    "IA.L2-3.5.9": "high", "IA.L2-3.5.10": "high", "IA.L2-3.5.11": "low",
    "IR.L2-3.6.1": "high", "IR.L2-3.6.2": "high", "IR.L2-3.6.3": "medium",
    "MA.L2-3.7.1": "medium", "MA.L2-3.7.2": "medium", "MA.L2-3.7.3": "high", "MA.L2-3.7.4": "medium",
    "MA.L2-3.7.5": "high", "MA.L2-3.7.6": "medium",
    "MP.L2-3.8.1": "medium", "MP.L2-3.8.2": "medium", "MP.L2-3.8.3": "high", "MP.L2-3.8.4": "low",
    "MP.L2-3.8.5": "medium", "MP.L2-3.8.6": "critical", "MP.L2-3.8.7": "medium", "MP.L2-3.8.8": "medium", "MP.L2-3.8.9": "high",
    "PS.L2-3.9.1": "medium", "PS.L2-3.9.2": "high",
    "PE.L2-3.10.1": "medium", "PE.L2-3.10.2": "medium", "PE.L2-3.10.3": "medium", "PE.L2-3.10.4": "medium",
    "PE.L2-3.10.5": "medium", "PE.L2-3.10.6": "low",
    "RA.L2-3.11.1": "high", "RA.L2-3.11.2": "high", "RA.L2-3.11.3": "high",
    "CA.L2-3.12.1": "medium", "CA.L2-3.12.2": "low", "CA.L2-3.12.3": "high", "CA.L2-3.12.4": "medium",
    "SC.L2-3.13.1": "critical", "SC.L2-3.13.2": "high", "SC.L2-3.13.3": "high", "SC.L2-3.13.4": "medium",
    "SC.L2-3.13.5": "critical", "SC.L2-3.13.6": "high", "SC.L2-3.13.7": "high", "SC.L2-3.13.8": "critical",
    "SC.L2-3.13.9": "low", "SC.L2-3.13.10": "high", "SC.L2-3.13.11": "high", "SC.L2-3.13.12": "low",
    "SC.L2-3.13.13": "medium", "SC.L2-3.13.14": "high", "SC.L2-3.13.15": "medium", "SC.L2-3.13.16": "critical",
    "SI.L2-3.14.1": "critical", "SI.L2-3.14.2": "critical", "SI.L2-3.14.3": "medium", "SI.L2-3.14.4": "critical",
    "SI.L2-3.14.5": "critical", "SI.L2-3.14.6": "high", "SI.L2-3.14.7": "high",
}
RISK.update(CMMC_RISK)


async def run(commit: bool):
    async with AsyncSessionLocal() as db:
        controls = (await db.execute(
            select(Control).where(Control.ref.in_(list(RISK.keys())))
        )).scalars().all()
        changed = 0
        for c in controls:
            want = ControlRisk(RISK[c.ref])
            if c.risk_rating != want:
                changed += 1
                if commit:
                    c.risk_rating = want
        print(f"Matched {len(controls)} controls; {changed} need updating. "
              f"Mode: {'COMMIT' if commit else 'DRY RUN'}")
        if commit:
            await db.commit()
            print("✅ Risk ratings updated.")
        else:
            print("Dry run - re-run with --yes to apply.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="commit changes")
    asyncio.run(run(ap.parse_args().yes))


if __name__ == "__main__":
    main()
