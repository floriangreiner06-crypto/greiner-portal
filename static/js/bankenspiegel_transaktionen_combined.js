// Bankenspiegel Transaktionen – kombinierte Seite: Übersicht | Kategorisieren
// Modus aus URL: ?mode=kategorisierung → Kategorisieren-Tab

// --- Übersicht (Transaktionen) ---
let alleTransaktionen = [];
let alleKonten = [];
let currentPage = 1;
let itemsPerPage = 50;
let filteredTransaktionen = [];

// --- Kategorisieren ---
let kategorienListe = [];
let unterkategorienByKat = {};
let currentLimit = 100;
let currentOffset = 0;
let currentTotal = 0;
let kategorisierungInitialized = false;
const SESSION_FILTER_KEY = 'bankenspiegel_kategorisierung_filter';

// --- Modus (Tab) ---
function getModeFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('mode') === 'kategorisierung' ? 'kategorisierung' : 'uebersicht';
}

function setModeInUrl(mode) {
    const url = new URL(window.location.href);
    if (mode === 'kategorisierung') {
        url.searchParams.set('mode', 'kategorisierung');
    } else {
        url.searchParams.delete('mode');
    }
    window.history.replaceState({}, '', url.toString());
}

function getActiveTabPanel() {
    const active = document.querySelector('#transaktionenTabContent .tab-pane.active');
    if (!active) return null;
    return active.id === 'panel-kategorisierung' ? 'kategorisierung' : 'uebersicht';
}

// --- Gemeinsame Hilfsfunktionen ---
function formatBetrag(betrag) {
    if (betrag === null || betrag === undefined) return '0,00 €';
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(betrag);
}

function formatZahl(zahl) {
    if (zahl === null || zahl === undefined) return '0';
    return new Intl.NumberFormat('de-DE').format(zahl);
}

function formatDatum(datum) {
    if (!datum) return '–';
    const d = new Date(datum);
    return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function escapeHtml(s) {
    if (s == null) return '';
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
}

function showToast(message, isError) {
    const toastEl = document.getElementById('toastMessage');
    const body = document.getElementById('toastBody');
    if (!toastEl || !body) return;
    toastEl.classList.remove('text-bg-success', 'text-bg-danger');
    toastEl.classList.add(isError ? 'text-bg-danger' : 'text-bg-success');
    body.textContent = message;
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

// ========== ÜBERSICHT ==========
async function loadKontenFilter() {
    try {
        const response = await fetch('/api/bankenspiegel/konten');
        if (!response.ok) throw new Error('API Fehler');
        const data = await response.json();
        alleKonten = data.konten || [];
        const kontoFilter = document.getElementById('kontoFilter');
        if (!kontoFilter) return;
        // Nur echte Konten (id > 0), keine EKF-Aggregate – API liefert id, nicht konto_id
        kontoFilter.innerHTML = '<option value="">Alle Konten</option>' +
            alleKonten
                .filter(k => k.aktiv && !k.ekf && (k.id == null || k.id > 0))
                .map(k => `<option value="${k.id}">${k.bank_name || ''} - ${k.kontoname || k.iban || ''}</option>`)
                .join('');
    } catch (e) {
        console.error('Konten laden:', e);
    }
}

function setDefaultDates() {
    const heute = new Date();
    heute.setHours(0, 0, 0, 0);
    const von = document.getElementById('vonDatum');
    const bis = document.getElementById('bisDatum');
    if (bis) bis.valueAsDate = heute;
    if (von) von.valueAsDate = heute;
}

function fillKategorieFilter() {
    const kat = {};
    alleTransaktionen.forEach(t => {
        const k = (t.kategorie || '').trim();
        if (k) kat[k] = true;
    });
    const sel = document.getElementById('kategorieFilter');
    if (!sel) return;
    const opts = Object.keys(kat).sort();
    sel.innerHTML = '<option value="">Alle Kategorien</option>' + opts.map(o => '<option value="' + escapeHtml(o) + '">' + escapeHtml(o) + '</option>').join('');
}

function checkUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    const kontoId = urlParams.get('konto_id');
    const kategorie = urlParams.get('kategorie');
    const kontoFilter = document.getElementById('kontoFilter');
    const kategorieFilter = document.getElementById('kategorieFilter');
    if (kontoId && kontoFilter) kontoFilter.value = kontoId;
    if (kategorie && kategorieFilter) kategorieFilter.value = kategorie;
}

let ekfInstitut = null; // Bei EKF-Ansicht: Stellantis | Hyundai Finance | Santander

async function loadTransaktionenUebersicht() {
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const ekfFromUrl = urlParams.get('ekf_institut');
        const kontoIdFromUrl = urlParams.get('konto_id');

        if (ekfFromUrl && ['Stellantis', 'Hyundai Finance', 'Santander'].includes(ekfFromUrl)) {
            ekfInstitut = ekfFromUrl;
            const response = await fetch('/api/bankenspiegel/ekf-bewegungen?institut=' + encodeURIComponent(ekfInstitut));
            if (!response.ok) throw new Error('EKF-Bewegungen konnten nicht geladen werden.');
            const data = await response.json();
            alleTransaktionen = data.transaktionen || [];
            showEKFHinweisBanner(data.hinweis || 'Stand aus CSV-Import – keine Kontoauszüge.', ekfInstitut);
            document.getElementById('kontoFilter')?.closest('.col-md-3')?.classList?.add('d-none');
        } else {
            ekfInstitut = null;
            hideEKFHinweisBanner();
            let apiUrl = '/api/bankenspiegel/transaktionen?limit=10000&offset=0';
            if (kontoIdFromUrl) apiUrl += '&konto_id=' + encodeURIComponent(kontoIdFromUrl);
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('API Fehler');
            const data = await response.json();
            alleTransaktionen = data.transaktionen || [];
            await loadKontenFilter();
        }
        fillKategorieFilter();
        setDefaultDates();
        checkUrlParams();
        applyFilters();
    } catch (error) {
        console.error('Fehler beim Laden der Transaktionen:', error);
        alert('Fehler: Transaktionen konnten nicht geladen werden.');
    }
}

function showEKFHinweisBanner(hinweis, institut) {
    let banner = document.getElementById('ekfHinweisBanner');
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'ekfHinweisBanner';
        banner.className = 'alert alert-info d-flex align-items-center mb-3';
        const panel = document.getElementById('panel-uebersicht');
        if (panel && panel.firstChild) panel.insertBefore(banner, panel.firstChild);
        else panel?.appendChild(banner);
    }
    banner.innerHTML = '<i class="bi bi-info-circle me-2"></i><span><strong>EKF ' + escapeHtml(institut) + ':</strong> ' + escapeHtml(hinweis) + '</span>';
    banner.classList.remove('d-none');
}

function hideEKFHinweisBanner() {
    const banner = document.getElementById('ekfHinweisBanner');
    if (banner) banner.classList.add('d-none');
    document.getElementById('kontoFilter')?.closest('.col-md-3')?.classList?.remove('d-none');
}

function applyFilters() {
    const vonDatum = document.getElementById('vonDatum').value;
    const bisDatum = document.getElementById('bisDatum').value;
    const kontoId = document.getElementById('kontoFilter').value;
    const typ = document.getElementById('typFilter').value;
    const kategorieEl = document.getElementById('kategorieFilter');
    const kategorie = kategorieEl ? kategorieEl.value : '';
    const searchTerm = (document.getElementById('searchTransaktionen') || {}).value.toLowerCase();

    filteredTransaktionen = alleTransaktionen.filter(t => {
        if (vonDatum && t.buchungsdatum < vonDatum) return false;
        if (bisDatum && t.buchungsdatum > bisDatum) return false;
        if (kontoId && t.konto_id !== parseInt(kontoId, 10)) return false;
        if (typ === 'einnahmen' && t.betrag < 0) return false;
        if (typ === 'ausgaben' && t.betrag >= 0) return false;
        if (kategorie && (t.kategorie || '').trim() !== kategorie) return false;
        if (searchTerm && !(t.verwendungszweck || '').toLowerCase().includes(searchTerm)) return false;
        return true;
    });

    updateStatistik();
    currentPage = 1;
    updateTransaktionenTable();
    updatePagination();
}

function updateStatistik() {
    const einnahmen = filteredTransaktionen.filter(t => t.betrag >= 0).reduce((sum, t) => sum + t.betrag, 0);
    const ausgaben = filteredTransaktionen.filter(t => t.betrag < 0).reduce((sum, t) => sum + Math.abs(t.betrag), 0);
    const saldo = einnahmen - ausgaben;
    const eEl = document.getElementById('einnahmenGefiltert');
    const aEl = document.getElementById('ausgabenGefiltert');
    const sEl = document.getElementById('saldoGefiltert');
    const nEl = document.getElementById('anzahlGefiltert');
    if (eEl) eEl.innerHTML = formatBetrag(einnahmen);
    if (aEl) aEl.innerHTML = formatBetrag(ausgaben);
    if (sEl) {
        sEl.innerHTML = formatBetrag(saldo);
        sEl.className = saldo >= 0 ? 'mb-0 text-success' : 'mb-0 text-danger';
    }
    if (nEl) nEl.innerHTML = formatZahl(filteredTransaktionen.length);
}

function updateTransaktionenTable() {
    const tbody = document.querySelector('#transaktionenTable tbody');
    if (!tbody) return;
    if (filteredTransaktionen.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center py-5 text-muted"><i class="bi bi-inbox me-2"></i>Keine Transaktionen gefunden</td></tr>';
        const info = document.getElementById('transaktionenInfo');
        if (info) info.textContent = 'Keine Transaktionen gefunden';
        return;
    }
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageTransaktionen = filteredTransaktionen.slice(startIndex, endIndex);
    tbody.innerHTML = pageTransaktionen.map(t => {
        const betrag = t.betrag || 0;
        const betragClass = betrag >= 0 ? 'text-success' : 'text-danger';
        const icon = betrag >= 0 ? '↑' : '↓';
        const konto = alleKonten.find(k => k.id === t.konto_id);
        const kontoInfo = konto ? `${konto.bank_name || ''}<br><small class="text-muted">${konto.kontoname || konto.iban}</small>` : '-';
        return '<tr><td class="text-muted small">' + formatDatum(t.buchungsdatum) + '</td><td class="small">' + kontoInfo + '</td><td><div style="max-width:500px;overflow:hidden;text-overflow:ellipsis;">' + escapeHtml(t.verwendungszweck || '-') + '</div></td><td class="text-end ' + betragClass + ' fw-bold">' + icon + ' ' + formatBetrag(Math.abs(betrag)) + '</td></tr>';
    }).join('');
    const von = startIndex + 1;
    const bis = Math.min(endIndex, filteredTransaktionen.length);
    const info = document.getElementById('transaktionenInfo');
    if (info) info.textContent = formatZahl(von) + '-' + formatZahl(bis) + ' von ' + formatZahl(filteredTransaktionen.length) + ' Transaktionen';
}

function updatePagination() {
    const totalPages = Math.ceil(filteredTransaktionen.length / itemsPerPage);
    const pagination = document.getElementById('pagination');
    if (!pagination) return;
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    if (endPage - startPage < 4) startPage = Math.max(1, endPage - 4);
    let html = '<li class="page-item ' + (currentPage === 1 ? 'disabled' : '') + '"><a class="page-link" href="#" onclick="changePage(' + (currentPage - 1) + '); return false;"><i class="bi bi-chevron-left"></i></a></li>';
    for (let i = startPage; i <= endPage; i++) {
        html += '<li class="page-item ' + (i === currentPage ? 'active' : '') + '"><a class="page-link" href="#" onclick="changePage(' + i + '); return false;">' + i + '</a></li>';
    }
    html += '<li class="page-item ' + (currentPage === totalPages ? 'disabled' : '') + '"><a class="page-link" href="#" onclick="changePage(' + (currentPage + 1) + '); return false;"><i class="bi bi-chevron-right"></i></a></li>';
    pagination.innerHTML = html;
}

function changePage(page) {
    const totalPages = Math.ceil(filteredTransaktionen.length / itemsPerPage);
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    updateTransaktionenTable();
    updatePagination();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ========== KATEGORISIERUNG ==========
function getVormonatVonBis() {
    const now = new Date();
    const vor = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const bis = new Date(now.getFullYear(), now.getMonth(), 0);
    return { von: vor.toISOString().slice(0, 10), bis: bis.toISOString().slice(0, 10) };
}

function loadFilterFromSession() {
    try {
        const raw = sessionStorage.getItem(SESSION_FILTER_KEY);
        if (!raw) return false;
        const o = JSON.parse(raw);
        const von = document.getElementById('filterVon');
        const bis = document.getElementById('filterBis');
        const nurUnk = document.getElementById('nurUnkategorisiert');
        const nurTrain = document.getElementById('nurTrainierte');
        const kat = document.getElementById('filterKategorie');
        const suche = document.getElementById('filterSuche');
        if (von && o.von) von.value = o.von;
        if (bis && o.bis) bis.value = o.bis;
        if (nurUnk && typeof o.nur_unkategorisiert === 'boolean') nurUnk.checked = o.nur_unkategorisiert;
        if (nurTrain && typeof o.nur_trainierte === 'boolean') nurTrain.checked = o.nur_trainierte;
        if (kat && o.kategorie !== undefined) kat.value = o.kategorie || '';
        if (suche && o.suche !== undefined) suche.value = o.suche || '';
        return true;
    } catch (e) {
        return false;
    }
}

function saveFilterToSession() {
    const von = document.getElementById('filterVon');
    const bis = document.getElementById('filterBis');
    const nurUnk = document.getElementById('nurUnkategorisiert');
    const nurTrain = document.getElementById('nurTrainierte');
    const kat = document.getElementById('filterKategorie');
    const suche = document.getElementById('filterSuche');
    const o = {
        von: von && von.value ? von.value : '',
        bis: bis && bis.value ? bis.value : '',
        nur_unkategorisiert: nurUnk ? nurUnk.checked : false,
        nur_trainierte: nurTrain ? nurTrain.checked : false,
        kategorie: kat ? (kat.value || '') : '',
        suche: suche ? (suche.value || '') : ''
    };
    try {
        sessionStorage.setItem(SESSION_FILTER_KEY, JSON.stringify(o));
    } catch (e) {}
}

async function loadKategorien() {
    try {
        const res = await fetch('/api/bankenspiegel/kategorien', { credentials: 'same-origin' });
        const text = await res.text();
        let data;
        try {
            data = JSON.parse(text);
        } catch (e) {
            if (res.status === 401 || res.status === 302) console.warn('Kategorien: Bitte anmelden.');
            return;
        }
        if (!data.success || !data.kategorien) return;
        kategorienListe = data.kategorien;
        unterkategorienByKat = {};
        kategorienListe.forEach(function (item) {
            const k = item.kategorie || '';
            if (!unterkategorienByKat[k]) unterkategorienByKat[k] = [];
            const u = item.unterkategorie == null ? '' : item.unterkategorie;
            if (unterkategorienByKat[k].indexOf(u) === -1) unterkategorienByKat[k].push(u);
        });
        const filterSelect = document.getElementById('filterKategorie');
        if (filterSelect) {
            const seen = {};
            filterSelect.innerHTML = '<option value="">Alle</option>';
            kategorienListe.forEach(function (item) {
                const k = item.kategorie;
                if (k && !seen[k]) { seen[k] = true; filterSelect.appendChild(new Option(k, k)); }
            });
        }
    } catch (e) {
        console.error('Kategorien laden:', e);
    }
}

function bauKategorieDropdown(transId, selectedKat, selectedUnter) {
    const kat = selectedKat || '';
    const uniqueKat = [];
    const seen = {};
    kategorienListe.forEach(function (item) {
        const k = item.kategorie || '';
        if (k && !seen[k]) { seen[k] = true; uniqueKat.push(k); }
    });
    let html = '<select class="form-select form-select-sm kategorie-select" data-trans-id="' + transId + '">';
    html += '<option value="">—</option>';
    uniqueKat.forEach(function (k) {
        html += '<option value="' + escapeHtml(k) + '"' + (k === kat ? ' selected' : '') + '>' + escapeHtml(k) + '</option>';
    });
    html += '</select>';
    return html;
}

function bauUnterkategorieDropdown(transId, kategorie, selectedUnter) {
    const unter = (selectedUnter == null || selectedUnter === '') ? '' : String(selectedUnter).trim();
    const options = unterkategorienByKat[kategorie] || [];
    const hasUnter = options.some(function (u) { return (u == null ? '' : u) === unter; });
    let html = '<select class="form-select form-select-sm unterkategorie-select" data-trans-id="' + transId + '">';
    html += '<option value="">—</option>';
    options.forEach(function (u) {
        const val = (u == null || u === '') ? '' : u;
        const label = val === '' ? '—' : val;
        html += '<option value="' + escapeHtml(val) + '"' + (val === unter ? ' selected' : '') + '>' + escapeHtml(label) + '</option>';
    });
    if (unter && !hasUnter) {
        html += '<option value="' + escapeHtml(unter) + '" selected>' + escapeHtml(unter) + '</option>';
    }
    html += '</select>';
    return html;
}

function textZeile(t) {
    const v = (t.verwendungszweck || '').trim();
    const b = (t.buchungstext || '').trim();
    const g = (t.gegenkonto_name || '').trim();
    const parts = [v, b, g].filter(Boolean);
    return parts.length ? parts.join(' · ') : '—';
}

async function loadTransaktionenKat() {
    const nurUnk = document.getElementById('nurUnkategorisiert');
    const filterKat = document.getElementById('filterKategorie');
    const von = document.getElementById('filterVon');
    const bis = document.getElementById('filterBis');
    const suche = document.getElementById('filterSuche');
    const nurTrain = document.getElementById('nurTrainierte');
    const params = new URLSearchParams({
        nur_unkategorisiert: (nurUnk && nurUnk.checked) ? 'true' : 'false',
        nur_kategorisiert: (nurTrain && nurTrain.checked) ? 'true' : 'false',
        limit: currentLimit,
        offset: currentOffset
    });
    if (filterKat && filterKat.value) params.set('kategorie', filterKat.value);
    if (von && von.value) params.set('von', von.value);
    if (bis && bis.value) params.set('bis', bis.value);
    if (suche && suche.value) params.set('suche', suche.value);
    params.set('_', String(Date.now()));

    const tbody = document.getElementById('kategorisierungBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4"><span class="spinner-border spinner-border-sm me-2"></span>Lade...</td></tr>';

    try {
        const res = await fetch('/api/bankenspiegel/transaktionen/kategorisierung?' + params.toString(), { credentials: 'same-origin' });
        const text = await res.text();
        let data;
        try {
            data = JSON.parse(text);
        } catch (parseErr) {
            const msg = res.status === 401 || res.status === 302 ? 'Bitte erneut anmelden (Session abgelaufen?).' : (res.status === 500 ? 'Serverfehler (500).' : 'Antwort ungültig (Status ' + res.status + ').');
            if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">' + escapeHtml(msg) + '</td></tr>';
            if (!res.ok) console.error('Kategorisierung API:', res.status, text.substring(0, 300));
            return;
        }
        if (!data.success) {
            if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Fehler: ' + escapeHtml(data.error || 'Unbekannt') + '</td></tr>';
            return;
        }
        const rows = data.transaktionen || [];
        currentTotal = Number(data.total) || 0;

        if (rows.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">Keine Transaktionen (Filter anpassen oder Regeln anwenden).</td></tr>';
        } else {
            tbody.innerHTML = rows.map(function (t) {
                const kat = (t.kategorie != null && t.kategorie !== '') ? String(t.kategorie).trim() : '';
                const unter = t.unterkategorie == null ? '' : String(t.unterkategorie);
                const txt = textZeile(t);
                const hatKategorie = kat.length > 0;
                const vomUserGespeichert = !!(t.kategorie_manuell === true);
                const rowClass = vomUserGespeichert ? 'table-success' : '';
                const dataKategorisiert = vomUserGespeichert ? ' data-kategorisiert="true"' : '';
                const kiLernenHtml = hatKategorie
                    ? '<span class="text-info kategorisierung-ki-lernen ms-1" title="Wird als KI-Lernbeispiel genutzt"><i class="bi bi-journal-check me-1"></i>KI-Lernbeispiel</span>'
                    : '';
                return '<tr' + (rowClass ? ' class="' + rowClass + '"' : '') + dataKategorisiert + ' data-trans-id="' + t.id + '" data-datum="' + (t.buchungsdatum || '') + '" data-vw="' + escapeHtml(t.verwendungszweck || '') + '" data-bt="' + escapeHtml(t.buchungstext || '') + '" data-gk="' + escapeHtml(t.gegenkonto_name || '') + '" data-betrag="' + (t.betrag != null ? t.betrag : '') + '">' +
                    '<td>' + formatDatum(t.buchungsdatum) + '</td>' +
                    '<td class="text-end">' + formatBetrag(t.betrag) + '</td>' +
                    '<td class="small text-break kategorisierung-buchungstext" data-full="' + escapeHtml(txt) + '"' + (txt ? ' title="' + escapeHtml(txt.length > 600 ? txt.substring(0, 600) + '…' : txt) + '"' : '') + '>' + escapeHtml(txt || '—') + '</td>' +
                    '<td>' + bauKategorieDropdown(t.id, kat, unter) + '</td>' +
                    '<td>' + bauUnterkategorieDropdown(t.id, kat, unter) + '</td>' +
                    '<td class="aktionen-cell">' +
                    '<button type="button" class="btn btn-sm btn-success me-1 btn-uebernehmen" onclick="speichern(' + t.id + ')" title="Speichern und als KI-Lernbeispiel nutzen">Übernehmen</button>' +
                    '<button type="button" class="btn btn-sm btn-outline-secondary btn-ki me-1" data-trans-id="' + t.id + '" onclick="kiVorschlag(' + t.id + ')" title="KI-Vorschlag anfordern">KI</button>' +
                    '<button type="button" class="btn btn-sm btn-outline-info me-1 btn-beleg-suchen" data-trans-id="' + t.id + '" onclick="belegSuchen(' + t.id + ')" title="Belege zu dieser Buchung in ecoDMS suchen"><i class="bi bi-file-earmark-pdf me-1"></i>Beleg</button>' +
                    '<button type="button" class="btn btn-sm btn-outline-secondary btn-verwerfen" onclick="verwerfenZeile(' + t.id + ')" title="Vorschlag verwerfen (Felder leeren)">Verwerfen</button>' +
                    '<span class="kategorisierung-status ms-2"></span>' +
                    kiLernenHtml +
                    '</td></tr>';
            }).join('');
            document.querySelectorAll('.kategorie-select').forEach(function (sel) {
                sel.addEventListener('change', function () {
                    const transId = parseInt(this.dataset.transId, 10);
                    const row = this.closest('tr');
                    const unterCell = row ? row.querySelector('td:nth-child(5)') : null;
                    if (unterCell) {
                        const neueKat = this.value;
                        const unterSelect = row.querySelector('.unterkategorie-select');
                        var bisherUnter = (row.dataset.kiUnterkategorie !== undefined && row.dataset.kiUnterkategorie !== '') ? row.dataset.kiUnterkategorie : (unterSelect ? unterSelect.value : '');
                        if (row.dataset.kiUnterkategorie !== undefined) delete row.dataset.kiUnterkategorie;
                        unterCell.innerHTML = bauUnterkategorieDropdown(transId, neueKat, bisherUnter);
                    }
                });
            });
        }

        const infoEl = document.getElementById('infoZeile');
        if (infoEl) infoEl.textContent = (currentOffset + 1) + '–' + (currentOffset + rows.length) + ' von ' + currentTotal + ' Transaktionen';
        renderPaginationKat();
    } catch (e) {
        console.error('Transaktionen laden:', e);
        if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Netzwerkfehler beim Laden.</td></tr>';
    }
}

function renderPaginationKat() {
    const ul = document.getElementById('paginationKat');
    if (!ul) return;
    const total = Number(currentTotal) || 0;
    const pages = Math.ceil(total / currentLimit) || 1;
    const page = Math.floor(currentOffset / currentLimit) + 1;
    ul.innerHTML = '';
    if (pages <= 1 || total <= currentLimit) return;
    function add(label, off, disabled) {
        const li = document.createElement('li');
        li.className = 'page-item' + (disabled ? ' disabled' : '');
        const a = document.createElement('a');
        a.className = 'page-link';
        a.href = '#';
        a.textContent = label;
        if (!disabled) a.onclick = function (e) { e.preventDefault(); currentOffset = off; loadTransaktionenKat(); };
        li.appendChild(a);
        ul.appendChild(li);
    }
    add('«', currentOffset - currentLimit, currentOffset <= 0);
    add('Seite ' + page + ' / ' + pages, currentOffset, true);
    add('»', currentOffset + currentLimit, currentOffset + currentLimit >= total);
}

function getRowKategorieUnter(transId) {
    const row = document.querySelector('#kategorisierungBody tr[data-trans-id="' + transId + '"]');
    if (!row) return { kategorie: null, unterkategorie: null };
    const katSel = row.querySelector('.kategorie-select');
    const unterSel = row.querySelector('.unterkategorie-select');
    return {
        kategorie: katSel ? (katSel.value || null) : null,
        unterkategorie: unterSel ? (unterSel.value || null) : null
    };
}

async function speichern(transId) {
    const { kategorie, unterkategorie } = getRowKategorieUnter(transId);
    var kat = (kategorie != null && kategorie !== '') ? String(kategorie).trim() : '';
    var unter = (unterkategorie != null && unterkategorie !== '') ? String(unterkategorie).trim() : '';
    if (!kat) {
        showToast('Bitte zuerst eine Kategorie wählen.', true);
        return;
    }
    try {
        const res = await fetch('/api/bankenspiegel/transaktionen/' + transId + '/kategorie', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ kategorie: kat, unterkategorie: unter }),
            credentials: 'same-origin'
        });
        const data = await res.json();
        if (data.success) {
            showToast('Gespeichert.');
            zeigeGespeichert(transId);
            const nurUnkEl = document.getElementById('nurUnkategorisiert');
            const nurTrainEl = document.getElementById('nurTrainierte');
            if ((nurUnkEl && nurUnkEl.checked) || (nurTrainEl && nurTrainEl.checked)) {
                setTimeout(function () { loadTransaktionenKat(); }, 150);
            }
        } else {
            showToast(data.error || 'Speichern fehlgeschlagen', true);
        }
    } catch (e) {
        showToast('Fehler beim Speichern', true);
    }
}

function zeigeGespeichert(transId) {
    const row = document.querySelector('#kategorisierungBody tr[data-trans-id="' + transId + '"]');
    if (!row) return;
    row.classList.add('table-success');
    row.setAttribute('data-kategorisiert', 'true');
    const status = row.querySelector('.kategorisierung-status');
    if (status) {
        status.innerHTML = '<span class="text-success"><i class="bi bi-check-circle-fill me-1"></i>Gespeichert · wird für KI gelernt</span>';
    }
}

function verwerfenZeile(transId) {
    const row = document.querySelector('#kategorisierungBody tr[data-trans-id="' + transId + '"]');
    if (!row) return;
    if (row.dataset.kiUnterkategorie !== undefined) delete row.dataset.kiUnterkategorie;
    const katSel = row.querySelector('.kategorie-select');
    if (katSel) {
        katSel.value = '';
        katSel.dispatchEvent(new Event('change'));
    }
    const status = row.querySelector('.kategorisierung-status');
    if (status) status.innerHTML = '';
}

async function kiVorschlag(transId, silent) {
    const row = document.querySelector('#kategorisierungBody tr[data-trans-id="' + transId + '"]');
    if (!row) return;
    const betrag = row.dataset.betrag !== '' && row.dataset.betrag != null ? parseFloat(row.dataset.betrag) : null;
    const payload = {
        verwendungszweck: row.dataset.vw || '',
        buchungstext: row.dataset.bt || '',
        gegenkonto_name: row.dataset.gk || '',
        betrag: betrag
    };
    const btn = row.querySelector('.btn-ki');
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>'; }
    try {
        const res = await fetch('/api/ai/kategorisiere/transaktion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const text = await res.text();
        var data;
        try {
            data = JSON.parse(text);
        } catch (parseErr) {
            if (!silent) showToast('KI-Antwort ungültig (z. B. Serverfehler)', true);
            if (btn) { btn.disabled = false; btn.textContent = 'KI'; }
            return;
        }
        if (data.success && data.vorschlag) {
            const v = data.vorschlag;
            const kat = (v.kategorie || '').trim();
            const unter = (v.unterkategorie != null && v.unterkategorie !== '') ? String(v.unterkategorie).trim() : '';
            const katSel = row.querySelector('.kategorie-select');
            if (katSel && kat) {
                katSel.value = kat;
                if (katSel.value !== kat) {
                    var opt = Array.prototype.find.call(katSel.options, function (o) {
                        return (o.value || '').trim().toLowerCase() === kat.toLowerCase();
                    });
                    if (opt) {
                        katSel.value = opt.value;
                    } else {
                        var newOpt = document.createElement('option');
                        newOpt.value = kat;
                        newOpt.textContent = kat;
                        katSel.appendChild(newOpt);
                        katSel.value = kat;
                    }
                }
                if (unter) row.dataset.kiUnterkategorie = unter;
                katSel.dispatchEvent(new Event('change'));
            }
            if (!silent) showToast('KI-Vorschlag: ' + (kat || '') + (unter ? ' / ' + unter : ''));
        } else {
            if (!silent) showToast(data.error || 'KI konnte keinen Vorschlag machen', true);
        }
    } catch (e) {
        if (!silent) showToast('KI-Anfrage fehlgeschlagen', true);
    }
    if (btn) { btn.disabled = false; btn.textContent = 'KI'; }
}

async function kiVorschlaegeVorladen() {
    const rows = document.querySelectorAll('#kategorisierungBody tr[data-trans-id]');
    const unkategorisiert = [];
    rows.forEach(function (tr) {
        const katSel = tr.querySelector('.kategorie-select');
        if (katSel && (!katSel.value || katSel.value === '')) unkategorisiert.push(parseInt(tr.dataset.transId, 10));
    });
    if (unkategorisiert.length === 0) {
        showToast('Keine unkategorisierten Zeilen auf dieser Seite.', true);
        return;
    }
    const btn = document.getElementById('btnKiVorladen');
    const statusEl = document.getElementById('kiVorladenStatus');
    if (btn) btn.disabled = true;
    if (statusEl) {
        statusEl.classList.remove('d-none');
        statusEl.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Lade KI-Vorschläge... (kann 1–2 Min. dauern)';
    }
    let done = 0;
    for (let i = 0; i < unkategorisiert.length; i++) {
        const transId = unkategorisiert[i];
        if (statusEl) statusEl.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> KI-Vorschläge ' + (i + 1) + '/' + unkategorisiert.length;
        await kiVorschlag(transId, true);
        done++;
        if (i < unkategorisiert.length - 1) await new Promise(function (r) { setTimeout(r, 400); });
    }
    if (statusEl) { statusEl.classList.add('d-none'); statusEl.innerHTML = ''; }
    if (btn) btn.disabled = false;
    showToast('KI-Vorschläge für ' + done + ' Zeilen geladen.');
}

async function belegSuchen(transId) {
    const row = document.querySelector('#kategorisierungBody tr[data-trans-id="' + transId + '"]');
    if (!row) return;
    const datum = (row.dataset.datum || '').trim();
    const betrag = row.dataset.betrag !== undefined && row.dataset.betrag !== '' ? row.dataset.betrag : '';
    const vw = (row.dataset.vw || '').trim();
    const bt = (row.dataset.bt || '').trim();
    const gk = (row.dataset.gk || '').trim();
    const referenz = [vw, bt, gk].filter(Boolean).join(' ').trim();
    const referenzParam = referenz.length > 500 ? referenz.substring(0, 500) : referenz;

    const modal = document.getElementById('modalBelegeEcodms');
    const body = document.getElementById('modalBelegeEcodmsBody');
    if (!modal || !body) return;
    body.innerHTML = '<p class="text-muted mb-0"><span class="spinner-border spinner-border-sm me-2"></span>Suche Belege in ecoDMS…</p>';
    const modalBs = new bootstrap.Modal(modal);
    modalBs.show();

    const params = new URLSearchParams();
    if (datum) params.set('datum', datum);
    if (betrag !== '') params.set('betrag', betrag);
    if (referenzParam) params.set('referenz', referenzParam);

    try {
        const res = await fetch('/api/bankenspiegel/transaktionen/ecodms/belege?' + params.toString(), { credentials: 'same-origin' });
        const text = await res.text();
        var data;
        try {
            data = JSON.parse(text);
        } catch (parseErr) {
            if (res.status === 401 || res.status === 302) {
                body.innerHTML = '<div class="alert alert-warning mb-0">Bitte erneut anmelden (Session abgelaufen?).</div>';
            } else if (res.status >= 500) {
                body.innerHTML = '<div class="alert alert-danger mb-0">ecoDMS oder Server meldet einen Fehler (Status ' + res.status + '). Prüfen: ecoDMS erreichbar? Zugangsdaten (ECODMS_USER/ECODMS_PASSWORD) konfiguriert?</div>';
            } else {
                body.innerHTML = '<div class="alert alert-warning mb-0">ecoDMS nicht erreichbar oder ungültige Antwort (Status ' + res.status + '). Bei Bedarf: Zugangsdaten und ecoDMS-URL prüfen.</div>';
            }
            return;
        }
        if (!data.success && data.error) {
            body.innerHTML = '<div class="alert alert-warning mb-0">' + escapeHtml(data.error) + '</div>';
            return;
        }
        const docs = data.documents || [];
        if (docs.length === 0) {
            const datumLabel = data.buchungsdatum || 'diesem Datum';
            body.innerHTML = '<div class="alert alert-info mb-0">Keine Belege zum Buchungsdatum <strong>' + escapeHtml(datumLabel) + '</strong> in ecoDMS gefunden. Ordner/Felder in ecoDMS oder Suchdatum prüfen.</div>';
            return;
        }
        const vorgeschlagenCount = (data.documents || []).filter(function (d) { return d.vorgeschlagen; }).length;
        const kreditor = data.kreditor_vermutet || '';
        const referenzHinweis = data.referenz_hinweis || '';
        let html = '<p class="small mb-2">Belege zum <strong>Buchungsdatum</strong> (konfigurierter Ordner + Buchhaltung). Bitte passenden Beleg auswählen.</p>';
        if (kreditor || referenzHinweis) {
            html += '<p class="small text-muted mb-3"><strong>Aus Transaktion (nur Hinweis):</strong> ';
            if (kreditor) html += '<span class="text-primary">' + escapeHtml(kreditor) + '</span>';
            if (kreditor && referenzHinweis) html += ' &middot; ';
            if (referenzHinweis) html += escapeHtml(referenzHinweis.length > 80 ? referenzHinweis.substring(0, 80) + '…' : referenzHinweis);
            html += '</p>';
        }
        if (vorgeschlagenCount > 0) html += '<p class="small text-success mb-2">' + vorgeschlagenCount + ' Beleg(e) mit passendem Text in den Attributen (Vorgeschlagen).</p>';
        html += '<div class="list-group list-group-flush">';
        docs.forEach(function (d, idx) {
            const attrs = d.attributes || {};
            const attrList = Object.keys(attrs).map(function (k) { return '<span class="me-2"><strong>' + escapeHtml(k) + ':</strong> ' + escapeHtml(attrs[k]) + '</span>'; });
            const attrBlock = attrList.length ? '<div class="small text-muted mt-1">' + attrList.join('<br>') + '</div>' : '';
            const badge = d.vorgeschlagen ? ' <span class="badge bg-success ms-2">Vorgeschlagen</span>' : '';
            const borderClass = d.vorgeschlagen ? ' border-start border-success border-3' : '';
            html += '<div class="list-group-item d-flex justify-content-between align-items-start' + borderClass + '">';
            html += '<div class="ms-2 me-2 flex-grow-1">';
            html += '<span class="fw-medium">Beleg #' + (idx + 1) + '</span>' + badge;
            if (attrBlock) html += attrBlock;
            html += '</div>';
            html += '<a href="' + escapeHtml(d.viewUrl || '') + '" class="btn btn-sm btn-outline-primary align-self-center" target="_blank" rel="noopener" download>Beleg anzeigen</a>';
            html += '</div>';
        });
        html += '</div>';
        body.innerHTML = html;
    } catch (e) {
        body.innerHTML = '<div class="alert alert-danger mb-0">Netzwerkfehler: ' + escapeHtml(e.message || 'Unbekannt') + '</div>';
    }
}

async function regelnAnwenden() {
    const btn = document.getElementById('btnRegeln');
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Läuft...'; }
    try {
        const res = await fetch('/api/bankenspiegel/transaktionen/kategorisieren', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ limit: 500, nur_unkategorisiert: true, mit_ki: false })
        });
        const data = await res.json();
        if (data.success && data.ergebnis) {
            const r = data.ergebnis;
            showToast('Regeln: ' + (r.aktualisiert || 0) + ' aktualisiert, ' + (r.uebersprungen || 0) + ' übersprungen.');
            loadTransaktionenKat();
        } else {
            showToast(data.error || 'Batch fehlgeschlagen', true);
        }
    } catch (e) {
        showToast('Fehler beim Regeln anwenden', true);
    }
    if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-gear me-1"></i>Regeln anwenden'; }
}

async function regelnErneutAnwenden() {
    const btn = document.getElementById('btnRegelnUeberschreiben');
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Läuft...'; }
    try {
        const res = await fetch('/api/bankenspiegel/transaktionen/kategorisieren', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ limit: 500, regeln_ueberschreiben: true })
        });
        const data = await res.json();
        if (data.success && data.ergebnis) {
            const r = data.ergebnis;
            showToast('Regeln erneut: ' + (r.aktualisiert || 0) + ' aktualisiert.');
            loadTransaktionenKat();
        } else {
            showToast(data.error || 'Regeln erneut anwenden fehlgeschlagen', true);
        }
    } catch (e) {
        showToast('Fehler beim Regeln erneut anwenden', true);
    }
    if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-arrow-repeat me-1"></i>Regeln erneut anwenden'; }
}

function applyFilter() {
    saveFilterToSession();
    currentOffset = 0;
    loadTransaktionenKat();
}

// --- Kategorisierung einmal initialisieren (Filter, Session, erste Ladung) ---
function ensureKategorisierungInit() {
    if (kategorisierungInitialized) return Promise.resolve();
    kategorisierungInitialized = true;
    return loadKategorien().then(function () {
        const von = document.getElementById('filterVon');
        const bis = document.getElementById('filterBis');
        const restored = loadFilterFromSession();
        if (!restored) {
            const vorbis = getVormonatVonBis();
            if (von) von.value = vorbis.von;
            if (bis) bis.value = vorbis.bis;
        }
        saveFilterToSession();
        loadTransaktionenKat();
        [von, bis].forEach(function (el) {
            if (el) el.addEventListener('change', saveFilterToSession);
        });
        const nurUnk = document.getElementById('nurUnkategorisiert');
        const nurTrain = document.getElementById('nurTrainierte');
        const filterKat = document.getElementById('filterKategorie');
        const suche = document.getElementById('filterSuche');
        if (nurUnk) nurUnk.addEventListener('change', function () { saveFilterToSession(); loadTransaktionenKat(); });
        if (nurTrain) nurTrain.addEventListener('change', function () { saveFilterToSession(); loadTransaktionenKat(); });
        if (filterKat) filterKat.addEventListener('change', saveFilterToSession);
        if (suche) suche.addEventListener('input', saveFilterToSession);
    });
}

// --- Tab-Steuerung und Start ---
document.addEventListener('DOMContentLoaded', function () {
    const mode = getModeFromUrl();
    setModeInUrl(mode);

    const tabUebersicht = document.getElementById('tab-uebersicht');
    const tabKategorisierung = document.getElementById('tab-kategorisierung');

    // Tab-Klick: URL setzen und bei Kategorisieren lazy init
    function onTabShown(e) {
        const targetId = e.target.getAttribute('data-bs-target');
        const isKat = targetId === '#panel-kategorisierung';
        const newMode = isKat ? 'kategorisierung' : 'uebersicht';
        setModeInUrl(newMode);
        if (isKat) {
            ensureKategorisierungInit();
        }
    }
    const tabContent = document.getElementById('transaktionenTabContent');
    if (tabContent) {
        tabContent.addEventListener('shown.bs.tab', onTabShown);
    }

    // Start: Tab per Bootstrap anzeigen und passende Logik starten
    const triggerId = mode === 'kategorisierung' ? 'tab-kategorisierung' : 'tab-uebersicht';
    const trigger = document.getElementById(triggerId);
    if (trigger && typeof bootstrap !== 'undefined' && bootstrap.Tab) {
        const tab = new bootstrap.Tab(trigger);
        tab.show();
    }
    if (mode === 'kategorisierung') {
        ensureKategorisierungInit();
    } else {
        loadTransaktionenUebersicht();
    }

    // Aktualisieren-Button
    const btnAktualisieren = document.getElementById('btnAktualisieren');
    if (btnAktualisieren) {
        btnAktualisieren.addEventListener('click', function () {
            if (getActiveTabPanel() === 'kategorisierung') {
                loadTransaktionenKat();
            } else {
                loadTransaktionenUebersicht();
            }
        });
    }
});
