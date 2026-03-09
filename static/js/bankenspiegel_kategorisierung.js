// Bankenspiegel – Kategorisierung (Buchhaltung)
// Transaktionen mit Kategorie/Unterkategorie versehen, Regeln/KI nutzen

let kategorienListe = [];      // [{ kategorie, unterkategorie }, ...]
let unterkategorienByKat = {}; // { "Personal": ["Gehalt", "Sozialversicherung", null], ... }
let currentLimit = 100;
let currentOffset = 0;
let currentTotal = 0;

function formatBetrag(betrag) {
    if (betrag === null || betrag === undefined) return '0,00 €';
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(betrag);
}

function formatDatum(datum) {
    if (!datum) return '–';
    const d = new Date(datum);
    return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function showToast(message, isError = false) {
    const toastEl = document.getElementById('toastMessage');
    const body = document.getElementById('toastBody');
    if (!toastEl || !body) return;
    toastEl.classList.remove('text-bg-success', 'text-bg-danger');
    toastEl.classList.add(isError ? 'text-bg-danger' : 'text-bg-success');
    body.textContent = message;
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

async function loadKategorien() {
    try {
        const res = await fetch('/api/bankenspiegel/kategorien');
        const data = await res.json();
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
    const unter = (selectedUnter == null || selectedUnter === '') ? '' : selectedUnter;
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
    const unter = (selectedUnter == null || selectedUnter === '') ? '' : selectedUnter;
    const options = unterkategorienByKat[kategorie] || [];
    let html = '<select class="form-select form-select-sm unterkategorie-select" data-trans-id="' + transId + '">';
    html += '<option value="">—</option>';
    options.forEach(function (u) {
        const val = (u == null || u === '') ? '' : u;
        const label = val === '' ? '—' : val;
        html += '<option value="' + escapeHtml(val) + '"' + (val === unter ? ' selected' : '') + '>' + escapeHtml(label) + '</option>';
    });
    html += '</select>';
    return html;
}

function escapeHtml(s) {
    if (s == null) return '';
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
}

function textZeile(t) {
    const v = (t.verwendungszweck || '').trim();
    const b = (t.buchungstext || '').trim();
    const g = (t.gegenkonto_name || '').trim();
    const parts = [v, b, g].filter(Boolean);
    return parts.length ? parts.join(' · ') : '—';
}

async function loadTransaktionen() {
    const nurUnk = document.getElementById('nurUnkategorisiert');
    const filterKat = document.getElementById('filterKategorie');
    const von = document.getElementById('filterVon');
    const bis = document.getElementById('filterBis');
    const suche = document.getElementById('filterSuche');
    const params = new URLSearchParams({
        nur_unkategorisiert: (nurUnk && nurUnk.checked) ? 'true' : 'false',
        limit: currentLimit,
        offset: currentOffset
    });
    if (filterKat && filterKat.value) params.set('kategorie', filterKat.value);
    if (von && von.value) params.set('von', von.value);
    if (bis && bis.value) params.set('bis', bis.value);
    if (suche && suche.value) params.set('suche', suche.value);

    const tbody = document.getElementById('kategorisierungBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4"><span class="spinner-border spinner-border-sm me-2"></span>Lade...</td></tr>';

    try {
        const res = await fetch('/api/bankenspiegel/transaktionen/kategorisierung?' + params.toString());
        const data = await res.json();
        if (!data.success) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Fehler: ' + escapeHtml(data.error || 'Unbekannt') + '</td></tr>';
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
                const txtShort = txt.length > 120 ? txt.substring(0, 120) + '…' : txt;
                const hatKategorie = kat.length > 0;
                const kiLernenHtml = hatKategorie
                    ? '<span class="text-info kategorisierung-ki-lernen ms-1" title="Wird als KI-Lernbeispiel genutzt"><i class="bi bi-journal-check me-1"></i>KI-Lernbeispiel</span>'
                    : '';
                return '<tr data-trans-id="' + t.id + '" data-vw="' + escapeHtml(t.verwendungszweck || '') + '" data-bt="' + escapeHtml(t.buchungstext || '') + '" data-gk="' + escapeHtml(t.gegenkonto_name || '') + '" data-betrag="' + (t.betrag != null ? t.betrag : '') + '">' +
                    '<td>' + formatDatum(t.buchungsdatum) + '</td>' +
                    '<td class="text-end">' + formatBetrag(t.betrag) + '</td>' +
                    '<td class="small" data-full="' + escapeHtml(txt) + '">' + escapeHtml(txtShort) + '</td>' +
                    '<td>' + bauKategorieDropdown(t.id, kat, unter) + '</td>' +
                    '<td>' + bauUnterkategorieDropdown(t.id, kat, unter) + '</td>' +
                    '<td class="aktionen-cell">' +
                    '<button type="button" class="btn btn-sm btn-outline-primary me-1 btn-speichern" onclick="speichern(' + t.id + ')" title="Speichern">Speichern</button>' +
                    '<button type="button" class="btn btn-sm btn-outline-secondary btn-ki" data-trans-id="' + t.id + '" onclick="kiVorschlag(' + t.id + ')" title="KI-Vorschlag (auch bei bereits kategorisierten Zeilen)">KI</button>' +
                    '<span class="kategorisierung-status ms-2"></span>' +
                    kiLernenHtml +
                    '</td></tr>';
            }).join('');
            // Unterkategorie-Dropdowns bei Kategorie-Änderung neu füllen
            document.querySelectorAll('.kategorie-select').forEach(function (sel) {
                sel.addEventListener('change', function () {
                    const transId = parseInt(this.dataset.transId, 10);
                    const row = this.closest('tr');
                    const unterCell = row.querySelector('td:nth-child(5)');
                    if (unterCell) {
                        const neueKat = this.value;
                        const unterSelect = row.querySelector('.unterkategorie-select');
                        const bisherUnter = unterSelect ? unterSelect.value : '';
                        unterCell.innerHTML = bauUnterkategorieDropdown(transId, neueKat, bisherUnter);
                    }
                });
            });
        }

        document.getElementById('infoZeile').textContent =
            (currentOffset + 1) + '–' + (currentOffset + rows.length) + ' von ' + currentTotal + ' Transaktionen';
        renderPagination();
    } catch (e) {
        console.error('Transaktionen laden:', e);
        if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Netzwerkfehler beim Laden.</td></tr>';
    }
}

function renderPagination() {
    const ul = document.getElementById('pagination');
    if (!ul) return;
    const total = Number(currentTotal) || 0;
    const pages = Math.ceil(total / currentLimit) || 1;
    const page = Math.floor(currentOffset / currentLimit) + 1;
    ul.innerHTML = '';
    if (pages <= 1 || total <= currentLimit) return;
    const add = function (label, off, disabled) {
        const li = document.createElement('li');
        li.className = 'page-item' + (disabled ? ' disabled' : '');
        const a = document.createElement('a');
        a.className = 'page-link';
        a.href = '#';
        a.textContent = label;
        if (!disabled) a.onclick = function (e) { e.preventDefault(); currentOffset = off; loadTransaktionen(); };
        li.appendChild(a);
        ul.appendChild(li);
    };
    add('«', currentOffset - currentLimit, currentOffset <= 0);
    add('Seite ' + page + ' / ' + pages, currentOffset, true);
    add('»', currentOffset + currentLimit, currentOffset + currentLimit >= total);
}

function getRowKategorieUnter(transId) {
    const row = document.querySelector('tr[data-trans-id="' + transId + '"]');
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
    if (!kategorie) {
        showToast('Bitte zuerst eine Kategorie wählen.', true);
        return;
    }
    try {
        const res = await fetch('/api/bankenspiegel/transaktionen/' + transId + '/kategorie', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ kategorie: kategorie || '', unterkategorie: unterkategorie || '' })
        });
        const data = await res.json();
        if (data.success) {
            showToast('Gespeichert.');
            zeigeGespeichert(transId);
            if (document.getElementById('nurUnkategorisiert').checked) loadTransaktionen();
        } else {
            showToast(data.error || 'Speichern fehlgeschlagen', true);
        }
    } catch (e) {
        showToast('Fehler beim Speichern', true);
    }
}

function zeigeGespeichert(transId) {
    const row = document.querySelector('tr[data-trans-id="' + transId + '"]');
    if (!row) return;
    row.classList.add('table-success');
    const status = row.querySelector('.kategorisierung-status');
    if (status) {
        status.innerHTML = '<span class="text-success"><i class="bi bi-check-circle-fill me-1"></i>Gespeichert</span>';
        status.setAttribute('title', 'Kategorie wurde gespeichert');
    }
}

async function kiVorschlag(transId, silent) {
    const row = document.querySelector('tr[data-trans-id="' + transId + '"]');
    if (!row) return;
    const betrag = row.dataset.betrag !== '' && row.dataset.betrag != null ? parseFloat(row.dataset.betrag) : null;
    const payload = {
        verwendungszweck: row.dataset.vw || '',
        buchungstext: row.dataset.bt || '',
        gegenkonto_name: row.dataset.gk || '',
        betrag: betrag
    };
    const btn = row.querySelector('.btn-ki') || row.querySelector('button[onclick*="kiVorschlag"]');
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span>'; }
    try {
        const res = await fetch('/api/ai/kategorisiere/transaktion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success && data.vorschlag) {
            const v = data.vorschlag;
            const katSel = row.querySelector('.kategorie-select');
            const unterCell = row.querySelector('td:nth-child(5)');
            if (katSel) {
                katSel.value = v.kategorie || '';
                katSel.dispatchEvent(new Event('change'));
            }
            setTimeout(function () {
                const unterSel = row.querySelector('.unterkategorie-select');
                if (unterSel && v.unterkategorie != null) unterSel.value = v.unterkategorie;
            }, 50);
            if (!silent) showToast('KI-Vorschlag: ' + (v.kategorie || '') + (v.unterkategorie ? ' / ' + v.unterkategorie : ''));
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
        if (statusEl) statusEl.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> KI-Vorschläge ' + (i + 1) + '/' + unkategorisiert.length + ' (kann 1–2 Min. dauern)';
        await kiVorschlag(transId, true);
        done++;
        if (i < unkategorisiert.length - 1) await new Promise(function (r) { setTimeout(r, 400); });
    }
    if (statusEl) {
        statusEl.classList.add('d-none');
        statusEl.innerHTML = '';
    }
    if (btn) btn.disabled = false;
    showToast('KI-Vorschläge für ' + done + ' Zeilen geladen.');
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
            loadTransaktionen();
        } else {
            showToast(data.error || 'Batch fehlgeschlagen', true);
        }
    } catch (e) {
        showToast('Fehler beim Regeln anwenden', true);
    }
    if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-gear me-1"></i>Regeln anwenden'; }
}

function applyFilter() {
    currentOffset = 0;
    loadTransaktionen();
}

document.addEventListener('DOMContentLoaded', function () {
    loadKategorien().then(function () {
        const bis = document.getElementById('filterBis');
        const von = document.getElementById('filterVon');
        if (bis && !bis.value) {
            const d = new Date();
            bis.value = d.toISOString().slice(0, 10);
        }
        if (von && !von.value) {
            const d = new Date();
            d.setMonth(d.getMonth() - 3);
            von.value = d.toISOString().slice(0, 10);
        }
        loadTransaktionen();
    });
});
