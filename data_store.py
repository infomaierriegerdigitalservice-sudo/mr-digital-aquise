"""
data_store.py – SQLite Datenbank
MR Digital – Akquise Automatisierung v2
"""

import sqlite3
import os
from datetime import datetime
from config import DB_PATH, DATA_DIR


def get_conn():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Erstellt alle Tabellen falls nicht vorhanden."""
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS leads (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            category    TEXT,
            city        TEXT,
            phone       TEXT,
            website     TEXT,
            email       TEXT,
            rating      TEXT,
            source      TEXT DEFAULT 'Manuell',
            status      TEXT DEFAULT 'Neu',
            notes       TEXT DEFAULT '',
            created_at  TEXT,
            contacted_at TEXT
        );

        CREATE TABLE IF NOT EXISTS emails_sent (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id     INTEGER REFERENCES leads(id),
            to_addr     TEXT,
            to_name     TEXT,
            subject     TEXT,
            body        TEXT,
            status      TEXT DEFAULT 'Gesendet',
            error_msg   TEXT DEFAULT '',
            sent_at     TEXT
        );

        CREATE TABLE IF NOT EXISTS blacklist (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT UNIQUE NOT NULL,
            company     TEXT,
            reason      TEXT DEFAULT 'Abgemeldet',
            added_at    TEXT
        );

        CREATE TABLE IF NOT EXISTS campaigns (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT,
            niche       TEXT,
            cities      TEXT,
            emails_per_day INTEGER DEFAULT 30,
            send_days   TEXT DEFAULT '0,1,2,3,4',
            send_hour   INTEGER DEFAULT 9,
            send_minute INTEGER DEFAULT 0,
            active      INTEGER DEFAULT 1,
            created_at  TEXT,
            updated_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS settings (
            key     TEXT PRIMARY KEY,
            value   TEXT
        );

        CREATE TABLE IF NOT EXISTS backups (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            filename    TEXT,
            path        TEXT,
            size_bytes  INTEGER,
            created_at  TEXT
        );
        """)


# ──────────────────────────────────────
# LEADS
# ──────────────────────────────────────

def save_lead(lead: dict) -> tuple[bool, int]:
    """Speichert Lead. Gibt (True, id) wenn neu, (False, id) wenn Duplikat."""
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM leads WHERE name = ? OR (email != '' AND email = ?)",
            (lead.get("name", ""), lead.get("email", ""))
        ).fetchone()
        if existing:
            return False, existing["id"]

        lead["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = conn.execute(
            """INSERT INTO leads (name, category, city, phone, website, email, rating, source, created_at)
               VALUES (:name, :category, :city, :phone, :website, :email, :rating, :source, :created_at)""",
            lead
        )
        return True, cur.lastrowid


def get_all_leads(status=None, category=None, city=None) -> list:
    with get_conn() as conn:
        q = "SELECT * FROM leads WHERE 1=1"
        params = []
        if status:
            q += " AND status = ?"
            params.append(status)
        if category:
            q += " AND category = ?"
            params.append(category)
        if city:
            q += " AND city = ?"
            params.append(city)
        q += " ORDER BY created_at DESC"
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]


def update_lead_status(lead_id: int, status: str, contacted_at: str = None):
    with get_conn() as conn:
        if contacted_at:
            conn.execute(
                "UPDATE leads SET status=?, contacted_at=? WHERE id=?",
                (status, contacted_at, lead_id)
            )
        else:
            conn.execute("UPDATE leads SET status=? WHERE id=?", (status, lead_id))


def delete_lead(lead_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM leads WHERE id=?", (lead_id,))


def add_to_blacklist(email: str, company: str = "", reason: str = "Abgemeldet"):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO blacklist (email, company, reason, added_at) VALUES (?, ?, ?, ?)",
            (email, company, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.execute("UPDATE leads SET status='Blacklist' WHERE email=?", (email,))


def is_blacklisted(email: str) -> bool:
    with get_conn() as conn:
        return conn.execute(
            "SELECT 1 FROM blacklist WHERE email=?", (email,)
        ).fetchone() is not None


def get_blacklist() -> list:
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM blacklist ORDER BY added_at DESC")]


# ──────────────────────────────────────
# EMAILS
# ──────────────────────────────────────

def save_email_sent(record: dict):
    record["sent_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO emails_sent (lead_id, to_addr, to_name, subject, body, status, error_msg, sent_at)
               VALUES (:lead_id, :to_addr, :to_name, :subject, :body, :status, :error_msg, :sent_at)""",
            record
        )


def get_emails_sent(limit: int = 100) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM emails_sent ORDER BY sent_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def count_emails_today() -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM emails_sent WHERE sent_at LIKE ? AND status='Gesendet'",
            (f"{today}%",)
        ).fetchone()
        return row["cnt"] if row else 0


# ──────────────────────────────────────
# CAMPAIGNS
# ──────────────────────────────────────

def get_active_campaign() -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM campaigns WHERE active=1 ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def save_campaign(data: dict):
    data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        existing = conn.execute("SELECT id FROM campaigns WHERE active=1").fetchone()
        if existing:
            conn.execute(
                """UPDATE campaigns SET name=:name, niche=:niche, cities=:cities,
                   emails_per_day=:emails_per_day, send_days=:send_days,
                   send_hour=:send_hour, send_minute=:send_minute, updated_at=:updated_at
                   WHERE active=1""",
                data
            )
        else:
            data["created_at"] = data["updated_at"]
            conn.execute(
                """INSERT INTO campaigns (name, niche, cities, emails_per_day, send_days,
                   send_hour, send_minute, active, created_at, updated_at)
                   VALUES (:name, :niche, :cities, :emails_per_day, :send_days,
                   :send_hour, :send_minute, 1, :created_at, :updated_at)""",
                data
            )


# ──────────────────────────────────────
# SETTINGS
# ──────────────────────────────────────

def get_setting(key: str, default=None):
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )


# ──────────────────────────────────────
# STATS
# ──────────────────────────────────────

def get_stats() -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        total_leads = conn.execute("SELECT COUNT(*) as c FROM leads").fetchone()["c"]
        new_leads = conn.execute("SELECT COUNT(*) as c FROM leads WHERE status='Neu'").fetchone()["c"]
        contacted = conn.execute("SELECT COUNT(*) as c FROM leads WHERE status='Kontaktiert'").fetchone()["c"]
        replied = conn.execute("SELECT COUNT(*) as c FROM leads WHERE status='Antwort'").fetchone()["c"]
        appointments = conn.execute("SELECT COUNT(*) as c FROM leads WHERE status='Termin'").fetchone()["c"]
        blacklisted = conn.execute("SELECT COUNT(*) as c FROM blacklist").fetchone()["c"]

        emails_today = conn.execute(
            "SELECT COUNT(*) as c FROM emails_sent WHERE sent_at LIKE ? AND status='Gesendet'",
            (f"{today}%",)
        ).fetchone()["c"]
        emails_total = conn.execute(
            "SELECT COUNT(*) as c FROM emails_sent WHERE status='Gesendet'"
        ).fetchone()["c"]
        errors_total = conn.execute(
            "SELECT COUNT(*) as c FROM emails_sent WHERE status='Fehler'"
        ).fetchone()["c"]

        # Letzte 7 Tage
        daily = []
        for i in range(6, -1, -1):
            from datetime import timedelta
            day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            cnt = conn.execute(
                "SELECT COUNT(*) as c FROM emails_sent WHERE sent_at LIKE ? AND status='Gesendet'",
                (f"{day}%",)
            ).fetchone()["c"]
            daily.append({"date": day, "count": cnt})

        return {
            "total_leads": total_leads,
            "new_leads": new_leads,
            "contacted": contacted,
            "replied": replied,
            "appointments": appointments,
            "blacklisted": blacklisted,
            "emails_today": emails_today,
            "emails_total": emails_total,
            "errors_total": errors_total,
            "daily": daily,
        }


# Initialisiere DB beim Import
init_db()
