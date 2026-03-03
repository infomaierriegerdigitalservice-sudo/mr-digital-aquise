"""
scheduler.py – Automatischer täglicher Email-Versand
MR Digital – Akquise Automatisierung v2
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler(timezone="Europe/Berlin")
_scheduler.start()

SCHEDULER_STATUS = {
    "running": False,
    "last_run": None,
    "last_result": None,
    "next_run": None,
    "job_id": "daily_akquise",
}


def _run_daily_campaign():
    """Führt die tägliche Akquise-Kampagne aus."""
    from data_store import get_all_leads, get_active_campaign, count_emails_today, get_setting
    from email_generator import generate_email
    from mailer import send_email
    from backup import create_backup

    SCHEDULER_STATUS["running"] = True
    SCHEDULER_STATUS["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.info("[Scheduler] ▶ Tägliche Kampagne gestartet")

    campaign = get_active_campaign()
    if not campaign:
        logger.warning("[Scheduler] Keine aktive Kampagne gefunden.")
        SCHEDULER_STATUS["running"] = False
        SCHEDULER_STATUS["last_result"] = "Keine aktive Kampagne"
        return

    max_today = int(get_setting("max_emails_per_day") or campaign.get("emails_per_day", 30))
    sent_today = count_emails_today()
    remaining = max_today - sent_today

    if remaining <= 0:
        logger.info(f"[Scheduler] Tageslimit bereits erreicht ({max_today})")
        SCHEDULER_STATUS["running"] = False
        SCHEDULER_STATUS["last_result"] = f"Tageslimit erreicht ({max_today})"
        return

    # Leads holen die noch nicht kontaktiert wurden
    all_leads = get_all_leads(status="Neu")
    leads_to_contact = [l for l in all_leads if l.get("email")][:remaining]

    sent_count = 0
    error_count = 0

    for lead in leads_to_contact:
        if not SCHEDULER_STATUS["running"]:
            logger.info("[Scheduler] Manuell gestoppt.")
            break

        email_data = generate_email(lead)
        result = send_email(lead, email_data["subject"],
                            email_data["body_html"], email_data["body_text"])

        if result["ok"]:
            sent_count += 1
            logger.info(f"[Scheduler] ✅ {lead['name']} ({lead['email']})")
        else:
            error_count += 1
            logger.warning(f"[Scheduler] ❌ {lead.get('name')}: {result['message']}")

    # Tägliches Backup
    try:
        create_backup()
    except Exception as e:
        logger.warning(f"[Scheduler] Backup-Fehler: {e}")

    result_msg = f"✅ {sent_count} gesendet, ❌ {error_count} Fehler"
    SCHEDULER_STATUS["running"] = False
    SCHEDULER_STATUS["last_result"] = result_msg
    _update_next_run()
    logger.info(f"[Scheduler] Kampagne abgeschlossen: {result_msg}")


def _update_next_run():
    job = _scheduler.get_job(SCHEDULER_STATUS["job_id"])
    if job and job.next_run_time:
        SCHEDULER_STATUS["next_run"] = job.next_run_time.strftime("%Y-%m-%d %H:%M")
    else:
        SCHEDULER_STATUS["next_run"] = None


def schedule_campaign(send_days: list, send_hour: int, send_minute: int):
    """Richtet den täglichen Job ein (überschreibt vorhandenen)."""
    job_id = SCHEDULER_STATUS["job_id"]

    if _scheduler.get_job(job_id):
        _scheduler.remove_job(job_id)

    if not send_days:
        logger.info("[Scheduler] Keine Versandtage – Job nicht eingerichtet.")
        return

    # CronTrigger mit ausgewählten Wochentagen
    days_str = ",".join(str(d) for d in send_days)
    trigger = CronTrigger(
        day_of_week=days_str,
        hour=send_hour,
        minute=send_minute,
        timezone="Europe/Berlin"
    )

    _scheduler.add_job(
        _run_daily_campaign,
        trigger=trigger,
        id=job_id,
        name="MR Digital Tägliche Akquise",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    _update_next_run()
    logger.info(f"[Scheduler] Job eingerichtet: Tage={days_str}, {send_hour:02d}:{send_minute:02d}")


def run_now():
    """Startet die Kampagne sofort (manuell)."""
    if SCHEDULER_STATUS["running"]:
        return {"ok": False, "message": "Kampagne läuft bereits."}
    _scheduler.add_job(
        _run_daily_campaign,
        id="manual_run",
        replace_existing=True,
        name="Manueller Versand",
    )
    return {"ok": True, "message": "✅ Kampagne manuell gestartet."}


def stop():
    """Stoppt den laufenden Versand."""
    SCHEDULER_STATUS["running"] = False
    return {"ok": True, "message": "⏹ Versand gestoppt."}


def get_status() -> dict:
    _update_next_run()
    return SCHEDULER_STATUS.copy()


def init_scheduler_from_db():
    """Lädt Kampagnen-Einstellungen aus DB und richtet Scheduler ein."""
    try:
        from data_store import get_active_campaign
        campaign = get_active_campaign()
        if campaign:
            days = [int(d) for d in campaign.get("send_days", "0,1,2,3,4").split(",")]
            schedule_campaign(days, campaign.get("send_hour", 9), campaign.get("send_minute", 0))
    except Exception as e:
        logger.warning(f"[Scheduler] Init-Fehler: {e}")
