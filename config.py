"""
config.py – Zentrale Konfiguration
MR Digital – Akquise Automatisierung v2
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────
# SMTP / EMAIL
# ──────────────────────────────────────
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "info.maier.rieger.digitalservice@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

# ──────────────────────────────────────
# ABSENDER / SIGNATUR
# ──────────────────────────────────────
SENDER_NAME = "Nicklas Rieger – MR Digital"
SENDER_TITLE = "Gründer & Geschäftsführer – MR DigitalServices"
WEBSITE = "https://mrdigitalservice.de"
PHONE = "+49 XXX XXXXXXXXX"  # In Einstellungen anpassen
CALENDLY_LINK = os.getenv("CALENDLY_LINK", "https://calendly.com/mr-digital")

# ──────────────────────────────────────
# VERSAND-LIMITS (DSGVO-konform)
# ──────────────────────────────────────
MAX_EMAILS_PER_DAY = 30          # Sicherer Startwert
MAX_EMAILS_PER_HOUR = 10         # Nicht zu viele auf einmal
SEND_DELAY_SECONDS = (30, 90)    # Zufällige Pause zwischen Mails (Min, Max)

# ──────────────────────────────────────
# SCHEDULING (Standard-Einstellungen)
# ──────────────────────────────────────
DEFAULT_SEND_DAYS = [0, 1, 2, 3, 4]   # Mo–Fr (0=Montag)
DEFAULT_SEND_HOUR = 9                  # Uhrzeit: 09:00
DEFAULT_SEND_MINUTE = 0

# ──────────────────────────────────────
# RESEARCH
# ──────────────────────────────────────
DEFAULT_NICHES = [
    "Elektriker",
    "Klempner",
    "Maler",
    "Schreiner",
    "Dachdecker",
    "Sanitär",
    "Heizung",
    "Kfz-Werkstatt",
    "Friseur",
    "Zahnarzt",
    "Steuerberater",
    "Immobilienmakler",
    "Reinigungsservice",
    "Umzugsunternehmen",
    "Gartenservice",
]

DEFAULT_CITIES = [
    "München", "Berlin", "Hamburg", "Frankfurt", "Köln",
    "Stuttgart", "Dresden", "Düsseldorf", "Leipzig", "Nürnberg",
]

MAX_RESEARCH_RESULTS = 10   # Leads pro Suchanfrage

# ──────────────────────────────────────
# BACKUP
# ──────────────────────────────────────
BACKUP_KEEP_DAYS = 30
AUTO_BACKUP_ENABLED = True

# ──────────────────────────────────────
# PFADE
# ──────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "akquise.db")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
LOG_PATH = os.path.join(DATA_DIR, "app.log")

SECRET_KEY = os.getenv("SECRET_KEY", "mr-digital-v2-secret")
