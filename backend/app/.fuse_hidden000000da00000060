# -*- coding: utf-8 -*-
"""Generate a French translation of an English-only catalog using the configured
AI connector, written into the catalog's *_FR.xlsx so the normal seed picks it up.

Use for catalogs with no official French source (e.g. NIST SP 800-53). The output
is an UNOFFICIAL machine translation; the English source remains authoritative.

Resumable: rows already translated in the FR file are skipped (unless --force).
Bracketed placeholders ([Assignment: …], [Selection: …]) and control identifiers
are preserved by instruction.

USAGE (inside the api container, with the AI connector configured & enabled):
    docker compose exec api python -m app.translate_catalog_fr            # translate all (NIST 800-53)
    docker compose exec api python -m app.translate_catalog_fr --limit 5  # try 5 first
    docker compose exec api python -m app.translate_catalog_fr --src CIS_Controls_v8.1.xlsx
Then load it:
    docker compose exec api python -m app.seed_catalogs --yes
"""
import argparse
import asyncio
import json
import os
import re

import openpyxl

from app.core.database import AsyncSessionLocal
from app.core.llm import get_llm_settings, chat, LlmError

DATA_DIR = os.path.join(os.path.dirname(__file__), "catalog_data")
COLS = ["ref", "title", "domain", "level", "priority", "risk", "description",
        "objective", "plain_language", "best_practices", "expected_evidence", "discussion", "mappings"]

SYSTEM = (
    "You are a professional translator specializing in cybersecurity and "
    "regulatory compliance. Translate the given English control text into clear, "
    "professional Canadian French. Rules: keep technical terms accurate; DO NOT "
    "translate or alter control identifiers (e.g. AC-2, AC-2(1)) or bracketed "
    "placeholders such as [Assignment: organization-defined ...] and "
    "[Selection: ...] — copy them verbatim; preserve list lettering (a. b. c.) and "
    "numbering; do not add commentary. Return ONLY a JSON object with keys "
    "\"title\", \"description\", \"discussion\" (use empty strings if an input is empty)."
)


def _read(path):
    if not os.path.exists(path):
        return {}
    ws = openpyxl.load_workbook(path, read_only=True).active
    rows = list(ws.iter_rows(values_only=True))
    hdr = [str(c).strip() if c else "" for c in rows[0]]
    out = {}
    for r in rows[1:]:
        d = {hdr[i]: ("" if i >= len(r) or r[i] is None else str(r[i])) for i in range(len(hdr))}
        if d.get("ref"):
            out[d["ref"]] = d
    return out


def _extract_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON in reply")
    return json.loads(m.group(0))


async def run(src, limit, force):
    en_path = os.path.join(DATA_DIR, src)
    if not os.path.exists(en_path):
        print(f"!! source not found: {en_path}"); return
    fr_path = os.path.join(DATA_DIR, src.replace(".xlsx", "_FR.xlsx"))
    en = _read(en_path)
    existing_fr = _read(fr_path)

    async with AsyncSessionLocal() as db:
        s = await get_llm_settings(db)
        if not s.enabled:
            print("!! AI connector is disabled. Configure & enable it under AI Connector first.")
            return
        print(f"Provider: {s.provider} · model: {s.model}")

        order = list(en.keys())
        todo = [ref for ref in order
                if force or not (existing_fr.get(ref, {}).get("description")
                                 or existing_fr.get(ref, {}).get("title", "") not in ("", en[ref].get("title", "")))]
        if limit:
            todo = todo[:limit]
        print(f"{len(en)} controls in source · {len(todo)} to translate "
              f"({'forced' if force else 'resuming'})\n")

        fr = dict(existing_fr)
        done = 0
        for ref in todo:
            e = en[ref]
            payload = json.dumps({"title": e.get("title", ""), "description": e.get("description", ""),
                                  "discussion": e.get("discussion", "")}, ensure_ascii=False)
            try:
                reply = await chat(s, [{"role": "system", "content": SYSTEM},
                                       {"role": "user", "content": payload}], max_tokens=2000)
                tr = _extract_json(reply)
            except (LlmError, ValueError) as ex:
                print(f"  [skip] {ref}: {ex}")
                continue
            row = dict(e)
            row["title"] = tr.get("title") or e.get("title", "")
            row["description"] = tr.get("description") or ""
            row["discussion"] = tr.get("discussion") or ""
            fr[ref] = row
            done += 1
            if done % 10 == 0:
                _write(fr_path, en, fr)
                print(f"  …{done}/{len(todo)} (saved)")
        _write(fr_path, en, fr)
        print(f"\nDone — {done} translated. Wrote {fr_path}")
        print("Next: docker compose exec api python -m app.seed_catalogs --yes")


def _write(fr_path, en, fr):
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "controls"
    ws.append(COLS)
    for ref in en.keys():
        row = fr.get(ref) or en[ref]
        ws.append([row.get(c, "") for c in COLS])
    wb.save(fr_path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="NIST_800-53r5.xlsx", help="English catalog filename in catalog_data/")
    ap.add_argument("--limit", type=int, default=0, help="translate at most N (0 = all)")
    ap.add_argument("--force", action="store_true", help="re-translate even rows already done")
    args = ap.parse_args()
    asyncio.run(run(args.src, args.limit, args.force))
