"""Compose bilingual (EN + FR) recording scripts for EVERY control in EVERY
framework, from each control's own catalog content. Runs at startup.

NON-DESTRUCTIVE: only fills scripts that are empty, so admin hand-edits survive
a restart. Pass --force to recompose every script (e.g. after improving the
composer).

Run:  python -m app.seed_scripts_all          # fill gaps only
      python -m app.seed_scripts_all --force  # recompose all
"""
import argparse
import asyncio
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.framework import Framework, Control
from app.script_compose import compose


async def run(force: bool = False):
    async with AsyncSessionLocal() as db:
        fws = (await db.execute(select(Framework))).scalars().all()
        total = filled = 0
        for fw in fws:
            ctrls = (await db.execute(
                select(Control).where(Control.framework_id == fw.id)
            )).scalars().all()
            n = 0
            for c in ctrls:
                if force or not c.video_script_en:
                    c.video_script_en = compose(c, "en"); n += 1
                if force or not c.video_script_fr:
                    c.video_script_fr = compose(c, "fr")
            total += len(ctrls); filled += n
            print(f"  {fw.name}: {len(ctrls)} controls ({n} scripted)")
        await db.commit()
        print(f"Done - {filled} controls scripted across {len(fws)} frameworks "
              f"({'forced' if force else 'gaps only'}).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="recompose every script")
    args = ap.parse_args()
    asyncio.run(run(args.force))
