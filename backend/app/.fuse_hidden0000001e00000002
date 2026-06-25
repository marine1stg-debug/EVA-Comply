"""Seed the composed NIST 800-171r3 recording scripts into the DB.

Run inside the api container:  python -m app.seed_scripts_nist
Matches the NIST 800-171 framework by name (avoids ITSP, which shares refs).
Scripts remain editable in the app (Training → Control preview).
"""
import asyncio
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.framework import Framework, Control
from app.nist_scripts_data import NIST_SCRIPTS


async def run():
    async with AsyncSessionLocal() as db:
        fw = (await db.execute(
            select(Framework).where(Framework.name.ilike("%800-171%"))
        )).scalars().first()
        if not fw:
            print("NIST 800-171 framework not found — import it first.")
            return
        updated, missing = 0, 0
        for ref, s in NIST_SCRIPTS.items():
            c = (await db.execute(
                select(Control).where(Control.framework_id == fw.id, Control.ref == ref)
            )).scalar_one_or_none()
            if not c:
                missing += 1
                continue
            c.video_script_en = s["en"]
            c.video_script_fr = s["fr"]
            updated += 1
        await db.commit()
        print(f'Seeded {updated} scripts into "{fw.name}" ({missing} refs not matched).')


if __name__ == "__main__":
    asyncio.run(run())
