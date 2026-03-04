/**
 * app.js – MR Digital Akquise v2 Dashboard
 */

// ──────────────────────────────────────
// GLOBALS
// ──────────────────────────────────────
let researchLeads = [];

// ──────────────────────────────────────
// INIT
// ──────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    setInterval(refreshDashboard, 15000);
    refreshDashboard();
    loadCampaign();
    loadNiches();
    loadSettings();
    updateDate();

    // Day toggle buttons
    document.querySelectorAll('.day-btn').forEach(btn => {
        btn.addEventListener('click', () => btn.classList.toggle('active'));
    });
});

function updateDate() {
    const el = document.getElementById('dash-date');
    if (el) {
        const d = new Date();
        el.textContent = d.toLocaleDateString('de-DE', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    }
}

// ──────────────────────────────────────
// TAB NAVIGATION
// ──────────────────────────────────────
function switchTab(name) {
    document.querySelectorAll('.tab-page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById('tab-' + name)?.classList.add('active');
    document.querySelector(`[data-tab="${name}"]`)?.classList.add('active');

    // Lazy-load data per tab
    if (name === 'leads') loadLeads();
    if (name === 'emails') loadEmails();
    if (name === 'backup') loadBackups();
    if (name === 'settings') { loadSettings(); loadBlacklist(); }
}

// ──────────────────────────────────────
// DASHBOARD
// ──────────────────────────────────────
async function refreshDashboard() {
    try {
        const [stats, sched] = await Promise.all([
            fetch('/api/stats').then(r => r.json()),
            fetch('/api/scheduler/status').then(r => r.json()),
        ]);
        renderStats(stats);
        renderSchedulerInfo(sched);
        renderChart(stats.daily || []);
        document.getElementById('badge-leads').textContent = stats.total_leads || 0;
        document.getElementById('badge-emails').textContent = stats.emails_total || 0;
    } catch (e) { console.warn('Dashboard refresh error', e); }
}

function renderStats(s) {
    const campaign = null; // limit displayed separately
    setText('d-emails-today', s.emails_today || 0);
    setText('d-emails-total', s.emails_total || 0);
    setText('d-leads', s.total_leads || 0);
    setText('d-replied', s.replied || 0);
    setText('d-appointments', s.appointments || 0);
    setText('d-errors', s.errors_total || 0);
}

function renderSchedulerInfo(s) {
    const dot = document.getElementById('status-dot');
    const statusEl = document.getElementById('status-text');
    const isRunning = s.running;
    dot?.classList.toggle('active', isRunning);
    if (statusEl) statusEl.textContent = isRunning ? 'Läuft...' : 'Bereit';
    setText('sched-status', isRunning ? '🟢 Läuft' : '⏸ Bereit');
    setText('sched-next', s.next_run || '–');
    setText('sched-last', s.last_run || '–');
    setText('sched-result', s.last_result || '–');

    const stopBtn = document.getElementById('btn-stop');
    const runBtn = document.getElementById('btn-run');
    if (stopBtn) stopBtn.style.display = isRunning ? '' : 'none';
    if (runBtn) runBtn.textContent = isRunning ? '⏳ Läuft...' : '▶ Jetzt senden';
    if (runBtn) runBtn.disabled = isRunning;
}

function renderChart(daily) {
    const wrap = document.getElementById('chart-bars');
    if (!wrap) return;
    const maxVal = Math.max(...daily.map(d => d.count), 1);
    wrap.innerHTML = daily.map(d => {
        const pct = Math.max((d.count / maxVal) * 100, d.count > 0 ? 10 : 3);
        const label = d.date.slice(5); // MM-DD
        return `<div class="chart-bar-wrap">
      <span class="chart-val">${d.count || ''}</span>
      <div class="chart-bar" style="height:${pct}%" title="${d.date}: ${d.count} Emails"></div>
      <span class="chart-label">${label}</span>
    </div>`;
    }).join('');
}

async function runNow() {
    const r = await postJson('/api/scheduler/run', {});
    toast(r.message, r.ok ? 'success' : 'error');
    setTimeout(refreshDashboard, 1000);
}

async function stopScheduler() {
    const r = await postJson('/api/scheduler/stop', {});
    toast(r.message, 'success');
    setTimeout(refreshDashboard, 500);
}

// ──────────────────────────────────────
// KAMPAGNE
// ──────────────────────────────────────
async function loadNiches() {
    const niches = await fetch('/api/config/niches').then(r => r.json()).catch(() => []);
    const sel = document.getElementById('camp-niche');
    if (sel) sel.innerHTML = niches.map(n => `<option value="${n}">${n}</option>`).join('');
}

async function loadCampaign() {
    const c = await fetch('/api/campaign').then(r => r.json()).catch(() => ({}));
    if (!c || !c.niche) return;
    setVal('camp-niche', c.niche);
    setVal('camp-cities', c.cities || '');
    setVal('camp-limit', c.emails_per_day || 30);
    document.getElementById('camp-limit-val').textContent = c.emails_per_day || 30;
    setVal('camp-hour', c.send_hour ?? 9);
    setVal('camp-minute', c.send_minute ?? 0);
    const activeDays = (c.send_days || '0,1,2,3,4').split(',').map(Number);
    document.querySelectorAll('.day-btn').forEach(btn => {
        btn.classList.toggle('active', activeDays.includes(Number(btn.dataset.day)));
    });
}

async function saveCampaign() {
    const activeDays = [...document.querySelectorAll('.day-btn.active')]
        .map(b => b.dataset.day).join(',');
    const body = {
        niche: getVal('camp-niche'),
        cities: getVal('camp-cities'),
        emails_per_day: parseInt(getVal('camp-limit')),
        send_days: activeDays || '0,1,2,3,4',
        send_hour: parseInt(getVal('camp-hour')),
        send_minute: parseInt(getVal('camp-minute')),
    };
    const r = await postJson('/api/campaign/save', body);
    toast(r.message, r.ok ? 'success' : 'error');
    if (r.ok) setTimeout(refreshDashboard, 800);
}

// ──────────────────────────────────────
// RESEARCH
// ──────────────────────────────────────
function startResearch() {
    const query = getVal('res-query').trim();
    const city = getVal('res-city').trim();
    const source = getVal('res-source');
    const maxRes = parseInt(getVal('res-max')) || 8;

    if (!query) { toast('Bitte einen Suchbegriff eingeben.', 'error'); return; }

    researchLeads = [];
    showEl('res-log-card');
    showEl('res-results-card');
    const log = document.getElementById('res-log');
    const tbody = document.getElementById('res-tbody');
    if (log) log.innerHTML = '';
    if (tbody) tbody.innerHTML = '';

    const btn = document.getElementById('btn-research');
    btn.disabled = true;
    btn.textContent = '⏳ Recherche läuft...';

    const url = `/api/research/stream?query=${encodeURIComponent(query)}&city=${encodeURIComponent(city)}&source=${source}&max=${maxRes}`;
    const es = new EventSource(url);

    es.onmessage = (e) => {
        try {
            const data = JSON.parse(e.data);
            if (data.type === 'lead') {
                researchLeads.push(data.lead);
                appendResearchRow(data.lead, researchLeads.length - 1);
                logLine(log, `✅ ${data.lead.name} (${data.lead.city})`, 'success');
            } else if (data.type === 'status') {
                logLine(log, data.message);
            } else if (data.type === 'warning') {
                logLine(log, `⚠️ ${data.message}`, 'warning');
            } else if (data.type === 'complete') {
                logLine(log, data.message, 'success');
                es.close();
                btn.disabled = false;
                btn.textContent = '🔍 Recherche starten';
            }
        } catch (err) { console.warn('SSE parse error', err); }
    };

    es.onerror = () => {
        logLine(log, '❌ Verbindungsfehler', 'error');
        es.close();
        btn.disabled = false;
        btn.textContent = '🔍 Recherche starten';
    };
}

function appendResearchRow(lead, idx) {
    const tbody = document.getElementById('res-tbody');
    if (!tbody) return;
    const tr = document.createElement('tr');
    tr.id = `res-row-${idx}`;
    tr.innerHTML = `
    <td><strong>${esc(lead.name)}</strong></td>
    <td>${esc(lead.category || '')}</td>
    <td>${esc(lead.city || '')}</td>
    <td>${esc(lead.email || '')}</td>
    <td><span class="badge badge-new">${esc(lead.source || '')}</span></td>
    <td>
      <button class="icon-btn" onclick="saveResearchLead(${idx})" title="In Leads übernehmen">➕</button>
    </td>`;
    tbody.appendChild(tr);
}

async function saveResearchLead(idx) {
    const lead = researchLeads[idx];
    if (!lead) return;
    const r = await postJson('/api/research/save', lead);
    const row = document.getElementById(`res-row-${idx}`);
    if (r.ok) {
        toast(`${lead.name} gespeichert.`, 'success');
        if (row) row.classList.add('saved');
    } else {
        toast(r.message, 'error');
    }
}

async function saveAllResearchLeads() {
    let saved = 0;
    for (let i = 0; i < researchLeads.length; i++) {
        const r = await postJson('/api/research/save', researchLeads[i]);
        if (r.ok) {
            saved++;
            document.getElementById(`res-row-${i}`)?.classList.add('saved');
        }
    }
    toast(`${saved} von ${researchLeads.length} Leads übernommen.`, 'success');
    await refreshDashboard();
}

// ──────────────────────────────────────
// LEADS
// ──────────────────────────────────────
async function loadLeads() {
    const status = getVal('filter-status');
    const url = '/api/leads' + (status ? `?status=${status}` : '');
    const leads = await fetch(url).then(r => r.json()).catch(() => []);

    const tbody = document.getElementById('leads-tbody');
    if (!tbody) return;
    document.getElementById('leads-count-info').textContent = `${leads.length} Lead(s)`;

    if (!leads.length) {
        tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><div class="empty-state-icon">🏢</div><p>Noch keine Leads vorhanden.<br>Starte ein Research oder füge manuell hinzu.</p></div></td></tr>`;
        return;
    }

    tbody.innerHTML = leads.map(l => `
    <tr>
      <td><strong>${esc(l.name)}</strong></td>
      <td>${esc(l.category || '–')}</td>
      <td>${esc(l.city || '–')}</td>
      <td>${esc(l.email || '–')}</td>
      <td>${statusBadge(l.status)}</td>
      <td style="color:var(--text3);font-size:12px">${esc(l.contacted_at || '–')}</td>
      <td>
        <div class="action-btns">
          <button class="icon-btn" onclick="sendSingleEmail(${l.id})" title="Email senden">📨</button>
          <button class="icon-btn" onclick="previewEmail(${l.id})" title="Email-Vorschau">👁</button>
          <select class="icon-btn" onchange="changeLeadStatus(${l.id}, this.value)" title="Status ändern">
            ${['Neu', 'Kontaktiert', 'Antwort', 'Termin'].map(s =>
        `<option value="${s}" ${l.status === s ? 'selected' : ''}>${s}</option>`).join('')}
          </select>
          <button class="icon-btn" onclick="blacklistLead(${l.id})" title="Blacklist">🚫</button>
          <button class="icon-btn" onclick="deleteLead(${l.id})" title="Löschen">🗑</button>
        </div>
      </td>
    </tr>`).join('');
}

async function sendSingleEmail(leadId) {
    toast('Sende Email...', 'success');
    const r = await postJson(`/api/emails/send/${leadId}`, {});
    toast(r.message, r.ok ? 'success' : 'error');
    if (r.ok) await loadLeads();
}

async function previewEmail(leadId) {
    const r = await fetch(`/api/emails/preview/${leadId}`).then(x => x.json());
    if (!r.ok) { toast(r.message, 'error'); return; }
    const email = r.email;
    const body = document.getElementById('email-modal-body');
    if (body) {
        body.innerHTML = `
      <div class="email-preview-header">
        <div><span>An:</span> <strong>${esc(email.to_name)} &lt;${esc(email.to_addr)}&gt;</strong></div>
        <div><span>Betreff:</span> <strong>${esc(email.subject)}</strong></div>
        <div><span>Status:</span> <span style="color:var(--yellow)">Vorschau</span></div>
      </div>
      <div class="email-preview-body">${email.body_html}</div>`;
    }
    showModal('email-modal');
}

async function changeLeadStatus(leadId, status) {
    await postJson(`/api/leads/${leadId}/status`, { status });
    loadLeads();
}

async function blacklistLead(leadId) {
    if (!confirm('Lead zur Blacklist hinzufügen?')) return;
    await postJson(`/api/leads/${leadId}/blacklist`, {});
    toast('Zur Blacklist hinzugefügt.', 'success');
    loadLeads();
}

async function deleteLead(leadId) {
    if (!confirm('Lead löschen?')) return;
    await postJson(`/api/leads/${leadId}/delete`, {});
    toast('Lead gelöscht.', 'success');
    loadLeads();
}

function exportLeads() { window.location = '/api/leads/export'; }

function openAddLeadModal() {
    ['new-lead-name', 'new-lead-email', 'new-lead-cat', 'new-lead-city', 'new-lead-phone', 'new-lead-website']
        .forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
    showModal('add-lead-modal');
}

async function submitNewLead() {
    const lead = {
        name: getVal('new-lead-name'),
        email: getVal('new-lead-email'),
        category: getVal('new-lead-cat'),
        city: getVal('new-lead-city'),
        phone: getVal('new-lead-phone'),
        website: getVal('new-lead-website'),
    };
    if (!lead.name || !lead.email) { toast('Name und Email pflicht.', 'error'); return; }
    const r = await postJson('/api/leads/add', lead);
    toast(r.message, r.ok ? 'success' : 'error');
    if (r.ok) { closeModal('add-lead-modal'); loadLeads(); refreshDashboard(); }
}

// ──────────────────────────────────────
// EMAILS
// ──────────────────────────────────────
async function loadEmails() {
    const emails = await fetch('/api/emails?limit=200').then(r => r.json()).catch(() => []);
    const tbody = document.getElementById('emails-tbody');
    if (!tbody) return;

    if (!emails.length) {
        tbody.innerHTML = `<tr><td colspan="5"><div class="empty-state"><div class="empty-state-icon">📭</div><p>Noch keine Emails versendet.</p></div></td></tr>`;
        return;
    }

    tbody.innerHTML = emails.map(e => `
    <tr>
      <td>${esc(e.to_name || '')} <span style="color:var(--text3);font-size:12px">&lt;${esc(e.to_addr || '')}&gt;</span></td>
      <td>${esc(e.subject || '').slice(0, 55)}</td>
      <td><span class="badge ${e.status === 'Gesendet' ? 'badge-ok' : 'badge-err'}">${esc(e.status)}</span></td>
      <td style="color:var(--text3);font-size:12px">${esc(e.sent_at || '')}</td>
      <td>
        <button class="icon-btn" onclick="showEmailBody(${JSON.stringify(e.body || '').replace(/'/g, "&#39;")}, ${JSON.stringify(e.subject || '')})" title="Vorschau">👁</button>
      </td>
    </tr>`).join('');
}

function showEmailBody(html, subject) {
    const body = document.getElementById('email-modal-body');
    if (body) body.innerHTML = `
    <div class="email-preview-header">
      <div><span>Betreff:</span> <strong>${esc(subject)}</strong></div>
    </div>
    <div class="email-preview-body">${html}</div>`;
    showModal('email-modal');
}

// ──────────────────────────────────────
// SETTINGS
// ──────────────────────────────────────
async function loadSettings() {
    const s = await fetch('/api/settings').then(r => r.json()).catch(() => ({}));
    setVal('set-gmail', s.gmail_address || '');
    setVal('set-pw', s.gmail_app_password || '');
    setVal('set-name', s.sender_name || '');
    setVal('set-phone', s.sender_phone || '');
    setVal('set-calendly', s.calendly_link || '');
    setVal('set-limit', s.max_emails_per_day || '30');
    setVal('set-subject', s.email_subject || '');
    setVal('set-tmpl-html', s.email_template_html || '');
    setVal('set-tmpl-text', s.email_template_text || '');
    const cb = document.getElementById('set-backup');
    if (cb) cb.checked = (s.auto_backup !== 'false');
}

async function saveSettings() {
    const data = {
        gmail_address: getVal('set-gmail'),
        gmail_app_password: getVal('set-pw'),
        sender_name: getVal('set-name'),
        sender_phone: getVal('set-phone'),
        calendly_link: getVal('set-calendly'),
        max_emails_per_day: getVal('set-limit'),
        auto_backup: document.getElementById('set-backup')?.checked ? 'true' : 'false',
        email_subject: getVal('set-subject'),
        email_template_html: getVal('set-tmpl-html'),
        email_template_text: getVal('set-tmpl-text'),
    };
    const r = await postJson('/api/settings/save', data);
    toast(r.message, r.ok ? 'success' : 'error');
}

async function testSmtp() {
    toast('Teste Verbindung...', 'success');
    const r = await postJson('/api/settings/test-smtp', {});
    toast(r.message, r.ok ? 'success' : 'error');
}

async function sendTestEmail() {
    toast('Sende Test-Email...', 'success');
    const r = await postJson('/api/settings/test-email', {});
    toast(r.message, r.ok ? 'success' : 'error');
}

// ──────────────────────────────────────
// BLACKLIST
// ──────────────────────────────────────
async function loadBlacklist() {
    const list = await fetch('/api/blacklist').then(r => r.json()).catch(() => []);
    const tbody = document.getElementById('blacklist-tbody');
    if (!tbody) return;

    if (!list.length) {
        tbody.innerHTML = `<tr><td colspan="4" style="color:var(--text3);padding:20px;text-align:center">Keine Einträge</td></tr>`;
        return;
    }

    tbody.innerHTML = list.map(b => `
    <tr>
      <td>${esc(b.email)}</td>
      <td>${esc(b.company || '–')}</td>
      <td>${esc(b.reason || '–')}</td>
      <td style="color:var(--text3);font-size:12px">${esc(b.added_at || '')}</td>
    </tr>`).join('');
}

function openBlacklistAddModal() {
    setVal('bl-email', ''); setVal('bl-company', ''); setVal('bl-reason', 'Abgemeldet');
    showModal('bl-add-modal');
}

async function submitBlacklist() {
    const r = await postJson('/api/blacklist/add', {
        email: getVal('bl-email'),
        company: getVal('bl-company'),
        reason: getVal('bl-reason'),
    });
    toast(r.message, r.ok ? 'success' : 'error');
    if (r.ok) { closeModal('bl-add-modal'); loadBlacklist(); }
}

// ──────────────────────────────────────
// BACKUP
// ──────────────────────────────────────
async function loadBackups() {
    const list = await fetch('/api/backup/list').then(r => r.json()).catch(() => []);
    const tbody = document.getElementById('backup-tbody');
    if (!tbody) return;

    if (!list.length) {
        tbody.innerHTML = `<tr><td colspan="4" style="color:var(--text3);padding:20px;text-align:center">Noch keine Backups erstellt.</td></tr>`;
        return;
    }

    tbody.innerHTML = list.map(b => `
    <tr>
      <td style="font-family:monospace;font-size:12px">${esc(b.filename)}</td>
      <td>${Math.round((b.size_bytes || 0) / 1024)} KB</td>
      <td style="color:var(--text3);font-size:12px">${esc(b.created_at || '')}</td>
      <td>
        <a class="btn btn-sm btn-ghost" href="/api/backup/download/${encodeURIComponent(b.filename)}">⬇ Download</a>
      </td>
    </tr>`).join('');
}

async function createBackup() {
    toast('Erstelle Backup...', 'success');
    const r = await postJson('/api/backup/create', {});
    if (r.ok) {
        toast(`✅ Backup erstellt (${r.size_kb} KB)`, 'success');
        loadBackups();
    } else {
        toast(r.message || 'Backup fehlgeschlagen', 'error');
    }
}

// ──────────────────────────────────────
// HELPERS
// ──────────────────────────────────────
function showModal(id) {
    const el = document.getElementById(id);
    if (el) { el.style.display = 'flex'; document.body.style.overflow = 'hidden'; }
}
function closeModal(id) {
    const el = document.getElementById(id);
    if (el) { el.style.display = 'none'; document.body.style.overflow = ''; }
}
function showEl(id) { const el = document.getElementById(id); if (el) el.style.display = ''; }

function toast(msg, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.innerHTML = `<span>${msg}</span>`;
    container.appendChild(t);
    setTimeout(() => t.remove(), 4000);
}

function logLine(el, msg, cls = '') {
    if (!el) return;
    const line = document.createElement('div');
    line.className = 'log-line' + (cls ? ' ' + cls : '');
    const ts = new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    line.textContent = `[${ts}] ${msg}`;
    el.appendChild(line);
    el.scrollTop = el.scrollHeight;
}

function statusBadge(status) {
    const map = {
        'Neu': 'badge-new',
        'Kontaktiert': 'badge-contact',
        'Antwort': 'badge-reply',
        'Termin': 'badge-appt',
        'Blacklist': 'badge-black',
    };
    return `<span class="badge ${map[status] || 'badge-new'}">${esc(status || 'Neu')}</span>`;
}

function esc(s) {
    return String(s || '')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function getVal(id) { return document.getElementById(id)?.value || ''; }
function setVal(id, v) { const el = document.getElementById(id); if (el) el.value = v || ''; }
function setText(id, v) { const el = document.getElementById(id); if (el) el.textContent = v; }

async function postJson(url, data) {
    try {
        const r = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        return r.json();
    } catch (e) {
        return { ok: false, message: String(e) };
    }
}
