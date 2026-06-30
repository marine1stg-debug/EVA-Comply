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
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from app.core.config import settings

log = logging.getLogger("eva.email")

# ── Effective config: in-app DB settings override .env ───────────────────────
# The mailer runs in both the API and the background worker (separate processes),
# so we read the single email_settings row at send time via a short-lived sync
# connection, cached briefly. If the row is missing or not configured, we fall
# back to the .env settings. Clearing the cache (reload_email_config) makes a
# fresh save take effect immediately for the "send test" button.
_cache: dict = {"at": 0.0, "cfg": None}
_CACHE_TTL = 15.0


def reload_email_config() -> None:
    _cache["cfg"] = None
    _cache["at"] = 0.0


def _db_row() -> dict | None:
    try:
        import psycopg2
        from app.core.secrets_crypto import decrypt
        url = settings.DATABASE_URL.replace("+asyncpg", "")
        conn = psycopg2.connect(url, connect_timeout=5)
        try:
            cur = conn.cursor()
            cur.execute("SELECT backend, from_email, smtp_host, smtp_port, smtp_user, "
                        "smtp_password, smtp_tls, sendgrid_api_key, configured "
                        "FROM email_settings LIMIT 1")
            r = cur.fetchone()
        finally:
            conn.close()
        if not r or not r[8]:   # no row / not configured in-app
            return None
        return {
            "backend": r[0] or "", "from_email": (r[1] or "").strip(),
            "smtp_host": r[2] or "", "smtp_port": int(r[3] or 587),
            "smtp_user": r[4] or "", "smtp_password": decrypt(r[5]) or "",
            "smtp_tls": bool(r[6]), "sendgrid_api_key": decrypt(r[7]) or "",
        }
    except Exception:
        return None   # table missing during migration, DB hiccup, etc. → env fallback


def _effective() -> dict:
    now = time.time()
    if _cache["cfg"] is not None and now - _cache["at"] < _CACHE_TTL:
        return _cache["cfg"]
    db = _db_row()
    cfg = {
        "backend": (db["backend"] if db and db["backend"] else settings.EMAIL_BACKEND),
        "from_email": (db["from_email"] if db and db["from_email"] else settings.FROM_EMAIL),
        "smtp_host": db["smtp_host"] if db else settings.SMTP_HOST,
        "smtp_port": db["smtp_port"] if db else settings.SMTP_PORT,
        "smtp_user": db["smtp_user"] if db else settings.SMTP_USER,
        "smtp_password": db["smtp_password"] if db else settings.SMTP_PASSWORD,
        "smtp_tls": db["smtp_tls"] if db else settings.SMTP_TLS,
        "sendgrid_api_key": db["sendgrid_api_key"] if db else settings.SENDGRID_API_KEY,
    }
    _cache.update(at=now, cfg=cfg)
    return cfg


def sender_address(sender: str) -> str:
    # Per-type overrides stay available via .env; otherwise the effective
    # from-address (in-app setting, else .env FROM_EMAIL) is used for all.
    mapping = {
        "invoicing": settings.EMAIL_FROM_INVOICING,
        "cases": settings.EMAIL_FROM_CASES,
        "noreply": settings.EMAIL_FROM_NOREPLY,
    }
    base = _effective()["from_email"]
    return (mapping.get(sender) or base).strip() or base


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
    cfg = _effective()
    if not cfg["smtp_host"]:
        log.warning("SMTP host not set; cannot send via smtp.")
        return False
    msg = _build_message(from_addr, recipients, subject, body, html, attachments)
    with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"], timeout=15) as s:
        if cfg["smtp_tls"]:
            s.starttls()
        if cfg["smtp_user"]:
            s.login(cfg["smtp_user"], cfg["smtp_password"])
        s.sendmail(from_addr, recipients, msg.as_string())
    return True


def send_email(to, subject: str, body: str, sender: str = "noreply",
               html: str | None = None, attachments: list | None = None) -> bool:
    """Send (best-effort). `sender` selects the from-address (invoicing/cases/noreply).
    Optional `html` body and `attachments` (list of (filename, bytes, mimetype))."""
    recipients = [to] if isinstance(to, str) else [r for r in to if r]
    if not recipients:
        return False
    cfg = _effective()
    from_addr = sender_address(sender)

    if cfg["backend"] == "smtp":
        try:
            return _send_smtp(from_addr, recipients, subject, body, html, attachments)
        except Exception as e:  # pragma: no cover - external
            log.warning("SMTP send failed (%s); falling back to console log.", e)

    if cfg["backend"] == "sendgrid" and cfg["sendgrid_api_key"]:
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            msg = Mail(from_email=from_addr, to_emails=recipients, subject=subject,
                       plain_text_content=body, html_content=html or None)
            SendGridAPIClient(cfg["sendgrid_api_key"]).send(msg)
            return True
        except Exception as e:  # pragma: no cover - external
            log.warning("SendGrid send failed (%s); falling back to console log.", e)

    att = ", ".join(f for (f, _d, _m) in (attachments or []))
    line = (f"[EMAIL · from={from_addr} → {', '.join(recipients)}] {subject}\n{body}"
            + (f"\n[attachments: {att}]" if att else ""))
    log.info(line)
    print(line, flush=True)
    return True


def send_test(to: str, sender: str = "noreply") -> tuple[bool, str]:
    """Real send attempt for the 'Send test email' button. Unlike send_email()
    (best-effort, always returns True), this reports the actual outcome/error so
    the admin can see whether the configuration works."""
    reload_email_config()
    cfg = _effective()
    from_addr = sender_address(sender)
    subj = "EVA Comply - test email"
    body = ("This is a test email from EVA Comply.\n\n"
            "If you received it, your email settings are working.")
    if cfg["backend"] == "smtp":
        if not cfg["smtp_host"]:
            return False, "No SMTP host is set."
        try:
            _send_smtp(from_addr, [to], subj, body)
            return True, f"Sent to {to} via {cfg['smtp_host']}."
        except Exception as e:
            return False, f"SMTP error: {e}"
    if cfg["backend"] == "sendgrid":
        if not cfg["sendgrid_api_key"]:
            return False, "No SendGrid API key is set."
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            m = Mail(from_email=from_addr, to_emails=[to], subject=subj, plain_text_content=body)
            SendGridAPIClient(cfg["sendgrid_api_key"]).send(m)
            return True, f"Sent to {to} via SendGrid."
        except Exception as e:
            return False, f"SendGrid error: {e}"
    return False, "Backend is 'console' (no real email is sent). Choose SMTP or SendGrid."
