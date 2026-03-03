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

    subject = f"Automatisierung für {company} – 15 Min. kostenlose Analyse"

    body_html = f"""<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; line-height: 1.6;">

<p>Sehr geehrte Damen und Herren von <strong>{company}</strong>,</p>

<p>mein Name ist <strong>{sender_name}</strong>, Gründer von 
<a href="{WEBSITE}" style="color: #6366f1;">MR DigitalServices</a>. 
Ich bin auf Ihr Unternehmen aufmerksam geworden und sehe großes Potenzial.</p>

<p>Viele <strong>{niche}-Betriebe {city_phrase}</strong> verlieren täglich Zeit, weil sie 
<strong>{pain_data['pain']}</strong>. Das muss nicht so sein.</p>

<p>Wir helfen handwerklichen Betrieben dabei, <strong>{pain_data['benefit']}</strong> – 
ohne technisches Vorwissen, ohne teure Software.</p>

<p>Unsere Kunden sparen im Durchschnitt <strong>{pain_data['time_save']} täglich</strong> 
– Zeit, die sie für ihre eigentliche Arbeit nutzen können.</p>

{f'<p><em>{rating_phrase}</em></p>' if rating_phrase else ''}

<p>Ich würde Ihnen gerne in einem unverbindlichen <strong>15-Minuten-Gespräch</strong> 
zeigen, welche Prozesse bei <strong>{company}</strong> am schnellsten automatisiert 
werden können – kostenlos und ohne Verpflichtung.</p>

<p style="text-align: center; margin: 30px 0;">
  <a href="{calendly}" 
     style="background: #6366f1; color: white; padding: 12px 28px; border-radius: 8px; 
            text-decoration: none; font-weight: bold; display: inline-block;">
    👉 Kostenloses Erstgespräch buchen
  </a>
</p>

<p>Mit freundlichen Grüßen,</p>

<table style="border-top: 2px solid #6366f1; padding-top: 16px; margin-top: 8px;">
<tr>
  <td>
    <strong style="color: #6366f1;">{sender_name}</strong><br>
    <em>{sender_phone}</em><br>
    <a href="{WEBSITE}" style="color: #6366f1;">{WEBSITE}</a><br>
    <a href="{calendly}" style="color: #888; font-size: 12px;">Termin buchen</a>
  </td>
</tr>
</table>

<hr style="border: none; border-top: 1px solid #eee; margin-top: 40px;">
<p style="font-size: 11px; color: #999; text-align: center;">
  MR DigitalServices · {WEBSITE} · {sender_phone}<br>
  Sie erhalten diese Email, weil wir Ihr Unternehmen auf Google Maps gefunden haben.<br>
  <a href="http://localhost:5001/unsubscribe?email={lead.get('email', '')}" 
     style="color: #999;">Abmelden / Unsubscribe</a>
</p>
</body>
</html>"""

    body_text = f"""Sehr geehrte Damen und Herren von {company},

mein Name ist {sender_name}, Gründer von MR DigitalServices.

Viele {niche}-Betriebe {city_phrase} verlieren täglich Zeit, weil sie
{pain_data['pain']}.

Wir helfen dabei, {pain_data['benefit']} – ohne technisches Vorwissen.

Unsere Kunden sparen im Durchschnitt {pain_data['time_save']} täglich.

Kostenloses 15-Min-Gespräch buchen: {calendly}

Mit freundlichen Grüßen,
{sender_name}
{WEBSITE} | {sender_phone}

---
Abmelden: http://localhost:5001/unsubscribe?email={lead.get('email', '')}
"""

    return {
        "lead_id": lead.get("id"),
        "to_addr": lead.get("email", ""),
        "to_name": company,
        "subject": subject,
        "body_html": body_html,
        "body_text": body_text,
    }
