"""E-mail sender with three configurable senders and multiple backends.

Senders (pick via `sender=`):
  - "invoicing"  → EMAIL_FROM_INVOICING   (invoices, billing)
  - "cases"      → EMAIL_FROM_CASES        (support cases)
  - "noreply"    → EMAIL_FROM_NOREPLY      (auth, system notices)  [default]
Each falls back to FROM_EMAIL when its address isn't configured.

Backends (EMAIL_BACKEND): console (dev log), smtp, sendgrid. Failures never raise.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from app.core.config import settings

log = logging.getLogger("eva.email")


def sender_address(sender: str) -> str:
    mapping = {
        "invoicing": settings.EMAIL_FROM_INVOICING,
        "cases": settings.EMAIL_FROM_CASES,
        "noreply": settings.EMAIL_FROM_NOREPLY,
    }
    return (mapping.get(sender) or settings.FROM_EMAIL).strip() or settings.FROM_EMAIL


def _build_message(from_addr, recipients, subject, body, html, attachments):
    """Plain MIMEText when simple; MIMEMultipart when html or attachments given."""
    if not html and not attachments:
        msg = MIMEText(body, "plain", "utf-8")
    else:
        msg = MIMEMultipart("mixed")
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(body, "plain", "utf-8"))
        if html:
            alt.attach(MIMEText(html, "html", "utf-8"))
        msg.attach(alt)
        for (fname, data, mime) in (attachments or []):
            sub = (mime.split("/", 1)[1] if "/" in mime else "octet-stream")
            part = MIMEApplication(data, _subtype=sub)
            part.add_header("Content-Disposition", "attachment", filename=fname)
            msg.attach(part)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(recipients)
    return msg


def _send_smtp(from_addr, recipients, subject, body, html=None, attachments=None) -> bool:
    if not settings.SMTP_HOST:
        log.warning("SMTP_HOST not set; cannot send via smtp.")
        return False
    msg = _build_message(from_addr, recipients, subject, body, html, attachments)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as s:
        if settings.SMTP_TLS:
            s.starttls()
        if settings.SMTP_USER:
            s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        s.sendmail(from_addr, recipients, msg.as_string())
    return True


def send_email(to, subject: str, body: str, sender: str = "noreply",
               html: str | None = None, attachments: list | None = None) -> bool:
    """Send (best-effort). `sender` selects the from-address (invoicing/cases/noreply).
    Optional `html` body and `attachments` (list of (filename, bytes, mimetype))."""
    recipients = [to] if isinstance(to, str) else [r for r in to if r]
    if not recipients:
        return False
    from_addr = sender_address(sender)

    if settings.EMAIL_BACKEND == "smtp":
        try:
            return _send_smtp(from_addr, recipients, subject, body, html, attachments)
        except Exception as e:  # pragma: no cover - external
            log.warning("SMTP send failed (%s); falling back to console log.", e)

    if settings.EMAIL_BACKEND == "sendgrid" and settings.SENDGRID_API_KEY:
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            msg = Mail(from_email=from_addr, to_emails=recipients, subject=subject,
                       plain_text_content=body, html_content=html or None)
            SendGridAPIClient(settings.SENDGRID_API_KEY).send(msg)
            return True
        except Exception as e:  # pragma: no cover - external
            log.warning("SendGrid send failed (%s); falling back to console log.", e)

    att = ", ".join(f for (f, _d, _m) in (attachments or []))
    line = (f"[EMAIL · from={from_addr} → {', '.join(recipients)}] {subject}\n{body}"
            + (f"\n[attachments: {att}]" if att else ""))
    log.info(line)
    print(line, flush=True)
    return True
