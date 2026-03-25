// Bankenspiegel Dashboard – kompaktes, professionelles Layout
let umsatzChart = null;

/** Prüft Response: bei HTML (z. B. Login-Seite) keine JSON-Parse-Fehler, klare Meldung. */
async function parseJsonResponse(response) {
    const contentType = (response.headers.get('Content-Type') || '').toLowerCase();
    const text = await response.text();
    if (contentType.indexOf('application/json') !== -1) {
        try {
            return JSON.parse(text);
        } catch (e) {
            throw new Error('Antwort ist kein gültiges JSON.');
        }
    }
    if (text && (text.trim().toLowerCase().indexOf('<!doctype') !== -1 || text.trim().indexOf('<!DOCTYPE') !== -1)) {
        if (response.status === 401 || response.status === 403) {
            throw new Error('Bitte erneut anmelden. (Session abgelaufen?)');
        }
        throw new Error('Server hat eine HTML-Seite zurückgegeben statt Daten. Bitte erneut anmelden oder Seite neu laden.');
    }
    throw new Error('Server antwortet nicht mit Daten (Status ' + response.status + ').');
}

function formatBetrag(betrag) {
    if (betrag === null || betrag === undefined) return '0,00 €';
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(betrag);
}

function formatZahl(zahl) {
    if (zahl === null || zahl === undefined) return '0';
    return new Intl.NumberFormat('de-DE').format(zahl);
}

function formatDatum(datum) {
    if (!datum) return '-';
    return new Date(datum).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function hideLoader() {
    const bar = document.getElementById('dashboardLoaderBar');
    if (bar) bar.style.display = 'none';
}

async function loadDashboard() {
    try {
        const response = await fetch('/api/bankenspiegel/dashboard');
        const data = await parseJsonResponse(response);
        if (!response.ok) throw new Error(data.error || data.message || 'API Fehler');
        const d = data.dashboard || data;
        updateKPIs(d);
        updateChart(d);
        updateTopKategorien(d.top_kategorien || []);
        loadLetzteTransaktionen();
        hideLoader();
    } catch (e) {
        console.error('Dashboard:', e);
        hideLoader();
        var msg = (e && e.message) ? e.message : String(e);
        var isAuth = msg.indexOf('anmelden') !== -1 || msg.indexOf('Session') !== -1;
        document.querySelectorAll('.kpi-value').forEach(function(el) { el.textContent = '—'; el.className = 'kpi-value text-muted'; });
        ['einnahmen30Tage', 'ausgaben30Tage', 'saldo30Tage', 'interneTransfersAnzahl', 'interneTransfersVolumen'].forEach(function(id) {
            var el = document.getElementById(id);
            if (el) el.textContent = '—';
        });
        var wrap = document.getElementById('topKategorien');
        if (wrap) wrap.innerHTML = isAuth
            ? '<span class="text-warning">Bitte Seite neu laden oder erneut anmelden.</span>'
            : '<span class="text-muted">Daten nicht geladen.</span>';
        var tbody = document.querySelector('#letzteTransaktionen tbody');
        if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="text-center py-3 small text-muted">—</td></tr>';
    }
}

function updateKPIs(data) {
    const saldo = data.gesamtsaldo ?? 0;
    const saldoEl = document.getElementById('gesamtsaldo');
    saldoEl.textContent = formatBetrag(saldo);
    saldoEl.className = 'kpi-value ' + (saldo >= 0 ? 'text-success' : 'text-danger');

    document.getElementById('anzahlBanken').textContent = formatZahl(data.anzahl_banken ?? 0);
    const aktiv = data.anzahl_konten ?? 0;
    const gesamt = data.anzahl_konten_gesamt ?? aktiv;
    const aktivEl = document.getElementById('anzahlKontenAktiv');
    const gesamtEl = document.getElementById('anzahlKontenGesamt');
    if (aktivEl) aktivEl.textContent = formatZahl(aktiv);
    if (gesamtEl) gesamtEl.textContent = formatZahl(gesamt);

    const l30 = data.letzte_30_tage || {};
    document.getElementById('anzahlTransaktionen').textContent = formatZahl(l30.anzahl_transaktionen ?? 0);

    document.getElementById('einnahmen30Tage').textContent = formatBetrag(l30.einnahmen ?? 0);
    document.getElementById('ausgaben30Tage').textContent = formatBetrag(Math.abs(l30.ausgaben ?? 0));
    const saldo30 = l30.saldo ?? 0;
    const saldo30El = document.getElementById('saldo30Tage');
    saldo30El.textContent = formatBetrag(saldo30);
    saldo30El.className = (saldo30 >= 0 ? 'text-success' : 'text-danger') + ' fw-semibold';

    const it = data.interne_transfers_30_tage || {};
    document.getElementById('interneTransfersAnzahl').textContent = formatZahl(it.anzahl_transaktionen ?? 0);
    document.getElementById('interneTransfersVolumen').textContent = formatBetrag(it.volumen ?? 0);
}

function updateChart(data) {
    const l30 = data.letzte_30_tage || {};
    const einnahmen = Math.abs(l30.einnahmen ?? 0);
    const ausgaben = Math.abs(l30.ausgaben ?? 0);
    const ctx = document.getElementById('umsatzChart');
    if (!ctx) return;
    if (umsatzChart) umsatzChart.destroy();

    umsatzChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Einnahmen', 'Ausgaben'],
            datasets: [{
                label: 'Betrag',
                data: [einnahmen, ausgaben],
                backgroundColor: ['rgba(25, 135, 84, 0.75)', 'rgba(220, 53, 69, 0.75)'],
                borderColor: ['rgba(25, 135, 84, 1)', 'rgba(220, 53, 69, 1)'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            barThickness: 28,
            maxBarThickness: 32,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            return formatBetrag(ctx.parsed.x);
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        maxTicksLimit: 6,
                        callback: function(v) { return formatBetrag(v); }
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { size: 11 } }
                }
            }
        }
    });
}

function updateTopKategorien(topKategorien) {
    const wrap = document.getElementById('topKategorien');
    if (!wrap) return;
    if (!topKategorien || topKategorien.length === 0) {
        wrap.innerHTML = '<span class="text-muted">Keine Kategorien vorhanden. Nutzen Sie „Kategorisieren“.</span>';
        return;
    }
    wrap.innerHTML = topKategorien.map(k => {
        const summe = (k.summe != null) ? formatBetrag(k.summe) : '0 €';
        const name = (k.kategorie || '').trim() || '—';
        const url = '/bankenspiegel/transaktionen?kategorie=' + encodeURIComponent(name);
        var title = '';
        if (name === 'Sonstige Ausgaben') title = ' title="Alle Ausgaben, die keiner anderen Kategorie (z. B. Einkaufsfinanzierung, Personal, Steuern) zugeordnet wurden. Klick zeigt die Liste."';
        return '<div class="d-flex justify-content-between py-1 border-bottom border-light"><span><a href="' + escapeHtml(url) + '" class="text-decoration-none text-dark"' + title + '>' + escapeHtml(name) + '</a>' + (name === 'Sonstige Ausgaben' ? ' <i class="bi bi-info-circle text-muted small" title="Fallback: alle Ausgaben ohne Treffer in den Regeln"></i>' : '') + '</span><span class="text-danger">' + summe + '</span></div>';
    }).join('');
}

function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
}

/** Kurze Meldung anzeigen, verschwindet nach ein paar Sekunden (kein blockierendes Modal). */
function showToast(message, isError) {
    var el = document.getElementById('dashboardToast');
    if (!el) return;
    el.textContent = message;
    el.className = 'bank-dashboard-toast ' + (isError ? 'error' : 'success');
    el.style.display = 'block';
    el.style.opacity = '1';
    clearTimeout(showToast._tid);
    showToast._tid = setTimeout(function() {
        el.style.opacity = '0';
        setTimeout(function() {
            el.textContent = '';
            el.className = 'bank-dashboard-toast';
            el.style.display = '';
        }, 300);
    }, 4000);
}

async function loadLetzteTransaktionen() {
    const tbody = document.querySelector('#letzteTransaktionen tbody');
    try {
        const res = await fetch('/api/bankenspiegel/transaktionen?limit=10&offset=0');
        const data = await parseJsonResponse(res);
        if (!res.ok) throw new Error(data.error || data.message || 'API Fehler');
        const rows = data.transaktionen || [];
        if (rows.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center py-3 small text-muted">Keine Transaktionen</td></tr>';
            return;
        }
        tbody.innerHTML = rows.map(t => {
            const betrag = t.betrag || 0;
            const betragClass = betrag >= 0 ? 'text-success' : 'text-danger';
            const kat = (t.kategorie || '').trim() ? '<span class="badge bg-light text-dark">' + escapeHtml(t.kategorie) + '</span>' : '<span class="text-muted">—</span>';
            return '<tr>' +
                '<td class="small">' + formatDatum(t.buchungsdatum) + '</td>' +
                '<td class="small">' + escapeHtml(t.kontoname || t.bank_name || '-') + '</td>' +
                '<td class="small text-truncate" style="max-width:180px" title="' + escapeHtml(t.verwendungszweck || '') + '">' + escapeHtml((t.verwendungszweck || '-').slice(0, 50)) + (t.verwendungszweck && t.verwendungszweck.length > 50 ? '…' : '') + '</td>' +
                '<td class="small">' + kat + '</td>' +
                '<td class="small text-end ' + betragClass + '">' + formatBetrag(betrag) + '</td>' +
                '</tr>';
        }).join('');
    } catch (e) {
        console.error('Transaktionen:', e);
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-3 small text-danger">Fehler beim Laden</td></tr>';
    }
}

async function runKategorisieren() {
    const btn = document.getElementById('btnKategorisieren');
    if (!btn) return;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Läuft…';
    try {
        var mitKi = !!document.getElementById('kategorisierenMitKi') && document.getElementById('kategorisierenMitKi').checked;
        var sonstigeNeu = !!document.getElementById('kategorisierenSonstigeNeu') && document.getElementById('kategorisierenSonstigeNeu').checked;
        const res = await fetch('/api/bankenspiegel/transaktionen/kategorisieren', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ limit: 500, nur_unkategorisiert: true, mit_ki: mitKi, sonstige_neu_pruefen: sonstigeNeu })
        });
        if (res.status === 404) {
            showToast('Kategorisieren-Endpoint nicht gefunden (404). Portal-Service neustarten.', true);
            return;
        }
        const data = await parseJsonResponse(res);
        if (data.success && data.ergebnis) {
            const r = data.ergebnis;
            const n = r.aktualisiert || 0;
            const ki = r.ki_aktualisiert || 0;
            const sonstigeN = (r.sonstige_neu_pruefen && r.sonstige_neu_pruefen.aktualisiert) ? r.sonstige_neu_pruefen.aktualisiert : 0;
            var msg = n + ' per Regeln';
            if (ki > 0) msg += ', ' + ki + ' per KI (LM Studio)';
            else if (mitKi) msg += '. Keine weiteren unkategorisierten für KI.';
            if (sonstigeN > 0) msg += ' · ' + sonstigeN + ' aus Sonstige neu zugeordnet.';
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-tags me-1"></i>Kategorisieren';
            showToast(msg, false);
            loadDashboard();
        } else {
            showToast('Fehler: ' + (data.error || 'Unbekannt'), true);
        }
    } catch (e) {
        var msg = e && e.message ? e.message : String(e);
        if (msg.indexOf('Bitte erneut anmelden') !== -1 && typeof window !== 'undefined' && window.location) {
            showToast(msg, true);
            window.location.reload();
            return;
        }
        showToast('Fehler: ' + msg, true);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-tags me-1"></i>Kategorisieren';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
    var btn = document.getElementById('btnKategorisieren');
    if (btn) btn.addEventListener('click', runKategorisieren);
    setInterval(loadDashboard, 5 * 60 * 1000);
});
