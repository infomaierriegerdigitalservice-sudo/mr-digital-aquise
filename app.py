"""
app.py – Flask Backend & API
MR Digital – Akquise Automatisierung v2
"""

import json
import logging
import os
from flask import (
    Flask, render_template, Response, jsonify,
    request, send_file, redirect, session, url_for
)
from functools import wraps
from config import SECRET_KEY, DATA_DIR, DEFAULT_NICHES, DEFAULT_CITIES
import data_store as db
from data_store import (
    get_all_leads, get_emails_sent, get_stats, get_blacklist,
    add_to_blacklist, delete_lead, update_lead_status, save_lead,
    get_active_campaign, save_campaign, get_setting, set_setting,
    is_blacklisted,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(DATA_DIR, "app.log"), encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

# ──────────────────────────────────────
# AUTH
# ──────────────────────────────────────
DASHBOARD_PASSWORD = "MaierRieger.1234"

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("auth"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ──────────────────────────────────────
# INIT
# ──────────────────────────────────────

os.makedirs(DATA_DIR, exist_ok=True)

from scheduler import init_scheduler_from_db
init_scheduler_from_db()


# ──────────────────────────────────────
# LOGIN / LOGOUT
# ──────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("auth"):
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        pw = request.form.get("password", "")
        if pw == DASHBOARD_PASSWORD:
            session["auth"] = True
            return redirect(url_for("index"))
        error = "Falsches Passwort. Bitte erneut versuchen."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ──────────────────────────────────────
# FRONTEND
# ──────────────────────────────────────

@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/unsubscribe")
def unsubscribe():
    email = request.args.get("email", "").strip()
    if email:
        add_to_blacklist(email, reason="Abgemeldet über Link")
        return f"""
        <html><body style="font-family:Arial;text-align:center;padding:60px;color:#333">
        <h2>✅ Erfolgreich abgemeldet</h2>
        <p>{email} wurde aus unserem Verteiler entfernt.</p>
        <p style="color:#888;font-size:14px">Sie erhalten keine weiteren Emails von MR Digital.</p>
        </body></html>
        """
    return "Ungültige Anfrage", 400


# ──────────────────────────────────────
# STATS & DASHBOARD
# ──────────────────────────────────────

@app.route("/api/stats")
@login_required
def api_stats():
    return jsonify(get_stats())


@app.route("/api/scheduler/status")
@login_required
def api_scheduler_status():
    from scheduler import get_status
    return jsonify(get_status())


# ──────────────────────────────────────
# LEADS
# ──────────────────────────────────────

@app.route("/api/leads")
@login_required
def api_leads():
    status = request.args.get("status")
    category = request.args.get("category")
    city = request.args.get("city")
    return jsonify(get_all_leads(status=status, category=category, city=city))


@app.route("/api/leads/add", methods=["POST"])
@login_required
def api_leads_add():
    data = request.json or {}
    if not data.get("name") or not data.get("email"):
        return jsonify({"ok": False, "message": "Name und Email sind pflicht."}), 400
    data.setdefault("source", "Manuell")
    data.setdefault("status", "Neu")
    new, lead_id = save_lead(data)
    if new:
        return jsonify({"ok": True, "message": "Lead gespeichert.", "id": lead_id})
    return jsonify({"ok": False, "message": "Lead existiert bereits."})


@app.route("/api/leads/<int:lead_id>/status", methods=["POST"])
@login_required
def api_lead_status(lead_id):
    data = request.json or {}
    status = data.get("status")
    if not status:
        return jsonify({"ok": False, "message": "Status fehlt."}), 400
    update_lead_status(lead_id, status)
    return jsonify({"ok": True})


@app.route("/api/leads/<int:lead_id>/delete", methods=["POST"])
@login_required
def api_lead_delete(lead_id):
    delete_lead(lead_id)
    return jsonify({"ok": True})


@app.route("/api/leads/<int:lead_id>/blacklist", methods=["POST"])
@login_required
def api_lead_blacklist(lead_id):
    leads = get_all_leads()
    lead = next((l for l in leads if l["id"] == lead_id), None)
    if lead:
        add_to_blacklist(lead.get("email", ""), lead.get("name", ""), "Manuell blockiert")
    return jsonify({"ok": True})


@app.route("/api/leads/export")
@login_required
def api_leads_export():
    from backup import export_csv_only
    path = export_csv_only()
    return send_file(path, as_attachment=True,
                     download_name="mr_digital_leads.csv", mimetype="text/csv")


# ──────────────────────────────────────
# EMAILS
# ──────────────────────────────────────

@app.route("/api/emails")
@login_required
def api_emails():
    limit = int(request.args.get("limit", 100))
    return jsonify(get_emails_sent(limit=limit))


@app.route("/api/emails/send/<int:lead_id>", methods=["POST"])
@login_required
def api_send_email(lead_id):
    """Sendet eine Email an einen einzelnen Lead (manuell)."""
    leads = get_all_leads()
    lead = next((l for l in leads if l["id"] == lead_id), None)
    if not lead:
        return jsonify({"ok": False, "message": "Lead nicht gefunden."}), 404
    if not lead.get("email"):
        return jsonify({"ok": False, "message": "Kein Email bei diesem Lead."})
    if is_blacklisted(lead["email"]):
        return jsonify({"ok": False, "message": "Lead ist in der Blacklist."})

    from email_generator import generate_email
    from mailer import send_email
    email_data = generate_email(lead)
    result = send_email(lead, email_data["subject"],
                        email_data["body_html"], email_data["body_text"])
    return jsonify(result)


@app.route("/api/emails/preview/<int:lead_id>")
@login_required
def api_email_preview(lead_id):
    """Gibt Email-Preview zurück ohne zu senden."""
    leads = get_all_leads()
    lead = next((l for l in leads if l["id"] == lead_id), None)
    if not lead:
        return jsonify({"ok": False, "message": "Lead nicht gefunden."}), 404
    from email_generator import generate_email
    email_data = generate_email(lead)
    return jsonify({"ok": True, "email": email_data})


# ──────────────────────────────────────
# BLACKLIST
# ──────────────────────────────────────

@app.route("/api/blacklist")
@login_required
def api_blacklist():
    return jsonify(get_blacklist())


@app.route("/api/blacklist/add", methods=["POST"])
@login_required
def api_blacklist_add():
    data = request.json or {}
    email = data.get("email", "").strip()
    if not email:
        return jsonify({"ok": False, "message": "Email fehlt."}), 400
    add_to_blacklist(email, data.get("company", ""), data.get("reason", "Manuell"))
    return jsonify({"ok": True, "message": f"{email} zur Blacklist hinzugefügt."})


# ──────────────────────────────────────
# KAMPAGNE
# ──────────────────────────────────────

@app.route("/api/campaign")
@login_required
def api_get_campaign():
    return jsonify(get_active_campaign() or {})


@app.route("/api/campaign/save", methods=["POST"])
@login_required
def api_save_campaign():
    data = request.json or {}
    required = ["niche", "cities", "emails_per_day"]
    for field in required:
        if not data.get(field):
            return jsonify({"ok": False, "message": f"Feld '{field}' fehlt."}), 400

    data.setdefault("name", f"Kampagne: {data['niche']}")
    data["emails_per_day"] = int(data["emails_per_day"])
    data["send_hour"] = int(data.get("send_hour", 9))
    data["send_minute"] = int(data.get("send_minute", 0))

    save_campaign(data)

    # Scheduler neu einrichten
    from scheduler import schedule_campaign
    days = [int(d) for d in data.get("send_days", "0,1,2,3,4").split(",")]
    schedule_campaign(days, data["send_hour"], data["send_minute"])

    return jsonify({"ok": True, "message": "✅ Kampagne gespeichert & Scheduler aktualisiert."})


# ──────────────────────────────────────
# SCHEDULER
# ──────────────────────────────────────

@app.route("/api/scheduler/run", methods=["POST"])
@login_required
def api_scheduler_run():
    from scheduler import run_now
    return jsonify(run_now())


@app.route("/api/scheduler/stop", methods=["POST"])
@login_required
def api_scheduler_stop():
    from scheduler import stop
    return jsonify(stop())


# ──────────────────────────────────────
# RESEARCH (SSE-Stream)
# ──────────────────────────────────────

@app.route("/api/research/stream")
@login_required
def api_research_stream():
    query = request.args.get("query", "").strip()
    city = request.args.get("city", "").strip()
    source = request.args.get("source", "auto")
    max_results = int(request.args.get("max", 8))

    if not query:
        return jsonify({"error": "query fehlt"}), 400

    def generate():
        from researcher import research_stream
        for event in research_stream(query, city, source, max_results):
            payload = json.dumps(event, ensure_ascii=False)
            yield f"data: {payload}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/research/save", methods=["POST"])
@login_required
def api_research_save():
    """Speichert einen recherchierten Lead in die DB."""
    lead = request.json or {}
    if not lead.get("name"):
        return jsonify({"ok": False, "message": "Name fehlt."}), 400
    lead.setdefault("source", "Research-Tool")
    lead.setdefault("status", "Neu")
    new, lead_id = save_lead(lead)
    if new:
        return jsonify({"ok": True, "message": "Lead gespeichert.", "id": lead_id})
    return jsonify({"ok": False, "message": "Lead existiert bereits.", "id": lead_id})


# ──────────────────────────────────────
# EINSTELLUNGEN
# ──────────────────────────────────────

@app.route("/api/settings")
@login_required
def api_get_settings():
    keys = [
        "gmail_address", "gmail_app_password", "calendly_link",
        "sender_name", "sender_phone", "max_emails_per_day",
        "auto_backup",
    ]
    result = {}
    for k in keys:
        val = get_setting(k)
        # App-Passwort niemals vollständig zurückgeben
        if k == "gmail_app_password" and val:
            result[k] = "••••••••••••••••" if len(val) > 4 else ""
        else:
            result[k] = val or ""
    return jsonify(result)


@app.route("/api/settings/save", methods=["POST"])
@login_required
def api_save_settings():
    data = request.json or {}
    allowed = [
        "gmail_address", "gmail_app_password", "calendly_link",
        "sender_name", "sender_phone", "max_emails_per_day", "auto_backup",
    ]
    for key in allowed:
        if key in data and data[key] and data[key] != "••••••••••••••••":
            set_setting(key, str(data[key]))
    return jsonify({"ok": True, "message": "✅ Einstellungen gespeichert."})


@app.route("/api/settings/test-smtp", methods=["POST"])
@login_required
def api_test_smtp():
    from mailer import test_connection
    return jsonify(test_connection())


@app.route("/api/settings/test-email", methods=["POST"])
@login_required
def api_test_email():
    from mailer import send_test_email
    return jsonify(send_test_email())


@app.route("/api/config/niches")
@login_required
def api_config_niches():
    return jsonify(DEFAULT_NICHES)


@app.route("/api/config/cities")
@login_required
def api_config_cities():
    return jsonify(DEFAULT_CITIES)


# ──────────────────────────────────────
# BACKUP
# ──────────────────────────────────────

@app.route("/api/backup/create", methods=["POST"])
@login_required
def api_backup_create():
    from backup import create_backup
    return jsonify(create_backup())


@app.route("/api/backup/list")
@login_required
def api_backup_list():
    from backup import get_all_backups
    return jsonify(get_all_backups())


@app.route("/api/backup/download/<filename>")
@login_required
def api_backup_download(filename):
    from config import BACKUP_DIR
    path = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(path):
        return jsonify({"error": "Nicht gefunden"}), 404
    return send_file(path, as_attachment=True,
                     download_name=filename, mimetype="application/zip")


# ──────────────────────────────────────
# START
# ──────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print("=" * 55)
    print("  MR Digital – Akquise Automatisierung v2")
    print(f"  http://localhost:{port}")
    print("=" * 55)
    app.run(host="0.0.0.0", debug=False, port=port, threaded=True, use_reloader=False)
