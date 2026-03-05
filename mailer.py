"""
mailer.py – Echter SMTP Email-Versand
MR Digital – Akquise Automatisierung v2
"""

import smtplib
import logging
import time
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import (
    GMAIL_ADDRESS, GMAIL_APP_PASSWORD, SMTP_HOST, SMTP_PORT,
    SENDER_NAME, MAX_EMAILS_PER_DAY, SEND_DELAY_SECONDS, WEBSITE
)
from data_store import (
    save_email_sent, update_lead_status, count_emails_today,
    is_blacklisted, get_setting
)

logger = logging.getLogger(__name__)


def _get_credentials():
    """Liest Credentials aus DB-Settings (überschreibt .env falls gesetzt)."""
    addr = get_setting("gmail_address") or GMAIL_ADDRESS
    pw = get_setting("gmail_app_password") or GMAIL_APP_PASSWORD
    return addr, pw


def test_connection() -> dict:
    """Testet die SMTP-Verbindung. Gibt {ok, message} zurück."""
    addr, pw = _get_credentials()
    if not pw or pw == "xxxx-xxxx-xxxx-xxxx":
        return {"ok": False, "message": "❌ Kein App-Passwort konfiguriert. Bitte in Einstellungen eintragen."}
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(addr, pw)
        return {"ok": True, "message": f"✅ SMTP-Verbindung OK ({addr})"}
    except smtplib.SMTPAuthenticationError:
        return {"ok": False, "message": "❌ Authentifizierung fehlgeschlagen – App-Passwort prüfen!"}
    except Exception as e:
        return {"ok": False, "message": f"❌ Verbindungsfehler: {str(e)[:150]}"}


def send_test_email() -> dict:
    """Schickt eine Test-Email an sich selbst."""
    addr, pw = _get_credentials()
    result = test_connection()
    if not result["ok"]:
        return result

    subject = "✅ MR Digital Akquise – Test-Email"
    body = (
        f"Hallo Nicklas,\n\n"
        f"das ist eine Test-Email der MR Digital Akquise-Automatisierung.\n"
        f"Der SMTP-Versand funktioniert korrekt.\n\n"
        f"Absender: {addr}\n"
        f"Empfänger: {addr} (test)\n\n"
        f"Viel Erfolg mit der Akquise! 🚀\n\n"
        f"– MR Digital Automatisierung v2"
    )
    return _send(addr, "MR Digital Test", subject, body, lead_id=None, is_test=True)


def send_email(lead: dict, subject: str, body_html: str, body_text: str) -> dict:
    """
    Sendet eine Akquise-Email an einen Lead.
    Prüft Blacklist, Tageslimit und Rate-Limiting.
    """
    addr, pw = _get_credentials()
    to_email = lead.get("email", "")
    lead_id = lead.get("id")

    # Validierungen
    if not to_email:
        return {"ok": False, "message": "Kein Email-Empfänger"}
    if is_blacklisted(to_email):
        return {"ok": False, "message": f"Blacklist: {to_email}"}

    max_per_day = int(get_setting("max_emails_per_day") or MAX_EMAILS_PER_DAY)
    sent_today = count_emails_today()
    if sent_today >= max_per_day:
        return {"ok": False, "message": f"Tageslimit erreicht ({max_per_day}/Tag)"}

    result = _send(to_email, lead.get("name", ""), subject, body_html,
                   body_text=body_text, lead_id=lead_id)

    if result["ok"] and lead_id:
        from datetime import datetime
        update_lead_status(lead_id, "Kontaktiert",
                           contacted_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Rate-limiting Pause
    delay = random.randint(*SEND_DELAY_SECONDS)
    time.sleep(delay)

    return result


def _send(to_addr: str, to_name: str, subject: str, body_html: str,
          body_text: str = None, lead_id=None, is_test=False) -> dict:
    """Interner SMTP-Versand."""
    addr, pw = _get_credentials()
    sender_full = f"{SENDER_NAME} <{addr}>"

    msg = MIMEMultipart("alternative")
    msg["From"] = sender_full
    msg["To"] = f"{to_name} <{to_addr}>" if to_name else to_addr
    msg["Subject"] = subject
    msg["Reply-To"] = addr

    # Unsubscribe-Header (DSGVO-konform)
    base_url = get_setting("app_url") or WEBSITE
    unsubscribe_url = f"{base_url}/unsubscribe?email={to_addr}"
    msg["List-Unsubscribe"] = f"<{unsubscribe_url}>"

    if body_text:
        msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(addr, pw)
            server.sendmail(addr, [to_addr], msg.as_string())

        if not is_test:
            save_email_sent({
                "lead_id": lead_id,
                "to_addr": to_addr,
                "to_name": to_name,
                "subject": subject,
                "body": body_html,
                "status": "Gesendet",
                "error_msg": "",
            })
        logger.info(f"[Mailer] ✅ Email gesendet → {to_addr}")
        return {"ok": True, "message": f"✅ Email gesendet an {to_addr}"}

    except Exception as e:
        err = str(e)[:200]
        if not is_test and lead_id:
            save_email_sent({
                "lead_id": lead_id,
                "to_addr": to_addr,
                "to_name": to_name,
                "subject": subject,
                "body": body_html,
                "status": "Fehler",
                "error_msg": err,
            })
        logger.error(f"[Mailer] ❌ Fehler bei {to_addr}: {err}")
        return {"ok": False, "message": f"❌ Fehler: {err}"}
