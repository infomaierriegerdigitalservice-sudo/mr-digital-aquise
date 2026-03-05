"""
email_generator.py – Personalisierte Akquise-Email-Templates
MR Digital – Akquise Automatisierung v2
"""

from config import SENDER_NAME, SENDER_TITLE, WEBSITE, PHONE, CALENDLY_LINK
from data_store import get_setting

# Branchen-spezifische Schmerzpunkte für die Personalisierung
NICHE_PAIN_POINTS = {
    "Elektriker": {
        "pain": "Angebote manuell erstellen, Terminkoordination per Telefon und Kundenrückrufe vergessen",
        "benefit": "Angebote automatisch verschicken, Termine online buchen lassen und Kunden automatisch erinnern",
        "time_save": "2–3 Stunden",
    },
    "Klempner": {
        "pain": "Notfallaufträge koordinieren, Rechnungen manuell schreiben und Folgetermine vergessen",
        "benefit": "Auftragseingang automatisieren, Rechnungen automatisch erstellen und Kunden nachfassen",
        "time_save": "3–4 Stunden",
    },
    "Maler": {
        "pain": "Kostenvoranschläge manuell ausarbeiten, Kundenanfragen spät beantworten und Projekte nachverfolgen",
        "benefit": "Kostenvoranschläge automatisch erstellen, sofort auf Anfragen reagieren und Projekte tracken",
        "time_save": "2–3 Stunden",
    },
    "Schreiner": {
        "pain": "Auftragsplanung manuell pflegen, Materialbestellungen koordinieren und Kundenkommunikation managen",
        "benefit": "Aufträge digital planen, Bestellungen automatisch auslösen und Kunden proaktiv informieren",
        "time_save": "2–4 Stunden",
    },
    "Dachdecker": {
        "pain": "Inspektionstermine koordinieren, Angebote manuell schreiben und Wartungsaufträge vergessen",
        "benefit": "Termine selbst buchen lassen, Angebote automatisch erstellen und Wartungserinnerungen automatisch senden",
        "time_save": "3–5 Stunden",
    },
    "Sanitär": {
        "pain": "Wartungsverträge manuell verwalten, Leads nicht zeitnah kontaktieren und Aufträge doppelt anlegen",
        "benefit": "Wartungsverträge automatisch verlängern, Leads sofort kontaktieren und Aufträge digital verwalten",
        "time_save": "2–3 Stunden",
    },
    "Heizung": {
        "pain": "Jährliche Wartungen manuell koordinieren, Energieberatungen aufwändig dokumentieren",
        "benefit": "Wartungstermine automatisch planen, Berichte automatisch erstellen und Kunden proaktiv erinnern",
        "time_save": "3–4 Stunden",
    },
    "Heizungsbauer": {
        "pain": "Jährliche Wartungen manuell koordinieren, Energieberatungen aufwändig dokumentieren",
        "benefit": "Wartungstermine automatisch planen, Berichte automatisch erstellen und Kunden proaktiv erinnern",
        "time_save": "3–4 Stunden",
    },
    "Kfz-Werkstatt": {
        "pain": "Termine telefonisch koordinieren, Serviceerinnerungen manuell verschicken und Rechnungen aufwändig erstellen",
        "benefit": "Online-Terminbuchung einrichten, Serviceerinnerungen automatisch senden und Rechnungen automatisieren",
        "time_save": "2–3 Stunden",
    },
    "Friseur": {
        "pain": "Terminbuchungen per Telefon entgegennehmen, Ausfälle kurzfristig auffüllen und Stammkunden erinnern",
        "benefit": "Online-Buchungssystem einrichten, freie Termine automatisch füllen und Kunden automatisch erinnern",
        "time_save": "1–2 Stunden",
    },
    "Steuerberater": {
        "pain": "Mandantenunterlagen per Email koordinieren, Fristen manuell tracken und Mandanten erinnern",
        "benefit": "Unterlagen automatisch einsammeln, Fristen automatisch tracken und Mandanten proaktiv informieren",
        "time_save": "3–5 Stunden",
    },
    "Reinigungsservice": {
        "pain": "Reinigungsaufträge manuell planen, Personal koordinieren und Rechnungen einzeln erstellen",
        "benefit": "Aufträge automatisch planen, Personal digital koordinieren und Rechnungen automatisch erstellen",
        "time_save": "2–3 Stunden",
    },
    "Gartenservice": {
        "pain": "Saisonale Aufträge manuell koordinieren, Kundentermine telefonisch vereinbaren und Angebote aufwändig erstellen",
        "benefit": "Saisoneinsätze automatisch planen, Termine online buchen lassen und Angebote automatisch verschicken",
        "time_save": "2–4 Stunden",
    },
}

DEFAULT_PAIN = {
    "pain": "wiederkehrende Aufgaben manuell erledigen, Kunden spät antworten und wertvolle Zeit mit Verwaltung verlieren",
    "benefit": "Routineaufgaben automatisieren, Kunden sofort antworten und Zeit für das Wesentliche gewinnen",
    "time_save": "2–3 Stunden",
}


def generate_email(lead: dict) -> dict:
    """Generiert eine personalisierte Akquise-Email für einen Lead."""

    # Credentials aus DB-Settings holen (könnten überschrieben sein)
    calendly = get_setting("calendly_link") or CALENDLY_LINK
    sender_name = get_setting("sender_name") or SENDER_NAME
    sender_phone = get_setting("sender_phone") or PHONE

    niche = lead.get("category", "Handwerk")
    pain_data = NICHE_PAIN_POINTS.get(niche, DEFAULT_PAIN)

    company = lead.get("name", "Ihrem Unternehmen")
    city = lead.get("city", "")
    rating = lead.get("rating", "")

    city_phrase = f"in {city} und Umgebung" if city else "in Ihrer Region"
    rating_phrase = ""
    if rating and rating.strip():
        rating_phrase = f"Ihre {rating} sprechen für sich – genau solche vertrauenswürdigen Betriebe sind unsere Lieblingskunden."

    subject_tmpl = get_setting("email_subject")
    if not subject_tmpl:
        subject_tmpl = "Potenzial für {company} – Mehr Zeit durch smarte Automatisierung"

    html_tmpl = get_setting("email_template_html")
    if not html_tmpl:
        html_tmpl = f"""<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; line-height: 1.6;">

<p>Sehr geehrte Damen und Herren von <strong>{{company}}</strong>,</p>

<p>mein Name ist <strong>{{sender_name}}</strong> von MR DigitalServices. Ich bin bei Recherchen {{city_phrase}} auf Ihr Unternehmen aufmerksam geworden und Ihr Profil hat mich direkt angesprochen.</p>

{f'<p><em>{rating_phrase}</em></p>' if rating_phrase else ''}

<p>Aus der Zusammenarbeit mit anderen {{niche}}-Betrieben wissen wir, dass oft im Hintergrund viel Zeit verloren geht – speziell wenn es darum geht, <strong>{{pain}}</strong>. Genau hier lässt sich durch simple Automatisierungen massiv Zeit einsparen.</p>

<p>Wir haben uns darauf spezialisiert, genau solche Prozesse reibungslos zu digitalisieren, sodass Sie <strong>{{benefit}}</strong>. Unsere Kunden sparen dadurch oft über <strong>{{time_save}}</strong> ein, die direkt wieder in produktive Arbeit oder Freizeit fließen können.</p>

<p>Ohne technisches Vorwissen für Sie umsetzbar. Ich zeige Ihnen gerne in einem kostenfreien, 15-minütigen Gespräch via Google Meet oder Zoom, wie einfach das für <strong>{{company}}</strong> aussehen kann.</p>

<p style="text-align: left; margin: 25px 0;">
  <a href="{{calendly}}" 
     style="background: #2563eb; color: white; padding: 12px 24px; border-radius: 6px; 
            text-decoration: none; font-weight: bold; display: inline-block;">
    👉 Zum Kalender: Kostenfreies Erstgespräch wählen
  </a>
</p>

<p>Ich freue mich auf unseren Austausch.</p>

<p>Mit besten Grüßen,</p>

<p>
  <strong>{{sender_name}}</strong><br>
  <em>MR DigitalServices</em><br>
  Tel: {{sender_phone}}<br>
  Web: <a href="{{website}}" style="color: #2563eb;">{{website}}</a>
</p>

<hr style="border: none; border-top: 1px solid #eee; margin-top: 40px;">
<p style="font-size: 11px; color: #999; text-align: center;">
  MR DigitalServices · {{website}}<br>
  Sie erhalten diese E-Mail, da Ihr Unternehmen online öffentlich verzeichnet ist.<br>
  <a href="http://localhost:5001/unsubscribe?email={lead.get('email', '')}" 
     style="color: #999;">Keine weiteren E-Mails erhalten</a>
</p>
</body>
</html>"""

    text_tmpl = get_setting("email_template_text")
    if not text_tmpl:
        text_tmpl = f"""Sehr geehrte Damen und Herren von {{company}},

mein Name ist {{sender_name}} von MR DigitalServices. Ich bin bei Recherchen {{city_phrase}} auf Ihr Unternehmen aufmerksam geworden.

Aus der Zusammenarbeit mit anderen {{niche}}-Betrieben wissen wir, dass oft viel Zeit verloren geht, speziell wenn es darum geht, {{pain}}.

Wir haben uns darauf spezialisiert, genau solche Prozesse zu digitalisieren, sodass Sie {{benefit}}. Unsere Kunden sparen dadurch oft über {{time_save}} ein.

Ich zeige Ihnen gerne in einem kostenfreien 15-minütigen Gespräch via Google Meet, wie einfach das für {{company}} aussehen kann.

Zum Kalender (Termin wählen): {{calendly}}

Ich freue mich auf unseren Austausch.

Mit besten Grüßen,

{{sender_name}}
MR DigitalServices
Tel: {{sender_phone}}
Web: {{website}}

---
Abmelden: http://localhost:5001/unsubscribe?email={lead.get('email', '')}
"""

    def _replace_vars(text: str) -> str:
        return text.replace("{company}", company)\
                   .replace("{niche}", niche)\
                   .replace("{city_phrase}", city_phrase)\
                   .replace("{pain}", pain_data['pain'])\
                   .replace("{benefit}", pain_data['benefit'])\
                   .replace("{time_save}", pain_data['time_save'])\
                   .replace("{sender_name}", sender_name)\
                   .replace("{sender_phone}", sender_phone)\
                   .replace("{calendly}", calendly)\
                   .replace("{website}", WEBSITE)

    subject = _replace_vars(subject_tmpl)
    body_html = _replace_vars(html_tmpl)
    body_text = _replace_vars(text_tmpl)

    return {
        "lead_id": lead.get("id"),
        "to_addr": lead.get("email", ""),
        "to_name": company,
        "subject": subject,
        "body_html": body_html,
        "body_text": body_text,
    }
