# -*- coding: utf-8 -*-
"""Diagnostic: per framework, how many controls actually have French content
in the database (title_fr / description_fr). Read-only.

USAGE (inside the api container):
    docker compose exec api python -m app.check_catalog_langs
"""
import asyncio
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.framework import Framework, Control


async def run():
    async with AsyncSessionLocal() as db:
        fws = (await db.execute(select(Framework).order_by(Framework.name))).scalars().all()
        print(f"{'Framework':40} {'ver':14} {'ctrls':>6} {'title_fr':>9} {'desc_fr':>8}")
        print("-" * 82)
        for fw in fws:
            total = (await db.execute(
                select(func.count(Control.id)).where(Control.framework_id == fw.id))).scalar_one()
            tfr = (await db.execute(
                select(func.count(Control.id)).where(
                    Control.framework_id == fw.id,
                    Control.title_fr.isnot(None), Control.title_fr != ""))).scalar_one()
            dfr = (await db.execute(
                select(func.count(Control.id)).where(
                    Control.framework_id == fw.id,
                    Control.description_fr.isnot(None), Control.description_fr != ""))).scalar_one()
            flag = "" if total == 0 else ("  ✅ FR" if tfr >= total else ("  ⚠️ EN only" if tfr == 0 else "  ◐ partial"))
            print(f"{fw.name[:40]:40} {str(fw.version)[:14]:14} {total:>6} {tfr:>9} {dfr:>8}{flag}")


if __name__ == "__main__":
    asyncio.run(run())
