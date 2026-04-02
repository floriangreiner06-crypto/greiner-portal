# Verkäufer-Zeitstrahl Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persönlicher NW/GW-Zielfortschritt pro Verkäufer im Auftragseingang — Monats- und Jahresansicht mit Hero-Card und Inline-Balken.

**Architecture:** Neuer API-Endpoint `/api/verkauf/auftragseingang/zeitstrahl` liefert pro Verkäufer Monatsziel, kumuliertes NW-Ziel und Jahresziel. Das Frontend ruft diesen Endpoint parallel zu den bestehenden Auftragseingang-Endpoints auf und rendert Hero-Card (Einzelverkäufer) sowie Inline-Fortschrittsbalken (VKL-Tabelle).

**Tech Stack:** Flask/Python (Backend), Vanilla JS + Bootstrap 5 (Frontend), PostgreSQL (Datenquelle)

**Spec:** `docs/superpowers/specs/2026-04-02-verkaufer-zeitstrahl-design.md`
**Mockup:** `static/mockups/zeitstrahl_verkauf_v3.html`

---

## File Structure

| Aktion | Datei | Verantwortung |
|--------|-------|---------------|
| Modify | `api/verkauf_api.py:637` | Neuer Endpoint `/auftragseingang/zeitstrahl` |
| Modify | `templates/verkauf_auftragseingang.html` | Hero-Card + Inline-Balken Rendering |

Keine neuen Dateien nötig — alles in bestehende Dateien integriert.

---

### Task 1: Backend — Neuer Zeitstrahl-Endpoint

**Files:**
- Modify: `api/verkauf_api.py` (nach Zeile 637, nach `get_auftragseingang_jahresuebersicht`)

Dieser Endpoint liefert pro Verkäufer die Zieldaten für den Zeitstrahl. Er kombiniert:
- Monatsziele aus `get_monatsziele_konzern_dict()` (SSOT)
- Kumuliertes NW-Ziel aus `get_nw_ziel_verkaeufer_monat()` (SSOT Zielprämie)
- Kumuliertes NW-IST aus `VerkaufData.get_auftragseingang_detail()` (SSOT Auftragseingang)
- Jahresziele aus `verkaeufer_ziele`-Tabelle

- [ ] **Step 1: Endpoint-Code schreiben**

In `api/verkauf_api.py` nach Zeile 637 (nach `get_auftragseingang_jahresuebersicht`) einfügen:

```python
@verkauf_api.route('/auftragseingang/zeitstrahl', methods=['GET'])
@login_required
def get_auftragseingang_zeitstrahl():
    """
    GET /api/verkauf/auftragseingang/zeitstrahl?jahr=2026&monat=4&location=1
    Liefert pro Verkäufer: Monatsziel NW/GW, kumuliertes NW-Ziel (Zielprämie),
    kumuliertes NW-IST, Jahresziel NW/GW.
    """
    jahr = request.args.get('jahr', datetime.now().year, type=int)
    monat = request.args.get('monat', datetime.now().month, type=int)
    location = request.args.get('location', type=int)
    forced_vk = None
    if _filter_mode_force_own('auftragseingang'):
        forced_vk = _get_current_user_salesman_number()

    try:
        from api.verkaeufer_zielplanung_api import (
            get_monatsziele_konzern_dict, get_nw_ziel_verkaeufer_monat)
        import calendar

        # 1) Monatsziele (NW + GW) pro Verkäufer für den gewählten Monat
        ziele_data = get_monatsziele_konzern_dict(jahr, monat)
        ziele_liste = ziele_data.get('ziele', []) if ziele_data.get('success') else []

        # 2) Kumuliertes NW-IST: Auftragseingang Jan bis Monatsende per Verkäufer
        last_day = calendar.monthrange(jahr, monat)[1]
        von = f"{jahr}-01-01"
        bis = f"{jahr}-{monat:02d}-{last_day:02d}"
        detail_data = VerkaufData.get_auftragseingang_detail(
            von=von, bis=bis, location=location)
        ist_by_nr = {}
        if detail_data.get('success'):
            for vk in detail_data.get('verkaufer', []):
                nr = vk.get('verkaufer_nummer')
                if nr:
                    ist_by_nr[int(nr)] = {
                        'kum_ist_nw': (vk.get('summe_neu') or 0) + (vk.get('summe_test_vorfuehr') or 0),
                        'kum_ist_gw': vk.get('summe_gebraucht') or 0,
                    }

        # 3) Jahresziele aus verkaeufer_ziele
        jahres_ziele = {}
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "SELECT mitarbeiter_nr, ziel_nw, ziel_gw FROM verkaeufer_ziele WHERE kalenderjahr = %s",
                (jahr,))
            for row in cur.fetchall():
                jahres_ziele[int(row['mitarbeiter_nr'])] = {
                    'jahres_ziel_nw': int(row['ziel_nw'] or 0),
                    'jahres_ziel_gw': int(row['ziel_gw'] or 0),
                }
            conn.close()
        except Exception:
            pass

        # 4) Pro Verkäufer zusammenbauen
        ergebnis = []
        for z in ziele_liste:
            nr = int(z['mitarbeiter_nr'])
            if forced_vk and nr != forced_vk:
                continue

            # Kumuliertes NW-Ziel: Summe der Monatsziele Jan bis aktueller Monat
            kum_ziel_nw = 0
            for m in range(1, monat + 1):
                kum_ziel_nw += get_nw_ziel_verkaeufer_monat(nr, jahr, m)

            ist = ist_by_nr.get(nr, {})
            jz = jahres_ziele.get(nr, {})

            ergebnis.append({
                'mitarbeiter_nr': nr,
                'name': z.get('name', ''),
                'monats_ziel_nw': z.get('ziel_nw') or 0,
                'monats_ziel_gw': z.get('ziel_gw') or 0,
                'kum_ziel_nw': kum_ziel_nw,
                'kum_ist_nw': ist.get('kum_ist_nw', 0),
                'kum_ist_gw': ist.get('kum_ist_gw', 0),
                'jahres_ziel_nw': jz.get('jahres_ziel_nw', 0),
                'jahres_ziel_gw': jz.get('jahres_ziel_gw', 0),
            })

        return jsonify({'success': True, 'jahr': jahr, 'monat': monat, 'verkaufer': ergebnis})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
```

- [ ] **Step 2: API testen**

```bash
curl -s -b /tmp/cookies.txt "http://drive:5002/api/verkauf/auftragseingang/zeitstrahl?jahr=2026&monat=4" | python3 -m json.tool | head -40
```

Erwartetes Ergebnis: JSON mit `success: true` und `verkaufer`-Array mit Einträgen die `monats_ziel_nw`, `kum_ziel_nw`, `kum_ist_nw`, `jahres_ziel_nw` etc. enthalten.

Falls Auth nötig, im Browser testen: http://drive:5002/api/verkauf/auftragseingang/zeitstrahl?jahr=2026&monat=4

- [ ] **Step 3: Commit**

```bash
git add api/verkauf_api.py
git commit -m "feat(verkauf): API-Endpoint /auftragseingang/zeitstrahl für Verkäufer-Zielfortschritt"
```

---

### Task 2: Frontend Monatsansicht — Hero-Card + Inline-Balken

**Files:**
- Modify: `templates/verkauf_auftragseingang.html`

Änderungen am JavaScript: neue Variable `zeitstrahlData`, Fetch in `loadData()`, Hero-Card in `loadSummary()`, Inline-Balken in `loadDetails()`.

- [ ] **Step 1: Zeitstrahl-Variable und Fetch hinzufügen**

In `templates/verkauf_auftragseingang.html` nach Zeile 200 (`let monatszieleData = null;`) einfügen:

```javascript
let zeitstrahlData = null; // Zeitstrahl: Zieldaten pro Verkäufer (NW kum + GW)
```

In der `loadData()`-Funktion (ca. Zeile 310-350), dort wo `monatszieleData` gefetched wird (Zeile 333-339), **danach** den Zeitstrahl-Fetch einfügen:

```javascript
// Zeitstrahl-Daten laden (Monatsziele + kumuliert + Jahresziel)
if (currentPeriod === 'month' || currentPeriod === 'year' || currentPeriod === 'fiscal') {
    try {
        const zsMonat = currentPeriod === 'month' ? currentMonth : new Date().getMonth() + 1;
        const zsJahr = currentPeriod === 'month' ? currentYear : currentYear;
        let zsUrl = `/api/verkauf/auftragseingang/zeitstrahl?jahr=${zsJahr}&monat=${zsMonat}`;
        if (currentLocation) zsUrl += `&location=${currentLocation}`;
        const zsRes = await fetch(zsUrl);
        const zsJson = await zsRes.json();
        zeitstrahlData = zsJson.success ? zsJson.verkaufer : null;
    } catch(e) { zeitstrahlData = null; }
}
```

- [ ] **Step 2: Hero-Card für Monatsansicht rendern**

In `loadSummary()` (Zeile 435+), **nach** dem Rendering der Summary-Cards und **nach** der Zielerfüllung-Zeile (ca. Zeile 549), aber **vor** dem Schließen des summaryContainer-HTML, folgendes einfügen.

Suche die Stelle wo `summaryContainer.innerHTML = html;` steht (ca. Zeile 623) und füge **davor** diesen Code ein:

```javascript
// === Zeitstrahl Hero-Card (Monatsansicht, Einzelverkäufer) ===
if (currentPeriod === 'month' && zeitstrahlData && currentVerkaufer) {
    const zsVk = zeitstrahlData.find(z => String(z.mitarbeiter_nr) === String(currentVerkaufer));
    if (zsVk) {
        const vkName = zsVk.name || 'Verkäufer';
        const monatName = document.getElementById('monthSelect').options[currentMonth - 1]?.text || '';
        // NW Monat
        const nwIst = zsVk.kum_ist_nw; // kum bis aktueller Monat = enthält auch diesen Monat
        // Für Monats-IST brauchen wir den Detail-Wert, nicht den kumulierten
        // Wir nehmen die Werte aus der Detail-Tabelle
        const detailRows = document.querySelectorAll('#verkauferContainer table tbody tr');
        let monatIstNw = 0, monatIstGw = 0;
        detailRows.forEach(row => {
            const cells = row.querySelectorAll('td');
            // Wird nach loadDetails befüllt — fallback auf zeitstrahl
        });
        // Einfacher: NW/GW IST aus summary-Daten
        const nwMonatIst = parseInt(document.querySelector('[data-summary-nw]')?.textContent) || 0;
        const gwMonatIst = parseInt(document.querySelector('[data-summary-gw]')?.textContent) || 0;

        const mzNw = zsVk.monats_ziel_nw;
        const mzGw = zsVk.monats_ziel_gw;
        const kumZielNw = zsVk.kum_ziel_nw;
        const kumIstNw = zsVk.kum_ist_nw;
        const pctNw = mzNw > 0 ? Math.round((nwMonatIst / mzNw) * 100) : 0;
        const pctGw = mzGw > 0 ? Math.round((gwMonatIst / mzGw) * 100) : 0;
        const kumPctNw = kumZielNw > 0 ? Math.round((kumIstNw / kumZielNw) * 100) : 0;

        function zsColor(pct) {
            if (pct >= 100) return '#198754';
            if (pct >= 75) return '#e67e22';
            return '#dc3545';
        }

        // Hero-Card HTML ... (wird in Step 3 definiert)
    }
}
```

Halt — das wird unübersichtlich wenn ich versuche die IST-Daten aus dem DOM zu lesen. Besser: Die Hero-Card wird in einer eigenen Funktion gerendert, die **nach** loadSummary und loadDetails aufgerufen wird, wenn alle Daten da sind.

**Revidierter Ansatz:** Neue Funktion `renderZeitstrahlHeroCard()` die nach `loadData()` aufgerufen wird.

Ersetze den obigen Code-Block. Stattdessen:

Füge **vor** der `loadData()`-Funktion (ca. Zeile 300) einen neuen Container im HTML ein. Suche die Zeile mit `<div class="row mb-4" id="prognoseRow"` (Zeile 95) und füge **danach** (nach dem schließenden `</div>` des prognoseRow auf Zeile 128) ein:

```html
<!-- Zeitstrahl Hero-Card -->
<div class="row mb-4" id="zeitstrahlHeroRow" style="display:none;">
    <div class="col-12">
        <div id="zeitstrahlHeroContainer"></div>
    </div>
</div>
```

Dann füge am Ende des `<script>`-Blocks (vor `</script>`) eine neue Funktion ein:

```javascript
// =============================================
// ZEITSTRAHL: Hero-Card + Hilfs-Funktionen
// =============================================
function zeitstrahlColor(pct) {
    if (pct >= 100) return '#198754';
    if (pct >= 75) return '#e67e22';
    return '#dc3545';
}

function renderZeitstrahlHeroCard() {
    const heroRow = document.getElementById('zeitstrahlHeroRow');
    const container = document.getElementById('zeitstrahlHeroContainer');
    if (!zeitstrahlData || !currentVerkaufer) {
        heroRow.style.display = 'none';
        return;
    }

    const zsVk = zeitstrahlData.find(z => String(z.mitarbeiter_nr) === String(currentVerkaufer));
    if (!zsVk) { heroRow.style.display = 'none'; return; }

    const monatNamen = ['Januar','Februar','März','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember'];
    const vkName = zsVk.name || '';

    if (currentPeriod === 'month') {
        // --- Monats-IST aus Detail-Daten ermitteln ---
        let monatIstNw = 0, monatIstGw = 0;
        const detailRows = document.querySelectorAll('#verkauferContainer table tbody tr[data-vk-nr]');
        detailRows.forEach(row => {
            if (row.dataset.vkNr === String(currentVerkaufer)) {
                monatIstNw = parseInt(row.dataset.istNw) || 0;
                monatIstGw = parseInt(row.dataset.istGw) || 0;
            }
        });

        const mzNw = zsVk.monats_ziel_nw;
        const mzGw = zsVk.monats_ziel_gw;
        const pctNw = mzNw > 0 ? Math.round((monatIstNw / mzNw) * 100) : 0;
        const pctGw = mzGw > 0 ? Math.round((monatIstGw / mzGw) * 100) : 0;
        const kumZiel = zsVk.kum_ziel_nw;
        const kumIst = zsVk.kum_ist_nw;
        const kumPct = kumZiel > 0 ? Math.round((kumIst / kumZiel) * 100) : 0;

        container.innerHTML = `
        <div class="card shadow-sm" style="border-left: 4px solid #0d6efd;">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-md-4">
                        <h5 class="mb-1"><i class="bi bi-person-circle text-primary"></i> Dein Monatsfortschritt</h5>
                        <p class="text-muted mb-0" style="font-size:0.85rem;">${monatNamen[currentMonth-1]} ${currentYear} — ${vkName}</p>
                    </div>
                    <div class="col-md-4">
                        <div style="background:#f8f9fa; border-radius:8px; padding:12px 16px; text-align:center;">
                            <div style="font-size:0.75rem; color:#6c757d; text-transform:uppercase;">Neuwagen</div>
                            <div style="font-size:1.8rem; font-weight:700; color:${zeitstrahlColor(pctNw)};">${monatIstNw} <small style="font-size:0.9rem; color:#6c757d;">/ ${mzNw}</small></div>
                            <div class="progress mt-1" style="height:8px;">
                                <div class="progress-bar" style="width:${Math.min(pctNw,100)}%; background:${zeitstrahlColor(pctNw)};"></div>
                            </div>
                            <div style="font-size:0.8rem; color:#6c757d;" class="mt-1">${pctNw}% Zielerfüllung</div>
                            <div style="font-size:0.72rem; color:#6c757d; margin-top:6px; padding-top:6px; border-top:1px dashed #dee2e6;">
                                <i class="bi bi-bar-chart-steps"></i>
                                Kum. Jan–${monatNamen[currentMonth-1].substring(0,3)}: <span style="font-weight:700; color:${zeitstrahlColor(kumPct)};">${kumIst}</span> / ${kumZiel} (${kumPct}%)
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div style="background:#f8f9fa; border-radius:8px; padding:12px 16px; text-align:center;">
                            <div style="font-size:0.75rem; color:#6c757d; text-transform:uppercase;">Gebrauchtwagen</div>
                            <div style="font-size:1.8rem; font-weight:700; color:${zeitstrahlColor(pctGw)};">${monatIstGw} <small style="font-size:0.9rem; color:#6c757d;">/ ${mzGw}</small></div>
                            <div class="progress mt-1" style="height:8px;">
                                <div class="progress-bar" style="width:${Math.min(pctGw,100)}%; background:${zeitstrahlColor(pctGw)};"></div>
                            </div>
                            <div style="font-size:0.8rem; color:#6c757d;" class="mt-1">${pctGw}% Zielerfüllung</div>
                        </div>
                    </div>
                </div>
                <!-- Mini-Timeline NW kumuliert -->
                <div class="mt-3 pt-2 border-top" id="zeitstrahlMiniTimeline"></div>
            </div>
        </div>`;
        heroRow.style.display = '';

        // Mini-Timeline asynchron laden (Jahresübersicht für diesen Verkäufer)
        loadZeitstrahlMiniTimeline(currentYear, currentVerkaufer);

    } else if (currentPeriod === 'year' || currentPeriod === 'fiscal') {
        // Jahresansicht: Hero-Card mit Jahresziel + kum. Reminder
        // Daten kommen aus loadZielauswertung — Hero-Card dort erweitern (Task 3)
        heroRow.style.display = 'none';
    } else {
        heroRow.style.display = 'none';
    }
}

async function loadZeitstrahlMiniTimeline(jahr, verkaufer) {
    const container = document.getElementById('zeitstrahlMiniTimeline');
    if (!container) return;
    try {
        const modus = currentPeriod === 'fiscal' ? 'geschaeftsjahr' : 'kalenderjahr';
        let url = `/api/verkauf/auftragseingang/jahresuebersicht?jahr=${jahr}&modus=${modus}&verkaufer=${verkaufer}`;
        if (currentLocation) url += `&location=${currentLocation}`;
        const res = await fetch(url);
        const data = await res.json();
        if (!data.success || !data.monate) { container.innerHTML = ''; return; }

        const aktMonat = new Date().getMonth() + 1;
        const labels = ['J','F','M','A','M','J','J','A','S','O','N','D'];
        let barsHtml = '';
        let labelsHtml = '';
        data.monate.forEach((m, i) => {
            const kumPct = m.kum_ziel_nw > 0 ? Math.round((m.kum_ist_nw / m.kum_ziel_nw) * 100) : 0;
            const isCurrent = m.monat === aktMonat && m.jahr === new Date().getFullYear();
            const isFuture = m.ist_zukunft;
            const height = isFuture ? 15 : Math.max(15, Math.min(90, kumPct));
            const color = isFuture ? '' : `background:${zeitstrahlColor(kumPct)};`;
            const cls = isFuture ? 'future' : (isCurrent ? 'current' : '');
            barsHtml += `<div class="month-bar ${cls}" style="height:${height}%;${color}" title="${labels[m.monat-1]}: ${m.kum_ist_nw}/${m.kum_ziel_nw} kum (${kumPct}%)"></div>`;
            labelsHtml += `<span class="${isCurrent ? 'current' : ''}">${labels[m.monat-1]}</span>`;
        });
        container.innerHTML = `
            <small class="text-muted"><i class="bi bi-calendar3"></i> Jahresverlauf NW — kumulierte Zielerfüllung</small>
            <div class="mini-timeline mt-1">${barsHtml}</div>
            <div class="mini-timeline-labels">${labelsHtml}</div>`;
    } catch(e) { container.innerHTML = ''; }
}
```

- [ ] **Step 3: CSS für Zeitstrahl-Komponenten hinzufügen**

Im `{% block content %}` vor dem Container-Start (Zeile 4) oder besser in einem `{% block styles %}` (falls vorhanden, sonst als `<style>` innerhalb `{% block content %}`), **vor** dem `<div class="container-fluid mt-4">` einfügen:

```html
<style>
/* Zeitstrahl */
.mini-timeline { display:flex; gap:3px; align-items:flex-end; height:40px; }
.mini-timeline .month-bar { flex:1; border-radius:2px 2px 0 0; min-width:0; transition:all 0.2s; }
.mini-timeline .month-bar.current { outline:2px solid #0d6efd; outline-offset:1px; }
.mini-timeline .month-bar.future { background:#e9ecef !important; opacity:0.5; }
.mini-timeline-labels { display:flex; gap:3px; }
.mini-timeline-labels span { flex:1; text-align:center; font-size:0.6rem; color:#6c757d; }
.mini-timeline-labels span.current { font-weight:700; color:#0d6efd; }
.inline-progress { height:18px; border-radius:3px; background:#e9ecef; position:relative; min-width:80px; }
.inline-progress-bar { height:100%; border-radius:3px; }
.inline-progress-text { position:absolute; top:0;left:0;right:0;bottom:0; display:flex; align-items:center; justify-content:center; font-size:0.7rem; font-weight:600; color:#333; }
.inline-kum { font-size:0.62rem; color:#888; text-align:center; margin-top:1px; }
</style>
```

- [ ] **Step 4: loadData() aufrufen und Hero-Card triggern**

In `loadData()` (ca. Zeile 310), am Ende der Funktion (nach `loadDetails()` und `loadZielauswertung()` Aufrufe), einfügen:

```javascript
// Zeitstrahl Hero-Card rendern (nachdem Detail-Daten geladen)
renderZeitstrahlHeroCard();
```

- [ ] **Step 5: Detail-Tabelle mit data-Attributen für IST-Werte erweitern**

In `loadDetails()` (Zeile 630+), dort wo die Verkäufer-Zeilen gerendert werden, das `<tr>` um data-Attribute erweitern damit `renderZeitstrahlHeroCard()` die IST-Werte lesen kann.

Suche die Stelle wo die TR-Zeile pro Verkäufer erstellt wird und ergänze:

```javascript
// Bestehende Zeile erweitern:
row += `<tr data-vk-nr="${vk.verkaufer_nummer}" data-ist-nw="${(vk.summe_neu || 0) + (vk.summe_test_vorfuehr || 0)}" data-ist-gw="${vk.summe_gebraucht || 0}">`;
```

- [ ] **Step 6: Inline-Fortschrittsbalken in VKL-Tabelle (Monatsansicht)**

In `loadDetails()` (Zeile 630+), dort wo die Ziel-Spalten gerendert werden (Zeile 669+), die bestehende Ziel-Darstellung durch Fortschrittsbalken ersetzen.

Ersetze die bestehende Ziel-Spalten-Logik (Zeilen 669-687) mit:

```javascript
// Ziel-Spalten Header
if (currentPeriod === 'month' && (monatszieleData || zeitstrahlData)) {
    headerHtml += '<th style="min-width:150px;">Ziel NW</th><th style="min-width:140px;">Ziel GW</th>';
}

// Pro Verkäufer-Zeile:
if (currentPeriod === 'month' && zeitstrahlData) {
    const zsVk = zeitstrahlData.find(z => String(z.mitarbeiter_nr) === String(vk.verkaufer_nummer));
    if (zsVk) {
        const istNw = (vk.summe_neu || 0) + (vk.summe_test_vorfuehr || 0);
        const istGw = vk.summe_gebraucht || 0;
        const mzNw = zsVk.monats_ziel_nw;
        const mzGw = zsVk.monats_ziel_gw;
        const pctNw = mzNw > 0 ? Math.round((istNw / mzNw) * 100) : 0;
        const pctGw = mzGw > 0 ? Math.round((istGw / mzGw) * 100) : 0;
        const kumPct = zsVk.kum_ziel_nw > 0 ? Math.round((zsVk.kum_ist_nw / zsVk.kum_ziel_nw) * 100) : 0;
        const kumCheck = kumPct >= 100 ? ' <span style="color:#198754;">&#10003;</span>' : '';

        row += `<td>
            <div class="inline-progress">
                <div class="inline-progress-bar" style="width:${Math.min(pctNw,100)}%; background:${zeitstrahlColor(pctNw)};"></div>
                <div class="inline-progress-text">${istNw}/${mzNw} (${pctNw}%)</div>
            </div>
            <div class="inline-kum">kum. ${zsVk.kum_ist_nw}/${zsVk.kum_ziel_nw} (${kumPct}%)${kumCheck}</div>
        </td>`;
        row += `<td>
            <div class="inline-progress">
                <div class="inline-progress-bar" style="width:${Math.min(pctGw,100)}%; background:${zeitstrahlColor(pctGw)};"></div>
                <div class="inline-progress-text">${istGw}/${mzGw} (${pctGw}%)</div>
            </div>
        </td>`;
    } else {
        row += '<td>-</td><td>-</td>';
    }
} else if (currentPeriod === 'month' && monatszieleData) {
    // Fallback: bestehende Ziel-Darstellung beibehalten
    // ... (existierender Code bleibt als Fallback)
}
```

- [ ] **Step 7: Browser-Test Monatsansicht**

1. Öffne http://drive:5002/verkauf/auftragseingang
2. Wähle "Dieser Monat" + einen Verkäufer aus dem Dropdown
3. Prüfe: Hero-Card erscheint mit NW/GW Balken + Kum.-Reminder + Mini-Timeline
4. Wähle "Alle Verkäufer"
5. Prüfe: Hero-Card verschwindet, Tabelle zeigt Inline-Balken pro Verkäufer

- [ ] **Step 8: Commit**

```bash
git add templates/verkauf_auftragseingang.html
git commit -m "feat(verkauf): Zeitstrahl Hero-Card + Inline-Balken Monatsansicht"
```

---

### Task 3: Frontend Jahresansicht — Hero-Card Erweiterung + VKL-Tabelle

**Files:**
- Modify: `templates/verkauf_auftragseingang.html`

Die Jahresansicht hat bereits eine Hero-Card (`loadZielauswertung()`). Diese wird erweitert um:
- Kum.-Reminder unter dem NW-Balken (bei Einzelverkäufer)
- Inline-Balken in der VKL-Tabelle

- [ ] **Step 1: Zeitstrahl-Daten auch bei Jahresansicht laden**

Im Zeitstrahl-Fetch-Code (Task 2, Step 1) ist `currentPeriod === 'year' || 'fiscal'` bereits abgedeckt. Prüfen dass `zsMonat` korrekt gesetzt ist:

```javascript
// Für Jahresansicht: aktuellen Kalendermonat verwenden
const zsMonat = currentPeriod === 'month' ? currentMonth : new Date().getMonth() + 1;
const zsJahr = currentYear;
```

- [ ] **Step 2: loadZielauswertung() erweitern — Kum.-Reminder bei Einzelverkäufer**

In `loadZielauswertung()` (Zeile 708+), dort wo der NW-Balken gerendert wird, **nach** dem `ziel-sub` (Zielerfüllung %) einfügen:

```javascript
// Kum.-Reminder (NW) wenn Einzelverkäufer und zeitstrahlData vorhanden
let kumReminderHtml = '';
if (verkaufer && zeitstrahlData) {
    const zsVk = zeitstrahlData.find(z => String(z.mitarbeiter_nr) === String(verkaufer));
    if (zsVk && zsVk.kum_ziel_nw > 0) {
        const kumPct = Math.round((zsVk.kum_ist_nw / zsVk.kum_ziel_nw) * 100);
        kumReminderHtml = `
            <div style="font-size:0.72rem; color:#6c757d; margin-top:6px; padding-top:6px; border-top:1px dashed #dee2e6;">
                <i class="bi bi-bar-chart-steps"></i>
                Kum. Ziel bis jetzt: <span style="font-weight:700; color:${zeitstrahlColor(kumPct)};">${zsVk.kum_ist_nw}</span> / ${zsVk.kum_ziel_nw} (${kumPct}%)
            </div>`;
    }
}
```

Dann `kumReminderHtml` in das NW-Box-HTML einsetzen nach der Zielerfüllung-Zeile.

- [ ] **Step 3: Jahresansicht Hero-Card auch bei Einzelverkäufer anzeigen**

In `renderZeitstrahlHeroCard()`, im `else if (currentPeriod === 'year' || currentPeriod === 'fiscal')` Block: Hier rendern wir die Hero-Card nicht separat, sondern die bestehende `loadZielauswertung()` zeigt sie bereits. Stattdessen sicherstellen dass `zeitstrahlHeroRow` auf `display:none` bleibt (Jahresansicht nutzt den bestehenden `#zielauswertungContainer`).

Keine Änderung nötig — der Block setzt bereits `heroRow.style.display = 'none'`.

- [ ] **Step 4: Inline-Balken in Jahres-VKL-Tabelle**

In `loadDetails()`, für die Jahresansicht (`currentPeriod === 'year' || currentPeriod === 'fiscal'`), zusätzliche Spalten rendern:

```javascript
// Jahresansicht: Ziel-Spalten hinzufügen wenn zeitstrahlData vorhanden
if ((currentPeriod === 'year' || currentPeriod === 'fiscal') && zeitstrahlData) {
    headerHtml += '<th style="min-width:160px;">NW Jahresziel</th><th style="min-width:160px;">GW Jahresziel</th>';
}

// Pro Verkäufer-Zeile (Jahresansicht):
if ((currentPeriod === 'year' || currentPeriod === 'fiscal') && zeitstrahlData) {
    const zsVk = zeitstrahlData.find(z => String(z.mitarbeiter_nr) === String(vk.verkaufer_nummer));
    if (zsVk) {
        const istNw = (vk.summe_neu || 0) + (vk.summe_test_vorfuehr || 0);
        const istGw = vk.summe_gebraucht || 0;
        const jzNw = zsVk.jahres_ziel_nw;
        const jzGw = zsVk.jahres_ziel_gw;
        const pctNw = jzNw > 0 ? Math.round((istNw / jzNw) * 100) : 0;
        const pctGw = jzGw > 0 ? Math.round((istGw / jzGw) * 100) : 0;
        const kumPct = zsVk.kum_ziel_nw > 0 ? Math.round((zsVk.kum_ist_nw / zsVk.kum_ziel_nw) * 100) : 0;
        const kumCheck = kumPct >= 100 ? ' <span style="color:#198754;">&#10003;</span>' : '';

        row += `<td>
            <div class="inline-progress">
                <div class="inline-progress-bar" style="width:${Math.min(pctNw,100)}%; background:${zeitstrahlColor(pctNw)};"></div>
                <div class="inline-progress-text">${istNw}/${jzNw} (${pctNw}%)</div>
            </div>
            <div class="inline-kum">kum. ${zsVk.kum_ist_nw}/${zsVk.kum_ziel_nw} (${kumPct}%)${kumCheck}</div>
        </td>`;
        row += `<td>
            <div class="inline-progress">
                <div class="inline-progress-bar" style="width:${Math.min(pctGw,100)}%; background:${zeitstrahlColor(pctGw)};"></div>
                <div class="inline-progress-text">${istGw}/${jzGw} (${pctGw}%)</div>
            </div>
        </td>`;
    } else {
        row += '<td>-</td><td>-</td>';
    }
}
```

- [ ] **Step 5: Detail-Tabelle Jahresansicht — Monats-Kum-Zeilen bei Einzelverkäufer**

In `loadZielauswertung()`, wenn `verkaufer` gesetzt, die Monats-Detail-Tabelle mit Monat- und Kum.-Zeile rendern (wie im Mockup). Nutze die Daten aus dem `monate`-Array der Jahresübersicht:

```javascript
// Nach der NW-Zielerfüllung-Box, Detail-Tabelle rendern:
if (verkaufer) {
    const monatLabels = ['Jan','Feb','Mär','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez'];
    let nwMonatRow = '<td class="fw-bold">Monat</td>';
    let nwKumRow = '<td class="fw-bold">Kum.</td>';
    let gwMonatRow = '<td class="fw-bold">Monat</td>';
    const aktM = new Date().getMonth() + 1;

    data.monate.forEach(m => {
        const isCurrent = m.monat === aktM && m.jahr === new Date().getFullYear();
        const cls = isCurrent ? 'current-month' : (m.ist_zukunft ? 'future' : '');
        const istNw = m.ist_zukunft ? '-' : m.ist_nw;
        const istGw = m.ist_zukunft ? '-' : m.ist_gw;
        const kumIst = m.ist_zukunft ? '-' : m.kum_ist_nw;
        const nwColor = m.ist_zukunft ? '' : `color:${zeitstrahlColor(m.ziel_nw > 0 ? Math.round(m.ist_nw/m.ziel_nw*100) : 0)}`;
        const kumColor = m.ist_zukunft ? '' : `color:${zeitstrahlColor(m.kum_ziel_nw > 0 ? Math.round(m.kum_ist_nw/m.kum_ziel_nw*100) : 0)}`;
        const gwColor = m.ist_zukunft ? '' : `color:${zeitstrahlColor(m.ziel_gw > 0 ? Math.round(m.ist_gw/m.ziel_gw*100) : 0)}`;

        nwMonatRow += `<td class="${cls}"><span style="${nwColor}">${istNw}</span>/${m.ziel_nw}</td>`;
        nwKumRow += `<td class="${cls}"><span style="${kumColor}">${kumIst}</span>/${m.kum_ziel_nw}</td>`;
        gwMonatRow += `<td class="${cls}"><span style="${gwColor}">${istGw}</span>/${m.ziel_gw}</td>`;
    });

    // Header
    let headerCells = data.monate.map(m => {
        const isCurrent = m.monat === aktM && m.jahr === new Date().getFullYear();
        return `<th class="${isCurrent ? 'current-month' : ''}">${monatLabels[m.monat-1]}</th>`;
    }).join('');

    // NW Tabelle mit Kum-Zeile
    nwDetailHtml = `
    <div class="mt-3">
        <table class="table table-sm table-bordered mb-0" style="font-size:0.7rem;">
            <thead><tr class="table-light"><th></th>${headerCells}</tr></thead>
            <tbody>
                <tr>${nwMonatRow}</tr>
                <tr style="border-top:2px solid #333; font-weight:600;">${nwKumRow}</tr>
            </tbody>
        </table>
    </div>`;

    // GW Tabelle ohne Kum-Zeile
    gwDetailHtml = `
    <div class="mt-3">
        <table class="table table-sm table-bordered mb-0" style="font-size:0.7rem;">
            <thead><tr class="table-light"><th></th>${headerCells}</tr></thead>
            <tbody><tr>${gwMonatRow}</tr></tbody>
        </table>
    </div>`;
}
```

- [ ] **Step 6: Browser-Test Jahresansicht**

1. Öffne http://drive:5002/verkauf/auftragseingang
2. Klicke "Dieses Jahr" + wähle einen Verkäufer
3. Prüfe: Hero-Card zeigt Jahresziel + kum. Reminder + Monatstabelle mit Kum.-Zeile
4. Wähle "Alle Verkäufer"
5. Prüfe: VKL-Tabelle zeigt NW/GW Jahresziel-Balken + kum. Reminder

- [ ] **Step 7: Commit**

```bash
git add templates/verkauf_auftragseingang.html
git commit -m "feat(verkauf): Zeitstrahl Jahresansicht — Kum.-Reminder + VKL-Inline-Balken"
```

---

### Task 4: Greiner-Test Service neustarten + Endtest

**Files:** Keine Code-Änderungen

- [ ] **Step 1: Service neustarten**

```bash
sudo -n /usr/bin/systemctl restart greiner-test
```

- [ ] **Step 2: Vollständiger Test**

1. **Monatsansicht** (als normaler Verkäufer / own_only):
   - Hero-Card mit persönlichem NW/GW-Fortschritt + Kum.-Reminder
   - Mini-Timeline Jahresverlauf
2. **Monatsansicht** (als VKL/GL):
   - Kein Hero-Card bei "Alle Verkäufer"
   - Inline-Balken in Tabelle: NW (Monat + kum.) + GW
   - Bei Einzelverkäufer-Filter: Hero-Card erscheint
3. **Jahresansicht** (als VKL):
   - Hero-Card mit Jahresziel + Kum.-Reminder + Detail-Tabelle
   - VKL-Tabelle mit NW/GW Jahresbalken + kum. Reminder
4. **Geschäftsjahr**: Gleiche Prüfungen wie Jahresansicht
5. **Ohne freigegebene Ziele**: Prüfen dass Zeitstrahl graceful mit 0-Werten umgeht

- [ ] **Step 3: Final-Commit (wenn nötig) + Workstream-CONTEXT.md aktualisieren**

```bash
# CONTEXT.md aktualisieren
git add docs/workstreams/verkauf/CONTEXT.md
git commit -m "docs(verkauf): CONTEXT.md um Zeitstrahl-Feature ergänzt"
```
