"""Populate a realistic demo compliance posture for evaluation.

Targets the NovLogix Inc. demo client and, for each of the four frameworks,
assigns the framework (creating org_control rows), then sets a realistic spread
of statuses, attaches sample evidence on completed controls, records
self-assessment answers, and sets per-domain maturity targets. Idempotent.

    docker compose exec api python -m app.seed_demo_posture          # dry run
    docker compose exec api python -m app.seed_demo_posture --yes    # write
"""
import os
import sys
import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.core.provisioning import assign_frameworks
from app.models.tenant import Tenant
from app.models.user import User
from app.models.framework import Framework, Control
from app.models.evidence import (
    OrgControl, OrgControlStatus, EvidenceItem, EvidenceStatus,
    EvidenceSource, EvidenceFrequency,
)
from app.models.self_assessment import SelfAssessment
from app.models.maturity import MaturityAssessment

ORG_NAME = "NovLogix Inc."
FRAMEWORKS = [
    "CMMC 2.0 — Level 1",
    "CMMC 2.0 — Level 2",
    "NIST SP 800-171 Rev. 3",
    "CyberSecure Canada",
]


def _write_seed_file(org_id, ref):
    """Write a small placeholder evidence file so downloads/preview work."""
    base = settings.STORAGE_LOCAL_PATH
    try:
        os.makedirs(os.path.join(base, str(org_id)), exist_ok=True)
        key = f"{org_id}/seed_{ref}.txt"
        content = (
            "EVA Cybersecurity Audit Portal — demo evidence\n"
            f"Control: {ref}\n"
            "Placeholder evidence generated for evaluation.\n"
        ).encode()
        with open(os.path.join(base, key), "wb") as fh:
            fh.write(content)
        return key, f"{ref}_evidence.txt", len(content)
    except Exception:
        return None, None, None


def plan_for(i: int):
    """Deterministic realistic spread: ~45% done, ~30% in progress, ~25% not started.
    Returns (status, coverage_pct, self_assessment_level_or_None, attach_evidence)."""
    m = i % 20
    if m < 5:                       # 25% verified
        return OrgControlStatus.verified, 100, 5, True
    if m < 9:                        # 20% implemented
        return OrgControlStatus.implemented, 85, 4, True
    if m < 14:                       # 30% in progress
        return OrgControlStatus.in_progress, 40, 2, False
    return OrgControlStatus.not_started, 0, None, False   # 25% not started


async def run(commit: bool):
    print(f"Mode: {'COMMIT' if commit else 'DRY RUN'}\n")
    async with AsyncSessionLocal() as db:
        org = (await db.execute(
            select(Tenant).where(Tenant.name == ORG_NAME)
        )).scalar_one_or_none()
        if not org:
            print(f"!! Org '{ORG_NAME}' not found — is the DB seeded?")
            return

        user = (await db.execute(
            select(User).where(User.tenant_id == org.id)
        )).scalars().first()
        if not user:
            print(f"!! No user found in '{ORG_NAME}'.")
            return

        totals = {"done": 0, "in_progress": 0, "not_started": 0, "evidence": 0}

        for fw_name in FRAMEWORKS:
            fw = (await db.execute(
                select(Framework).where(Framework.name == fw_name)
            )).scalar_one_or_none()
            if not fw:
                print(f"  - {fw_name}: framework not found, skipping")
                continue

            await assign_frameworks(db, org.id, [fw.id])
            await db.flush()

            controls = (await db.execute(
                select(Control).where(Control.framework_id == fw.id).order_by(Control.sort_order)
            )).scalars().all()
            ocs = (await db.execute(
                select(OrgControl).where(
                    OrgControl.org_id == org.id,
                    OrgControl.control_id.in_([c.id for c in controls]),
                )
            )).scalars().all()
            oc_by_cid = {oc.control_id: oc for oc in ocs}

            domains = set()
            for i, c in enumerate(controls):
                oc = oc_by_cid.get(c.id)
                if not oc:
                    continue
                status, cov, level, attach = plan_for(i)
                oc.status = status
                oc.coverage_pct = cov
                oc.owner_user_id = user.id
                if getattr(c, "domain", None):
                    domains.add(c.domain)

                if status in (OrgControlStatus.verified, OrgControlStatus.implemented):
                    totals["done"] += 1
                elif status == OrgControlStatus.in_progress:
                    totals["in_progress"] += 1
                else:
                    totals["not_started"] += 1

                if attach:
                    exists = (await db.execute(
                        select(EvidenceItem.id).where(EvidenceItem.org_control_id == oc.id)
                    )).first()
                    if not exists:
                        key, name, size = _write_seed_file(org.id, c.ref)
                        db.add(EvidenceItem(
                            org_control_id=oc.id, org_id=org.id,
                            title=f"{c.ref} — evidence",
                            description="Demo evidence for evaluation.",
                            file_key=key, file_name=name, file_size=size,
                            file_type="text/plain",
                            source=EvidenceSource.upload,
                            status=EvidenceStatus.accepted,
                            collected_by=user.id,
                            frequency=EvidenceFrequency.annual,
                        ))
                        totals["evidence"] += 1

                if level is not None:
                    sa = (await db.execute(
                        select(SelfAssessment).where(
                            SelfAssessment.org_id == org.id,
                            SelfAssessment.control_id == c.id,
                        )
                    )).scalar_one_or_none()
                    if sa:
                        sa.answers = {"default": level}
                    else:
                        db.add(SelfAssessment(
                            org_id=org.id, control_id=c.id, answers={"default": level}
                        ))

            for d in domains:
                exists = (await db.execute(
                    select(MaturityAssessment.id).where(
                        MaturityAssessment.org_id == org.id,
                        MaturityAssessment.framework_id == fw.id,
                        MaturityAssessment.domain == d,
                    )
                )).first()
                if not exists:
                    db.add(MaturityAssessment(
                        org_id=org.id, framework_id=fw.id, domain=d, target_level=4
                    ))

            print(f"  - {fw_name}: {len(controls)} controls")

        print(f"\n{ORG_NAME}: done={totals['done']} "
              f"in_progress={totals['in_progress']} not_started={totals['not_started']} "
              f"evidence_files={totals['evidence']}")

        if commit:
            await db.commit()
            print("\nCommitted. Log in and open NovLogix Inc. to evaluate.")
        else:
            print("\nDry run — re-run with --yes to write.")


if __name__ == "__main__":
    asyncio.run(run("--yes" in sys.argv))
