"""Import the four bilingual framework catalogs (EN + FR) as system frameworks.

Reads the EN and FR .xlsx files in app/catalog_data/, creates (or fills) the
frameworks and their controls with English content plus French (*_fr) columns.
Domains are kept in English in the DB and localized for display by the API.

Idempotent / re-runnable: upserts controls by (framework, ref), so re-running
backfills French columns and updated text without creating duplicates.

USAGE (inside the api container):
    docker compose exec api python -m app.seed_catalogs            # dry run
    docker compose exec api python -m app.seed_catalogs --yes
Then apply the maturity banks (matches by ref across these frameworks):
    docker compose exec api python -m app.seed_maturity_questions --yes
"""
import argparse
import asyncio
import os

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models import framework, evidence  # noqa: F401 — register mappers
from app.models.framework import Framework, Control, ControlPriority, ControlRisk

DATA_DIR = os.path.join(os.path.dirname(__file__), "catalog_data")

# (en_file, fr_file, framework name, version, levels, description, description_fr)
CATALOGS = [
    ("CMMC_2.0_Level_1.xlsx", "CMMC_2.0_Level_1_FR.xlsx",
     "CMMC 2.0 — Level 1", "2.0 (Level 1)", ["Level 1"],
     "Cybersecurity Maturity Model Certification 2.0, Level 1 — 17 practices for Federal Contract Information (FCI).",
     "Cybersecurity Maturity Model Certification 2.0, niveau 1 — 17 pratiques pour les renseignements contractuels fédéraux (FCI)."),
    ("CMMC_2.0_Level_2.xlsx", "CMMC_2.0_Level_2_FR.xlsx",
     "CMMC 2.0 — Level 2", "2.0 (Level 2)", ["Level 2"],
     "Cybersecurity Maturity Model Certification 2.0, Level 2 — 110 practices aligned to NIST SP 800-171 for Controlled Unclassified Information (CUI).",
     "Cybersecurity Maturity Model Certification 2.0, niveau 2 — 110 pratiques alignées sur NIST SP 800-171 pour les renseignements non classifiés contrôlés (CUI)."),
    ("ITSP_10-171.xlsx", "ITSP_10-171_FR.xlsx",
     "ITSP.10.171 (CPCSC)", "2025 (NIST SP 800-171 R3)", ["Level 1", "Level 2", "Level 3"],
     "Canadian Centre for Cyber Security adaptation of NIST SP 800-171 R3; cornerstone of the Canadian Program for Cyber Security Certification (CPCSC). 17 families.",
     "Adaptation par le Centre canadien pour la cybersécurité de NIST SP 800-171 R3; pierre angulaire du Programme canadien pour la certification en cybersécurité (PCCC). 17 familles."),
    ("NIST_800-171r3.xlsx", "NIST_800-171r3_FR.xlsx",
     "NIST SP 800-171 Rev. 3", "r3", ["—"],
     "NIST Special Publication 800-171 Revision 3 — protecting Controlled Unclassified Information in nonfederal systems. 17 families, 97 requirements.",
     "Publication spéciale NIST 800-171 révision 3 — protection des renseignements non classifiés contrôlés dans les systèmes non fédéraux. 17 familles, 97 exigences."),
    ("CyberSecure_Canada.xlsx", "CyberSecure_Canada_FR.xlsx",
     "CyberSecure Canada", "Baseline V1.2", ["Baseline"],
     "CyberSecure Canada — CCCS Baseline Cyber Security Controls for Small and Medium Organizations V1.2 (TLP:WHITE). 5 organizational + 13 baseline control areas, 50 controls (OC.* / BC.*), verbatim.",
     "CyberSecure Canada — Contrôles de cybersécurité de base du CCC pour les petites et moyennes organisations V1.2 (TLP:WHITE). 5 contrôles organisationnels + 13 domaines de contrôles de base, 50 contrôles (OC.* / BC.*), textuels."),
    ("CIS_Controls_v8.1.xlsx", "CIS_Controls_v8.1_FR.xlsx",
     "CIS Controls v8.1", "8.1.2", ["IG1", "IG2", "IG3"],
     "CIS Critical Security Controls v8.1 — 153 safeguards across 18 controls, tagged by Implementation Group (IG1/IG2/IG3). © CIS, CC BY-NC-ND 4.0 (cisecurity.org/controls).",
     "Contrôles de sécurité critiques CIS v8.1 — 153 mesures réparties dans 18 contrôles, marquées par groupe de mise en œuvre (IG1/IG2/IG3). © CIS, CC BY-NC-ND 4.0 (cisecurity.org/controls)."),
    ("NIST_800-53r5.xlsx", "NIST_800-53r5_FR.xlsx",
     "NIST SP 800-53 Rev. 5", "r5", ["Base", "Enhancement"],
     "NIST SP 800-53 Revision 5 — Security and Privacy Controls. Full control catalog: 1189 controls (322 base + 867 enhancements) across 20 families, verbatim from the official NIST spreadsheet (public domain). English source — NIST publishes no official French.",
     "NIST SP 800-53 révision 5 — Contrôles de sécurité et de confidentialité. Catalogue complet : 1189 contrôles (322 de base + 867 améliorations) dans 20 familles, textuels d'après le tableur officiel du NIST (domaine public). Source en anglais — le NIST ne publie pas de version française officielle."),
]

# EN xlsx column -> Control attribute
EN_MAP = {
    "title": "title", "domain": "domain", "level": "level",
    "description": "description", "objective": "objective",
    "plain_language": "plain_language", "best_practices": "best_practices",
    "expected_evidence": "evidence_best_practices", "discussion": "discussion",
}
# FR xlsx column -> Control attribute
FR_MAP = {
    "title": "title_fr", "description": "description_fr", "objective": "objective_fr",
    "plain_language": "plain_language_fr", "best_practices": "best_practices_fr",
    "expected_evidence": "evidence_best_practices_fr", "discussion": "discussion_fr",
}


def _read_xlsx(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    hdr = [str(h).strip() if h is not None else "" for h in rows[0]]
    out = []
    for r in rows[1:]:
        d = {hdr[i]: r[i] for i in range(len(hdr))}
        if d.get("ref"):
            out.append(d)
    return out


def _clean(v):
    if v is None:
        return None
    s = str(v).strip()
    return s if s and s.lower() != "none" else None


def _enum(cls, v):
    v = _clean(v)
    if not v:
        return None
    try:
        return cls(v.lower())
    except ValueError:
        return None


def _parse_mappings(v):
    import json
    v = _clean(v)
    if not v:
        return None
    try:
        obj = json.loads(v)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


async def run(commit: bool):
    async with AsyncSessionLocal() as db:
        print(f"Mode: {'COMMIT' if commit else 'DRY RUN'}\n")
        for en_file, fr_file, name, version, levels, desc, desc_fr in CATALOGS:
            en_path = os.path.join(DATA_DIR, en_file)
            fr_path = os.path.join(DATA_DIR, fr_file)
            if not os.path.exists(en_path):
                print(f"!! missing {en_file} — skipped"); continue
            en_rows = _read_xlsx(en_path)
            fr_by_ref = {str(d["ref"]).strip(): d for d in _read_xlsx(fr_path)} if os.path.exists(fr_path) else {}

            fw = (await db.execute(
                select(Framework).where(Framework.name == name, Framework.version == version)
            )).scalar_one_or_none()
            created_fw = False
            if not fw:
                fw = Framework(name=name, version=version, description=desc, description_fr=desc_fr,
                               is_system=True, is_active=True, levels=levels)
                db.add(fw); await db.flush(); created_fw = True
            else:
                fw.description = fw.description or desc
                fw.description_fr = fw.description_fr or desc_fr

            existing = {c.ref: c for c in (await db.execute(
                select(Control).where(Control.framework_id == fw.id)
            )).scalars().all()}

            n_new = n_upd = 0
            for i, row in enumerate(en_rows):
                ref = str(row["ref"]).strip()
                c = existing.get(ref)
                if not c:
                    c = Control(framework_id=fw.id, ref=ref, title=_clean(row.get("title")) or ref, sort_order=i)
                    db.add(c); n_new += 1
                else:
                    n_upd += 1
                # EN fields
                for col, attr in EN_MAP.items():
                    val = _clean(row.get(col))
                    if val is not None:
                        setattr(c, attr, val)
                c.priority = _enum(ControlPriority, row.get("priority")) or c.priority
                c.risk_rating = _enum(ControlRisk, row.get("risk")) or c.risk_rating
                mp = _parse_mappings(row.get("mappings"))
                if mp:
                    c.mappings = mp
                c.sort_order = i
                # FR fields
                fr = fr_by_ref.get(ref)
                if fr:
                    for col, attr in FR_MAP.items():
                        val = _clean(fr.get(col))
                        if val is not None:
                            setattr(c, attr, val)
            print(f"{'[new] ' if created_fw else '[fill]'} {name} ({version}): "
                  f"{len(en_rows)} controls — {n_new} new, {n_upd} updated, "
                  f"{len(fr_by_ref)} FR rows")

        if commit:
            await db.commit()
            print("\nCommitted.")
        else:
            print("\nDry run only — re-run with --yes to apply.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="write the frameworks/controls")
    args = ap.parse_args()
    asyncio.run(run(args.yes))
