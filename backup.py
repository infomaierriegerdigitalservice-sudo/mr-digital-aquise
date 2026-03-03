"""
backup.py – Automatisches Backup-System
MR Digital – Akquise Automatisierung v2
"""

import os
import zipfile
import logging
import csv
from datetime import datetime, timedelta
from config import DATA_DIR, BACKUP_DIR, DB_PATH, BACKUP_KEEP_DAYS
from data_store import get_all_leads, get_emails_sent, get_blacklist

logger = logging.getLogger(__name__)


def create_backup() -> dict:
    """Erstellt ein ZIP-Backup der Datenbank + CSV-Exports."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    zip_name = f"backup_{ts}.zip"
    zip_path = os.path.join(BACKUP_DIR, zip_name)

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # SQLite-Datenbank
            if os.path.exists(DB_PATH):
                zf.write(DB_PATH, "akquise.db")

            # CSV-Exports
            leads = get_all_leads()
            if leads:
                leads_csv = os.path.join(BACKUP_DIR, f"leads_{ts}.csv")
                _write_csv(leads_csv, leads)
                zf.write(leads_csv, "leads.csv")
                os.remove(leads_csv)

            emails = get_emails_sent(limit=10000)
            if emails:
                emails_csv = os.path.join(BACKUP_DIR, f"emails_{ts}.csv")
                _write_csv(emails_csv, emails)
                zf.write(emails_csv, "emails_sent.csv")
                os.remove(emails_csv)

            blacklist = get_blacklist()
            if blacklist:
                bl_csv = os.path.join(BACKUP_DIR, f"blacklist_{ts}.csv")
                _write_csv(bl_csv, blacklist)
                zf.write(bl_csv, "blacklist.csv")
                os.remove(bl_csv)

        size = os.path.getsize(zip_path)

        # In DB registrieren
        from data_store import get_conn
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO backups (filename, path, size_bytes, created_at) VALUES (?, ?, ?, ?)",
                (zip_name, zip_path, size, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )

        # Alte Backups aufräumen
        _cleanup_old_backups()

        logger.info(f"[Backup] ✅ Erstellt: {zip_name} ({size // 1024} KB)")
        return {
            "ok": True,
            "filename": zip_name,
            "path": zip_path,
            "size_kb": round(size / 1024, 1),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    except Exception as e:
        logger.error(f"[Backup] Fehler: {e}")
        return {"ok": False, "message": str(e)}


def get_all_backups() -> list:
    """Gibt alle registrierten Backups zurück."""
    from data_store import get_conn
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM backups ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def export_csv_only() -> str:
    """Erstellt nur einen temporären CSV-Export (Leads) und gibt Pfad zurück."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(BACKUP_DIR, f"leads_export_{ts}.csv")
    leads = get_all_leads()
    _write_csv(path, leads)
    return path


def _write_csv(path: str, data: list):
    if not data:
        return
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


def _cleanup_old_backups():
    """Löscht Backups älter als BACKUP_KEEP_DAYS."""
    cutoff = datetime.now() - timedelta(days=BACKUP_KEEP_DAYS)
    from data_store import get_conn
    with get_conn() as conn:
        old = conn.execute(
            "SELECT path FROM backups WHERE created_at < ?",
            (cutoff.strftime("%Y-%m-%d"),)
        ).fetchall()
        for row in old:
            try:
                if os.path.exists(row["path"]):
                    os.remove(row["path"])
            except Exception:
                pass
        conn.execute(
            "DELETE FROM backups WHERE created_at < ?",
            (cutoff.strftime("%Y-%m-%d"),)
        )
