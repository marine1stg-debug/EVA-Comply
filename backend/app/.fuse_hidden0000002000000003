from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "eva_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="generate_report")
def generate_report(report_type: str, org_id: str, options: dict):
    """Async report generation task."""
    import time
    time.sleep(2)  # Simulate generation
    return {"status": "ready", "report_type": report_type, "org_id": org_id}

@celery_app.task(name="send_email")
def send_email(to: str, subject: str, body: str):
    """Send transactional email."""
    print(f"EMAIL → {to}: {subject}")
    return {"sent": True}

@celery_app.task(name="scan_file")
def scan_file(file_key: str, evidence_id: str):
    """Simulate ClamAV virus scan."""
    print(f"SCAN → {file_key}")
    return {"scan_status": "clean", "evidence_id": evidence_id}
