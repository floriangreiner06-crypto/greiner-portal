# Provision Detail-Seite Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Provision Detail-Seite (`provision_detail.html`) visuell an das Dashboard-Design angleichen und funktional erweitern (Bearbeitungs-Modal mit Berechnungszeile, Einkäufer-Umzuweisung).

**Architecture:** Backend-Erweiterungen in `provision_api.py` (Position-Edit erweitern, neuer Reassign-Endpoint) + `provision_service.py` (Detail-Query erweitern, aktive Verkäufer laden). Frontend komplett neu als Dashboard-Style mit Accordion-Kategorien, KPI-Karten, Edit-Modal.

**Tech Stack:** Flask/Python (Backend), Jinja2 + Bootstrap 5.3 + Vanilla JS (Frontend), PostgreSQL

---

## File Structure

| Datei | Aktion | Verantwortung |
|-------|--------|---------------|
| `api/provision_service.py:667-675` | Modify | Detail-Query um Berechnungsfelder erweitern + neue Funktion `get_aktive_verkaeufer()` |
| `api/provision_api.py:298-338` | Modify | `/position/<id>/bearbeiten` erweitern (provisionssatz, bemessungsgrundlage) |
| `api/provision_api.py` (neu, nach Zeile 370) | Modify | Neuer Endpoint `/position/<id>/reassign-einkaeufer` |
| `api/provision_api.py:184-196` | Modify | Lauf-Detail-Response um aktive Verkäufer ergänzen |
| `templates/provision/provision_detail.html` | Rewrite | Komplettes Redesign (Dashboard-Style, Accordion, Modal) |

---

### Task 1: Backend — Detail-Query um Berechnungsfelder erweitern

**Files:**
- Modify: `api/provision_service.py:667-675`

Die aktuelle Query in `get_lauf_detail()` liefert `provision_final` aber NICHT `bemessungsgrundlage`, `provisionssatz`, `provision_berechnet`, `kosten_abzug`. Diese werden für das Bearbeitungs-Modal benötigt.

- [ ] **Step 1: Positions-Query erweitern**

In `api/provision_service.py`, Funktion `get_lauf_detail()`, die SELECT-Query (Zeile 667-674) um die fehlenden Felder erweitern:

```python
        cur.execute("""
            SELECT id, kategorie, vin, modell, fahrzeugart, kaeufer_name, einkaeufer_name,
                   rg_netto, deckungsbeitrag, bemessungsgrundlage, kosten_abzug,
                   provisionssatz, provision_berechnet, provision_final,
                   locosoft_rg_nr, rg_datum, einspruch_flag, einspruch_text
            FROM provision_positionen WHERE lauf_id = %s
            ORDER BY CASE kategorie
                WHEN 'I_neuwagen' THEN 1 WHEN 'II_testwagen' THEN 2
                WHEN 'III_gebrauchtwagen' THEN 3 WHEN 'IV_gw_bestand' THEN 4 ELSE 5 END,
                provision_final DESC NULLS LAST
        """, (lauf_id,))
```

Ergebnis: Jede Position enthält jetzt `bemessungsgrundlage`, `provisionssatz`, `provision_berechnet`, `kosten_abzug`.

- [ ] **Step 2: Neue Funktion `get_aktive_verkaeufer()` hinzufügen**

Am Ende von `api/provision_service.py` (nach `delete_vorlauf`), neue Funktion für das Einkäufer-Dropdown:

```python
def get_aktive_verkaeufer() -> List[Dict[str, Any]]:
    """Alle Verkäufer mit provision_aktiv=true für Einkäufer-Dropdown."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT locosoft_id,
                   TRIM(BOTH ' ' FROM COALESCE(TRIM(first_name), '') || ' ' || COALESCE(TRIM(last_name), '')) AS name
            FROM employees
            WHERE COALESCE(provision_aktiv, true) = true
              AND locosoft_id IS NOT NULL
            ORDER BY last_name, first_name
        """)
        return rows_to_list(cur.fetchall())
```

- [ ] **Step 3: Lauf-Detail-Response um Verkäufer-Liste ergänzen**

In `api/provision_api.py`, Endpoint `lauf_detail()` (Zeile 184-196), die aktiven Verkäufer mitliefern (nur für VKL/Admin):

```python
@provision_api.route('/lauf/<int:lauf_id>', methods=['GET'])
@login_required
def lauf_detail(lauf_id):
    """GET /api/provision/lauf/<id> – Lauf inkl. Positionen. Verkäufer nur eigener Lauf."""
    data = get_lauf_detail(lauf_id)
    if not data:
        return jsonify({'success': False, 'error': 'Lauf nicht gefunden'}), 404
    vkb = data['lauf'].get('verkaufer_id')
    my_vkb = _get_vkb_for_request()
    if not _may_see_all_verkaufer() and my_vkb != vkb:
        return jsonify({'success': False, 'error': 'Kein Zugriff'}), 403
    data['success'] = True
    if _may_see_all_verkaufer():
        from api.provision_service import get_aktive_verkaeufer
        data['aktive_verkaeufer'] = get_aktive_verkaeufer()
    return jsonify(data)
```

- [ ] **Step 4: Import ergänzen**

In `api/provision_api.py`, Zeile 8, Import erweitern:

```python
from api.provision_service import berechne_live_provision, create_vorlauf, delete_vorlauf, get_dashboard_daten, get_lauf_detail, get_aktive_verkaeufer
```

- [ ] **Step 5: Testen**

```bash
curl -s -b /tmp/cookies.txt 'http://localhost:5002/api/provision/lauf/1' | python3 -m json.tool | head -40
```

Prüfen: Positionen enthalten `bemessungsgrundlage`, `provisionssatz`, `provision_berechnet`. Response enthält `aktive_verkaeufer`.

- [ ] **Step 6: Commit**

```bash
git add api/provision_service.py api/provision_api.py
git commit -m "feat(provision): Detail-API um Berechnungsfelder und Verkäufer-Liste erweitern"
```

---

### Task 2: Backend — Position-Bearbeitung erweitern

**Files:**
- Modify: `api/provision_api.py:298-338`

Aktuell akzeptiert `/position/<id>/bearbeiten` nur `provision_final`. Erweitern um `provisionssatz` und `bemessungsgrundlage` als optionale Override-Felder.

- [ ] **Step 1: Endpoint erweitern**

Die Funktion `position_bearbeiten()` in `api/provision_api.py` (Zeile 298-338) komplett ersetzen:

```python
@provision_api.route('/position/<int:pos_id>/bearbeiten', methods=['POST'])
@login_required
def position_bearbeiten(pos_id):
    """
    POST /api/provision/position/<id>/bearbeiten
    Body: { "provision_final": 123.45, "provisionssatz": 0.009, "bemessungsgrundlage": 28500.0 }
    Alle Felder optional — nur übergebene Felder werden aktualisiert.
    Nur VKL/Admin. Nicht bei Status ENDLAUF.
    """
    if not _may_see_all_verkaufer():
        return jsonify({'success': False, 'error': 'Nur VKL/Admin dürfen Positionen bearbeiten.'}), 403

    data = request.get_json() or {}

    # Mindestens ein Feld muss übergeben werden
    editable_fields = ('provision_final', 'provisionssatz', 'bemessungsgrundlage')
    updates = {}
    for field in editable_fields:
        if field in data and data[field] is not None:
            try:
                updates[field] = float(data[field])
            except (TypeError, ValueError):
                return jsonify({'success': False, 'error': f'{field} muss eine Zahl sein.'}), 400

    if not updates:
        return jsonify({'success': False, 'error': 'Mindestens ein Feld (provision_final, provisionssatz, bemessungsgrundlage) ist erforderlich.'}), 400

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.lauf_id, l.status
            FROM provision_positionen p
            JOIN provision_laeufe l ON l.id = p.lauf_id
            WHERE p.id = %s
        """, (pos_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'Position nicht gefunden.'}), 404
        if (row['status'] or '').upper() == 'ENDLAUF':
            return jsonify({'success': False, 'error': 'Endlauf ist gesperrt – keine Änderungen möglich.'}), 403

        lauf_id = row['lauf_id']
        set_parts = [f"{k} = %s" for k in updates]
        vals = list(updates.values())
        cur.execute(f"UPDATE provision_positionen SET {', '.join(set_parts)} WHERE id = %s", vals + [pos_id])
        _recalc_lauf_sums(cur, lauf_id)
        conn.commit()

    return jsonify({'success': True, 'message': 'Position aktualisiert.'})
```

- [ ] **Step 2: Testen**

Manuell testen: Position bearbeiten mit provisionssatz + bemessungsgrundlage. Prüfen, dass sich nur die übergebenen Felder ändern.

- [ ] **Step 3: Commit**

```bash
git add api/provision_api.py
git commit -m "feat(provision): Position-Bearbeitung um Provisionssatz und Bemessungsgrundlage erweitern"
```

---

### Task 3: Backend — Neuer Endpoint: Einkäufer-Umzuweisung

**Files:**
- Modify: `api/provision_api.py` (neuer Endpoint nach Zeile 370)

Neuer Endpoint, der eine GW-aus-Bestand-Position einem anderen Einkäufer zuweist. Die Position wird aus dem aktuellen Lauf entfernt und in den Lauf des Ziel-Verkäufers für denselben Monat eingefügt.

- [ ] **Step 1: Neuen Endpoint anlegen**

Nach `position_loeschen()` (Zeile 370) in `api/provision_api.py` einfügen:

```python
@provision_api.route('/position/<int:pos_id>/reassign-einkaeufer', methods=['POST'])
@login_required
def position_reassign_einkaeufer(pos_id):
    """
    POST /api/provision/position/<id>/reassign-einkaeufer
    Body: { "neuer_einkaeufer_id": 2008 }
    Verschiebt eine GW-aus-Bestand-Position zu einem anderen Verkäufer.
    Nur VKL/Admin. Nicht bei ENDLAUF.
    Voraussetzung: Ziel-Verkäufer hat bereits einen Vorlauf für denselben Monat.
    """
    if not _may_see_all_verkaufer():
        return jsonify({'success': False, 'error': 'Nur VKL/Admin dürfen Einkäufer umzuweisen.'}), 403

    data = request.get_json() or {}
    neuer_einkaeufer_id = data.get('neuer_einkaeufer_id')
    if neuer_einkaeufer_id is None:
        return jsonify({'success': False, 'error': 'neuer_einkaeufer_id ist erforderlich.'}), 400
    try:
        neuer_einkaeufer_id = int(neuer_einkaeufer_id)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'neuer_einkaeufer_id muss eine Zahl sein.'}), 400

    with db_session() as conn:
        cur = conn.cursor()

        # 1. Position + aktueller Lauf laden
        cur.execute("""
            SELECT p.*, l.status, l.verkaufer_id, l.abrechnungsmonat
            FROM provision_positionen p
            JOIN provision_laeufe l ON l.id = p.lauf_id
            WHERE p.id = %s
        """, (pos_id,))
        pos = cur.fetchone()
        if not pos:
            return jsonify({'success': False, 'error': 'Position nicht gefunden.'}), 404
        if (pos['status'] or '').upper() == 'ENDLAUF':
            return jsonify({'success': False, 'error': 'Endlauf ist gesperrt – keine Änderungen möglich.'}), 403
        if pos['kategorie'] != 'IV_gw_bestand':
            return jsonify({'success': False, 'error': 'Einkäufer-Umzuweisung nur für Kategorie IV (GW aus Bestand).'}), 400

        alter_lauf_id = pos['lauf_id']
        monat = pos['abrechnungsmonat']

        # 2. Ziel-Lauf des neuen Einkäufers finden
        cur.execute("""
            SELECT id, status FROM provision_laeufe
            WHERE verkaufer_id = %s AND abrechnungsmonat = %s
        """, (neuer_einkaeufer_id, monat))
        ziel_lauf = cur.fetchone()
        if not ziel_lauf:
            return jsonify({
                'success': False,
                'error': f'Kein Vorlauf für Verkäufer {neuer_einkaeufer_id} im Monat {monat} vorhanden. Bitte erst einen Vorlauf erstellen.'
            }), 400
        if (ziel_lauf['status'] or '').upper() == 'ENDLAUF':
            return jsonify({'success': False, 'error': 'Der Ziel-Lauf ist bereits Endlauf (gesperrt).'}), 403

        ziel_lauf_id = ziel_lauf['id']

        # 3. Neuen Einkäufer-Namen ermitteln
        cur.execute("""
            SELECT TRIM(BOTH ' ' FROM COALESCE(TRIM(first_name), '') || ' ' || COALESCE(TRIM(last_name), '')) AS name
            FROM employees WHERE locosoft_id = %s
        """, (neuer_einkaeufer_id,))
        emp = cur.fetchone()
        neuer_name = (emp['name'] if emp else f'VKB {neuer_einkaeufer_id}').strip()

        # 4. Position verschieben: lauf_id ändern + einkaeufer_name aktualisieren
        cur.execute("""
            UPDATE provision_positionen
            SET lauf_id = %s, einkaeufer_name = %s
            WHERE id = %s
        """, (ziel_lauf_id, neuer_name, pos_id))

        # 5. Summen beider Läufe neu berechnen
        _recalc_lauf_sums(cur, alter_lauf_id)
        _recalc_lauf_sums(cur, ziel_lauf_id)
        conn.commit()

    return jsonify({
        'success': True,
        'neuer_lauf_id': ziel_lauf_id,
        'neuer_einkaeufer_name': neuer_name,
        'message': f'Position an {neuer_name} (Lauf {ziel_lauf_id}) übertragen.'
    })
```

- [ ] **Step 2: Commit**

```bash
git add api/provision_api.py
git commit -m "feat(provision): Endpoint für Einkäufer-Umzuweisung bei GW aus Bestand"
```

---

### Task 4: Frontend — Template komplett neu aufbauen (Dashboard-Style)

**Files:**
- Rewrite: `templates/provision/provision_detail.html`

Kompletter Neuaufbau des Templates im Dashboard-Design-Stil. Dieses Task enthält das gesamte Template als ein Stück, da alle Teile voneinander abhängen.

- [ ] **Step 1: Template komplett ersetzen**

`templates/provision/provision_detail.html` mit dem neuen Template ersetzen. Die Design-Prinzipien:

**Layout-Struktur:**
- Header mit Icon-Box (blau, `#2563eb`), Breadcrumb, Titel, Monatsanzeige
- KPI-Karten (4er-Grid) für Kat. I–IV Summen + Gesamt-Karte
- Accordion-Bereich für Kategorien (eingeklappt by default)
- Endlauf-Formular / Endlauf-Info (bedingt)
- Aktions-Buttons unten

**CSS-Klassen vom Dashboard übernommen:**
- `.prov-header` für den Header-Bereich
- `.kpi-card` + `.kpi-bar` für farbige KPI-Karten
- `.section-header` für Abschnitts-Überschriften
- Borderless Tables statt `table-bordered`

**Accordion-Kategorien:**
- Jede Kategorie ist ein Bootstrap-Accordion-Item
- Header: Kategorie-Name + Badge mit Fahrzeug-Anzahl + Summe rechts
- Body: Tabelle mit Positionen
- Alle standardmäßig eingeklappt (`collapsed`)

**Tabellen-Spalten pro Kategorie:**
- Kat. I/II/III: Modell | Käufer | Rg.Nr. | Bemessungsgrdl. | Provision | [Aktionen]
- Kat. IV: Modell | Käufer | Einkäufer | Rg.Nr. | Bemessungsgrdl. | Provision | [Aktionen]
- (Einkäufer-Spalte NUR bei Kat. IV)

**Bearbeitungs-Modal:**
- Fahrzeug-Info (Modell, Käufer, Rg.Nr.) oben als Read-Only
- Bemessungsgrundlage (editierbar)
- Provisionssatz in % (editierbar)
- Live-berechnete Provision (= Bemessungsgrdl. × Satz)
- Provision final (editierbar, Override)
- Bei Kat. IV: Einkäufer-Dropdown mit allen aktiven Verkäufern

**Kumuliert-Zeile:** Komplett entfernt.

```html
{% extends "base.html" %}
{% block title %}Provisionslauf – Greiner DRIVE{% endblock %}
{% block content %}
<style>
    /* ── Layout (Dashboard-Style) ── */
    .prov-detail-main { padding: 1.25rem 2rem; background: #f8fafc; min-height: calc(100vh - 60px); }

    /* Header */
    .prov-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem; }
    .prov-header .title-icon {
        width: 36px; height: 36px; border-radius: 10px; background: #2563eb;
        display: flex; align-items: center; justify-content: center; margin-right: .75rem; flex-shrink: 0;
    }
    .prov-header .title-icon i { color: #fff; font-size: 1rem; }
    .prov-header h2 { font-size: 1.4rem; font-weight: 700; color: #1e293b; margin: 0; }
    .prov-header .breadcrumb { font-size: .75rem; margin-bottom: .15rem; }
    .prov-header .breadcrumb a { color: #64748b; text-decoration: none; }
    .prov-header .breadcrumb a:hover { color: #2563eb; }
    .prov-header .subtitle { font-size: .82rem; color: #64748b; margin-top: .15rem; }
    .prov-status-badge {
        display: inline-block; padding: .25rem .75rem; border-radius: 6px; font-size: .75rem;
        font-weight: 600; text-transform: uppercase; letter-spacing: .5px;
    }
    .prov-status-badge.vorlauf { background: #fef3c7; color: #92400e; }
    .prov-status-badge.freigegeben { background: #dbeafe; color: #1e40af; }
    .prov-status-badge.endlauf { background: #d1fae5; color: #065f46; }

    /* KPIs */
    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: .75rem; margin-bottom: 1.5rem; }
    .kpi-card {
        border: 1px solid #e2e8f0; border-radius: 12px; background: #fff;
        overflow: hidden; position: relative; transition: box-shadow .15s;
    }
    .kpi-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,.07); }
    .kpi-card .kpi-bar { position: absolute; left: 0; top: 0; bottom: 0; width: 4px; border-radius: 12px 0 0 12px; }
    .kpi-card .card-body { padding: .9rem 1rem .9rem 1.25rem; }
    .kpi-icon { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: .85rem; }
    .kpi-label { font-size: .65rem; font-weight: 700; text-transform: uppercase; letter-spacing: .6px; color: #64748b; }
    .kpi-value { font-size: 1.3rem; font-weight: 700; line-height: 1.2; color: #1e293b; }
    .kpi-count { font-size: .72rem; color: #94a3b8; margin-top: .15rem; }

    /* Accordion */
    .prov-accordion .accordion-item { border: 1px solid #e2e8f0; border-radius: 10px !important; margin-bottom: .5rem; overflow: hidden; }
    .prov-accordion .accordion-button {
        background: #fff; font-weight: 600; font-size: .9rem; color: #1e293b;
        padding: .75rem 1rem; box-shadow: none !important;
    }
    .prov-accordion .accordion-button:not(.collapsed) { background: #f8fafc; color: #2563eb; }
    .prov-accordion .accordion-button::after { width: 1rem; height: 1rem; background-size: 1rem; }
    .prov-accordion .kat-badge { background: #e2e8f0; color: #475569; font-size: .7rem; padding: .15rem .5rem; border-radius: 4px; font-weight: 600; margin-left: .5rem; }
    .prov-accordion .kat-sum { margin-left: auto; font-size: .85rem; font-weight: 700; color: #1e293b; padding-right: .5rem; }

    /* Tabellen in Accordion */
    .prov-accordion table { margin-bottom: 0; font-size: .82rem; }
    .prov-accordion thead th { font-size: .7rem; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; color: #64748b; border-bottom: 2px solid #e2e8f0; padding: .5rem .75rem; }
    .prov-accordion tbody td { padding: .5rem .75rem; vertical-align: middle; border-bottom: 1px solid #f1f5f9; }
    .prov-accordion tbody tr:hover { background: #f8fafc; }

    /* Endlauf-Bereich */
    .endlauf-card { border: 1px solid #2563eb; border-radius: 12px; background: #fff; overflow: hidden; margin-bottom: 1rem; }
    .endlauf-card .card-header { background: #2563eb; color: #fff; font-weight: 700; padding: .6rem 1rem; font-size: .9rem; }
    .endlauf-card .card-body { padding: 1rem; }
    .endlauf-info {
        background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 12px; padding: 1rem 1.25rem;
        display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;
    }
    .endlauf-info .belegnr { font-size: 1.15rem; font-weight: 700; color: #1e40af; }

    /* Aktions-Buttons */
    .prov-actions { display: flex; gap: .5rem; align-items: center; flex-wrap: wrap; margin-top: 1rem; }
    .btn-navy { background: #1e3a5f; color: #fff; font-weight: 600; border: none; }
    .btn-navy:hover { background: #15304f; color: #fff; }

    /* Modal */
    .calc-row { display: flex; align-items: center; gap: .5rem; margin-bottom: .5rem; }
    .calc-row label { font-size: .78rem; font-weight: 600; color: #475569; min-width: 140px; }
    .calc-row .form-control { max-width: 160px; }
    .calc-divider { border-top: 2px solid #e2e8f0; margin: .5rem 0; }
    .calc-result { font-size: .85rem; color: #64748b; }
    .calc-result strong { color: #1e293b; }
</style>

<div class="prov-detail-main">
    <div id="loading" class="text-center py-5"><div class="spinner-border text-primary"></div><p class="text-muted mt-2">Lade Provisionslauf...</p></div>
    <div id="error" class="alert alert-danger" style="display: none;"></div>
    <div id="content" style="display: none;">

        <!-- Header -->
        <div class="prov-header">
            <div class="d-flex align-items-start">
                <div class="title-icon"><i class="bi bi-receipt"></i></div>
                <div>
                    <div class="breadcrumb mb-0"><a href="/provision/dashboard">Dashboard</a> <span class="mx-1 text-muted">/</span> <span class="text-muted">Lauf #<span id="laufId">{{ lauf_id }}</span></span></div>
                    <h2><span id="vName"></span></h2>
                    <div class="subtitle"><span id="vMonat"></span> &middot; <span id="vStatus" class="prov-status-badge"></span></div>
                </div>
            </div>
            <div class="d-flex gap-2 align-items-center">
                <a href="/provision/pdf/{{ lauf_id }}" download class="btn btn-sm btn-navy" id="btnPdfDownload" style="display:none;"><i class="bi bi-file-earmark-pdf"></i> PDF</a>
            </div>
        </div>

        <!-- KPI-Karten -->
        <div class="kpi-grid" id="kpiGrid">
            <div class="kpi-card"><div class="kpi-bar" style="background:#3b82f6;"></div><div class="card-body"><div class="d-flex justify-content-between align-items-start"><div><div class="kpi-label">I. Neuwagen</div><div class="kpi-value" id="kpiI">–</div><div class="kpi-count" id="kpiICount"></div></div><div class="kpi-icon" style="background:#eff6ff;color:#3b82f6;"><i class="bi bi-car-front"></i></div></div></div></div>
            <div class="kpi-card"><div class="kpi-bar" style="background:#8b5cf6;"></div><div class="card-body"><div class="d-flex justify-content-between align-items-start"><div><div class="kpi-label">II. Testwagen</div><div class="kpi-value" id="kpiII">–</div><div class="kpi-count" id="kpiIICount"></div></div><div class="kpi-icon" style="background:#f5f3ff;color:#8b5cf6;"><i class="bi bi-speedometer"></i></div></div></div></div>
            <div class="kpi-card"><div class="kpi-bar" style="background:#10b981;"></div><div class="card-body"><div class="d-flex justify-content-between align-items-start"><div><div class="kpi-label">III. Gebrauchtwagen</div><div class="kpi-value" id="kpiIII">–</div><div class="kpi-count" id="kpiIIICount"></div></div><div class="kpi-icon" style="background:#ecfdf5;color:#10b981;"><i class="bi bi-car-front-fill"></i></div></div></div></div>
            <div class="kpi-card"><div class="kpi-bar" style="background:#f59e0b;"></div><div class="card-body"><div class="d-flex justify-content-between align-items-start"><div><div class="kpi-label">IV. GW aus Bestand</div><div class="kpi-value" id="kpiIV">–</div><div class="kpi-count" id="kpiIVCount"></div></div><div class="kpi-icon" style="background:#fffbeb;color:#f59e0b;"><i class="bi bi-box-seam"></i></div></div></div></div>
            <div class="kpi-card"><div class="kpi-bar" style="background:#6366f1;"></div><div class="card-body"><div class="d-flex justify-content-between align-items-start"><div><div class="kpi-label">Ia. Stückprämie</div><div class="kpi-value" id="kpiStueck">–</div></div><div class="kpi-icon" style="background:#eef2ff;color:#6366f1;"><i class="bi bi-trophy"></i></div></div></div></div>
            <div class="kpi-card"><div class="kpi-bar" style="background:#1e293b;"></div><div class="card-body"><div class="d-flex justify-content-between align-items-start"><div><div class="kpi-label">Gesamt</div><div class="kpi-value" id="kpiGesamt">–</div></div><div class="kpi-icon" style="background:#f1f5f9;color:#1e293b;"><i class="bi bi-calculator"></i></div></div></div></div>
        </div>

        <!-- Accordion: Kategorien -->
        <div class="accordion prov-accordion" id="katAccordion"></div>

        <!-- Endlauf-Formular (nur bei FREIGEGEBEN + Berechtigung) -->
        <div id="endlaufBereich" style="display:none;" class="endlauf-card mt-3">
            <div class="card-header"><i class="bi bi-check-circle me-1"></i> Endlauf erstellen</div>
            <div class="card-body">
                <p class="text-muted small mb-2">Belegnummer-Vorschau: <strong id="belegnummerVorschau"></strong></p>
                <div class="row g-2 mb-2">
                    <div class="col-md-2"><label class="form-label small">Kat. I</label><input type="number" step="0.01" class="form-control form-control-sm" id="efSumI"></div>
                    <div class="col-md-2"><label class="form-label small">Kat. II</label><input type="number" step="0.01" class="form-control form-control-sm" id="efSumII"></div>
                    <div class="col-md-2"><label class="form-label small">Kat. III</label><input type="number" step="0.01" class="form-control form-control-sm" id="efSumIII"></div>
                    <div class="col-md-2"><label class="form-label small">Kat. IV</label><input type="number" step="0.01" class="form-control form-control-sm" id="efSumIV"></div>
                    <div class="col-md-2"><label class="form-label small">Kat. V</label><input type="number" step="0.01" class="form-control form-control-sm" id="efSumV"></div>
                    <div class="col-md-2"><label class="form-label small fw-bold">Gesamt</label><input type="number" step="0.01" class="form-control form-control-sm fw-bold" id="efSumGesamt"></div>
                </div>
                <button type="button" id="btnEndlauf" class="btn btn-primary btn-sm"><i class="bi bi-check-circle"></i> Endlauf erstellen</button>
            </div>
        </div>

        <!-- Endlauf-Info (nur bei ENDLAUF) -->
        <div id="endlaufInfo" style="display:none;" class="endlauf-info mt-3">
            <div>
                <span class="belegnr" id="endlaufBelegnummer"></span>
                <span class="ms-2 text-muted small" id="endlaufDatum"></span>
            </div>
            <a href="/provision/pdf/{{ lauf_id }}" download class="btn btn-sm btn-navy ms-auto" id="btnPdfEndlauf"><i class="bi bi-file-earmark-pdf"></i> PDF herunterladen</a>
        </div>

        <!-- Aktions-Buttons -->
        <div class="prov-actions">
            <a href="/provision/dashboard" class="btn btn-sm btn-outline-secondary"><i class="bi bi-arrow-left"></i> Dashboard</a>
            <button type="button" id="btnLoeschen" class="btn btn-sm btn-outline-danger" style="display:none;"><i class="bi bi-trash"></i> Vorlauf löschen</button>
        </div>
    </div>
</div>

<!-- Modal: Position bearbeiten -->
<div class="modal fade" id="editModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header py-2">
                <h5 class="modal-title"><i class="bi bi-pencil-square"></i> Position bearbeiten</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="mb-3 p-2 rounded" style="background:#f8fafc;">
                    <div class="small"><strong id="editModell">–</strong></div>
                    <div class="small text-muted">Käufer: <span id="editKaeufer">–</span> &middot; Rg.Nr.: <span id="editRgNr">–</span></div>
                    <div class="small text-muted">Kategorie: <span id="editKategorie">–</span></div>
                </div>
                <input type="hidden" id="editPosId">
                <input type="hidden" id="editKat">
                <div class="calc-row">
                    <label>Bemessungsgrdl. (€)</label>
                    <input type="number" step="0.01" class="form-control form-control-sm" id="editBemessung">
                </div>
                <div class="calc-row">
                    <label>Provisionssatz (%)</label>
                    <input type="number" step="0.001" class="form-control form-control-sm" id="editSatz">
                </div>
                <div class="calc-divider"></div>
                <div class="calc-result mb-2">Berechnet: <strong id="editBerechnet">–</strong></div>
                <div class="calc-row">
                    <label>Provision final (€)</label>
                    <input type="number" step="0.01" class="form-control form-control-sm" id="editFinal">
                </div>
                <!-- Einkäufer-Dropdown (nur Kat IV) -->
                <div id="editEinkaeuferWrap" style="display:none;" class="mt-3 pt-3" style="border-top:1px solid #e2e8f0;">
                    <div class="calc-row">
                        <label>Einkäufer</label>
                        <select class="form-select form-select-sm" id="editEinkaeufer" style="max-width:220px;"></select>
                    </div>
                    <div class="small text-muted mt-1"><i class="bi bi-info-circle"></i> Bei Änderung wird die Position zum neuen Einkäufer verschoben.</div>
                </div>
            </div>
            <div class="modal-footer py-2">
                <button type="button" class="btn btn-sm btn-outline-secondary" data-bs-dismiss="modal">Abbrechen</button>
                <button type="button" class="btn btn-sm btn-primary" id="editSave"><i class="bi bi-check-lg"></i> Speichern</button>
            </div>
        </div>
    </div>
</div>

<!-- Modal: Locosoft-Infos zur Rechnung -->
<div class="modal fade" id="provision-rechnung-modal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
            <div class="modal-header py-2">
                <h5 class="modal-title">Rechnung – Locosoft-Daten</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div id="provision-modal-loading" class="text-muted py-3">Lade…</div>
                <div id="provision-modal-content" style="display:none;">
                    <p class="mb-2"><strong>Kunde:</strong> <span id="provision-modal-kunde"></span> <span id="provision-modal-customer-nr" class="text-muted small"></span></p>
                    <p class="mb-3"><strong>Rechnung:</strong> <span id="provision-modal-rg-nr"></span> vom <span id="provision-modal-rg-datum"></span></p>
                    <p class="mb-3"><strong>Auftrag:</strong> <span id="provision-modal-auftrag">–</span></p>
                    <div id="provision-modal-rechnungen-wrap" class="mb-3" style="display:none;">
                        <h6 class="mb-2">Rechnungskopf (loco_invoices)</h6>
                        <div id="provision-modal-rechnungen"></div>
                    </div>
                    <h6 class="mb-2">FIBU-Buchungen</h6>
                    <div class="table-responsive">
                        <table class="table table-sm table-bordered mb-0">
                            <thead class="table-light"><tr><th>Konto</th><th>S/H</th><th class="text-end">Betrag</th><th>Beleg</th><th>Buchdat</th><th>Ausziff.</th><th>MA</th><th>Text</th></tr></thead>
                            <tbody id="provision-modal-buchungen"></tbody>
                        </table>
                    </div>
                </div>
                <div id="provision-modal-error" class="alert alert-danger py-2 mb-0" style="display:none;"></div>
            </div>
        </div>
    </div>
</div>

<!-- Modal: Auftragsdetails -->
<div class="modal fade" id="provision-auftrag-modal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
            <div class="modal-header py-2">
                <h5 class="modal-title">Auftrag – Details</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body" id="provision-auftrag-modal-body">
                <div class="text-center py-4"><div class="spinner-border text-primary"></div></div>
            </div>
        </div>
    </div>
</div>

<script>
(function(){
    var id = {{ lauf_id }};
    var pvUserCanEndlauf = {% if current_user.portal_role in ('admin', 'buchhaltung', 'personalbüro') %}true{% else %}false{% endif %};
    var pvUserCanPdf = {% if current_user.portal_role in ('admin', 'verkauf', 'verkauf_leitung', 'geschaeftsfuehrung', 'personalbüro', 'buchhaltung') %}true{% else %}false{% endif %};
    var pvUserCanEdit = {% if current_user.portal_role in ('admin', 'verkauf_leitung', 'geschaeftsfuehrung') %}true{% else %}false{% endif %};

    var L = document.getElementById('loading'), E = document.getElementById('error'), C = document.getElementById('content');
    var aktiveVerkaeufer = []; // Gefüllt aus API-Response

    function fmt(v) { return v != null && v !== '' ? Number(v).toLocaleString('de-DE', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '–'; }
    function fmtEuro(v) { return v != null && !isNaN(v) ? new Intl.NumberFormat('de-DE', {style:'currency', currency:'EUR'}).format(v) : '–'; }
    function escapeHtml(s) { return s == null ? '' : String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

    var katOrder = ['I_neuwagen','II_testwagen','III_gebrauchtwagen','IV_gw_bestand'];
    var katLabel = {'I_neuwagen':'I. Neuwagen','II_testwagen':'II. Testwagen / VFW','III_gebrauchtwagen':'III. Gebrauchtwagen','IV_gw_bestand':'IV. GW aus Bestand'};
    var katColor = {'I_neuwagen':'#3b82f6','II_testwagen':'#8b5cf6','III_gebrauchtwagen':'#10b981','IV_gw_bestand':'#f59e0b'};

    function buildAccordion(pos, lauf) {
        var byKat = {};
        pos.forEach(function(p){ var k = p.kategorie || ''; if(!byKat[k]) byKat[k] = []; byKat[k].push(p); });
        var acc = document.getElementById('katAccordion');
        acc.innerHTML = '';
        var statusUpper = (lauf.status || '').toUpperCase();
        var editable = statusUpper !== 'ENDLAUF' && pvUserCanEdit;

        katOrder.forEach(function(kat, idx){
            var rows = byKat[kat];
            if (!rows || rows.length === 0) return;
            var isGW = kat === 'IV_gw_bestand';
            var sumKey = {'I_neuwagen':'summe_kat_i','II_testwagen':'summe_kat_ii','III_gebrauchtwagen':'summe_kat_iii','IV_gw_bestand':'summe_kat_iv'}[kat];
            var sumVal = lauf[sumKey];

            var item = document.createElement('div');
            item.className = 'accordion-item';
            var headerId = 'heading_' + kat;
            var collapseId = 'collapse_' + kat;

            // Header
            item.innerHTML = ''
                + '<h2 class="accordion-header" id="' + headerId + '">'
                + '<button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#' + collapseId + '">'
                + '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:' + katColor[kat] + ';margin-right:.5rem;"></span>'
                + escapeHtml(katLabel[kat])
                + '<span class="kat-badge">' + rows.length + ' Fzg.</span>'
                + '<span class="kat-sum">' + fmt(sumVal) + ' €</span>'
                + '</button></h2>'
                + '<div id="' + collapseId + '" class="accordion-collapse collapse" data-bs-parent="#katAccordion">'
                + '<div class="accordion-body p-0"><div class="table-responsive">'
                + '<table class="table table-sm mb-0"><thead><tr>'
                + '<th>Modell</th><th>Käufer</th>'
                + (isGW ? '<th>Einkäufer</th>' : '')
                + '<th>Rg.Nr.</th><th class="text-end">Bemessungsgrdl.</th><th class="text-end">Provision</th>'
                + (editable ? '<th style="width:68px;">Aktionen</th>' : '')
                + '</tr></thead><tbody></tbody></table>'
                + '</div></div></div>';

            var tbody = item.querySelector('tbody');
            rows.forEach(function(p){
                var tr = document.createElement('tr');
                var rgHtml = (p.locosoft_rg_nr && p.rg_datum) ?
                    '<a href="#" class="provision-rg-link" data-invoice="'+escapeHtml(p.locosoft_rg_nr)+'" data-date="'+escapeHtml(p.rg_datum)+'">'+escapeHtml(p.locosoft_rg_nr)+'</a>' :
                    escapeHtml(p.locosoft_rg_nr || '–');
                var bemessung = p.bemessungsgrundlage != null ? fmt(p.bemessungsgrundlage) + ' €' : '–';
                var prov = p.provision_final != null ? fmt(p.provision_final) + ' €' : '–';
                var aktionen = editable ?
                    '<td class="text-nowrap"><button class="btn btn-sm btn-outline-primary pv-edit-btn" data-pos=\''+escapeHtml(JSON.stringify(p))+'\' title="Bearbeiten"><i class="bi bi-pencil"></i></button> <button class="btn btn-sm btn-outline-danger pv-del-btn" data-pos-id="'+p.id+'" title="Löschen"><i class="bi bi-trash"></i></button></td>' : '';

                tr.innerHTML = ''
                    + '<td>' + escapeHtml(p.modell || '–') + '</td>'
                    + '<td>' + escapeHtml(p.kaeufer_name || '–') + '</td>'
                    + (isGW ? '<td>' + escapeHtml(p.einkaeufer_name || '–') + '</td>' : '')
                    + '<td>' + rgHtml + '</td>'
                    + '<td class="text-end">' + bemessung + '</td>'
                    + '<td class="text-end">' + prov + '</td>'
                    + aktionen;
                tbody.appendChild(tr);
            });

            // Summenzeile
            var sumRow = document.createElement('tr');
            sumRow.style.background = '#f8fafc';
            sumRow.style.fontWeight = '700';
            var colCount = isGW ? (editable ? 6 : 5) : (editable ? 5 : 4);
            sumRow.innerHTML = '<td colspan="' + colCount + '" class="text-end">Summe</td><td class="text-end">' + fmt(sumVal) + ' €</td>' + (editable ? '<td></td>' : '');
            tbody.appendChild(sumRow);

            acc.appendChild(item);
        });

        // Event-Delegation: Rechnungs-Links
        acc.querySelectorAll('.provision-rg-link').forEach(function(a){
            a.addEventListener('click', function(ev){
                ev.preventDefault();
                openRechnungModal(this.getAttribute('data-invoice'), this.getAttribute('data-date'));
            });
        });

        // Event-Delegation: Edit + Delete
        if (editable) {
            acc.addEventListener('click', function(ev){
                var editBtn = ev.target.closest('.pv-edit-btn');
                if (editBtn) {
                    ev.preventDefault();
                    var posData = JSON.parse(editBtn.getAttribute('data-pos'));
                    openEditModal(posData);
                    return;
                }
                var delBtn = ev.target.closest('.pv-del-btn');
                if (delBtn) {
                    ev.preventDefault();
                    if (!confirm('Position wirklich löschen?')) return;
                    delBtn.disabled = true;
                    fetch('/api/provision/position/'+delBtn.getAttribute('data-pos-id')+'/loeschen', {method:'POST', credentials:'same-origin'})
                    .then(function(r){return r.json();})
                    .then(function(res){ if(res.success) window.location.reload(); else { alert(res.error||'Fehler'); delBtn.disabled=false; }});
                }
            });
        }
    }

    // ── Edit Modal ──
    function openEditModal(p) {
        document.getElementById('editPosId').value = p.id;
        document.getElementById('editKat').value = p.kategorie || '';
        document.getElementById('editModell').textContent = p.modell || '–';
        document.getElementById('editKaeufer').textContent = p.kaeufer_name || '–';
        document.getElementById('editRgNr').textContent = p.locosoft_rg_nr || '–';
        document.getElementById('editKategorie').textContent = katLabel[p.kategorie] || p.kategorie || '–';
        document.getElementById('editBemessung').value = p.bemessungsgrundlage != null ? Number(p.bemessungsgrundlage) : 0;
        document.getElementById('editSatz').value = p.provisionssatz != null ? Number((p.provisionssatz * 100).toFixed(4)) : 0;
        document.getElementById('editFinal').value = p.provision_final != null ? Number(p.provision_final) : 0;
        recalcModal();

        // Einkäufer-Dropdown nur bei Kat IV
        var einWrap = document.getElementById('editEinkaeuferWrap');
        if (p.kategorie === 'IV_gw_bestand') {
            einWrap.style.display = 'block';
            var sel = document.getElementById('editEinkaeufer');
            sel.innerHTML = '<option value="">— nicht ändern —</option>';
            aktiveVerkaeufer.forEach(function(vk){
                var opt = document.createElement('option');
                opt.value = vk.locosoft_id;
                opt.textContent = vk.name + ' (VKB ' + vk.locosoft_id + ')';
                sel.appendChild(opt);
            });
        } else {
            einWrap.style.display = 'none';
        }

        bootstrap.Modal.getOrCreateInstance(document.getElementById('editModal')).show();
    }

    function recalcModal() {
        var bem = parseFloat(document.getElementById('editBemessung').value) || 0;
        var satzPct = parseFloat(document.getElementById('editSatz').value) || 0;
        var berechnet = Math.round(bem * (satzPct / 100) * 100) / 100;
        document.getElementById('editBerechnet').textContent = fmt(berechnet) + ' €';
    }

    // Live-Recalc bei Eingabe
    document.getElementById('editBemessung').addEventListener('input', function(){
        recalcModal();
        document.getElementById('editFinal').value = (parseFloat(document.getElementById('editBemessung').value) || 0) * ((parseFloat(document.getElementById('editSatz').value) || 0) / 100);
        document.getElementById('editFinal').value = (Math.round(parseFloat(document.getElementById('editFinal').value) * 100) / 100).toFixed(2);
    });
    document.getElementById('editSatz').addEventListener('input', function(){
        recalcModal();
        document.getElementById('editFinal').value = (parseFloat(document.getElementById('editBemessung').value) || 0) * ((parseFloat(document.getElementById('editSatz').value) || 0) / 100);
        document.getElementById('editFinal').value = (Math.round(parseFloat(document.getElementById('editFinal').value) * 100) / 100).toFixed(2);
    });

    // Speichern
    document.getElementById('editSave').addEventListener('click', function(){
        var posId = document.getElementById('editPosId').value;
        var btn = this;
        btn.disabled = true;

        var satzPct = parseFloat(document.getElementById('editSatz').value);
        var body = {
            bemessungsgrundlage: parseFloat(document.getElementById('editBemessung').value),
            provisionssatz: !isNaN(satzPct) ? satzPct / 100 : undefined,
            provision_final: parseFloat(document.getElementById('editFinal').value)
        };

        // Erst Position bearbeiten
        fetch('/api/provision/position/'+posId+'/bearbeiten', {method:'POST', headers:{'Content-Type':'application/json'}, credentials:'same-origin', body: JSON.stringify(body)})
        .then(function(r){return r.json();})
        .then(function(res){
            if (!res.success) { alert(res.error||'Fehler'); btn.disabled=false; return Promise.reject('edit failed'); }

            // Dann ggf. Einkäufer umzuweisen
            var neuerEinkaeufer = document.getElementById('editEinkaeufer').value;
            if (neuerEinkaeufer && document.getElementById('editKat').value === 'IV_gw_bestand') {
                return fetch('/api/provision/position/'+posId+'/reassign-einkaeufer', {
                    method:'POST', headers:{'Content-Type':'application/json'}, credentials:'same-origin',
                    body: JSON.stringify({neuer_einkaeufer_id: parseInt(neuerEinkaeufer)})
                }).then(function(r){return r.json();});
            }
            return {success: true};
        })
        .then(function(res){
            if (res && !res.success) { alert(res.error||'Fehler beim Umzuweisen'); btn.disabled=false; return; }
            window.location.reload();
        })
        .catch(function(err){ if(err !== 'edit failed') { alert('Fehler: ' + err); btn.disabled=false; } });
    });

    // ── Rechnung-Modal (unveränderte Logik) ──
    function openRechnungModal(invoice, date) {
        if (!invoice || !date) return;
        var modalEl = document.getElementById('provision-rechnung-modal');
        var loadingEl = document.getElementById('provision-modal-loading');
        var contentEl = document.getElementById('provision-modal-content');
        var errorEl = document.getElementById('provision-modal-error');
        loadingEl.style.display = 'block'; contentEl.style.display = 'none'; errorEl.style.display = 'none';
        var params = new URLSearchParams({ invoice_number: invoice, invoice_date: date });
        fetch('/api/controlling/opos/rechnung-detail?' + params.toString(), { credentials: 'same-origin' })
            .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
            .then(function(data) {
                loadingEl.style.display = 'none';
                document.getElementById('provision-modal-kunde').textContent = data.kunde || '–';
                document.getElementById('provision-modal-customer-nr').textContent = data.customer_number != null ? '(Nr. ' + data.customer_number + ')' : '';
                document.getElementById('provision-modal-rg-nr').textContent = data.invoice_number || '–';
                document.getElementById('provision-modal-rg-datum').textContent = data.invoice_date || '–';
                document.getElementById('provision-modal-auftrag').textContent = '–';
                var wrap = document.getElementById('provision-modal-rechnungen-wrap');
                var div = document.getElementById('provision-modal-rechnungen');
                if (data.rechnungen && data.rechnungen.length > 0) {
                    var auftraege = data.rechnungen.map(function(inv){return inv.order_number;}).filter(function(v){return v!=null&&String(v).trim()!=='';}).map(function(v){return String(v).trim();});
                    if (auftraege.length > 0) {
                        var uniq = Array.from(new Set(auftraege));
                        document.getElementById('provision-modal-auftrag').innerHTML = uniq.map(function(nr){
                            return '<a href="#" class="provision-auftrag-link" data-auftrag="'+escapeHtml(nr)+'">'+escapeHtml(nr)+'</a>';
                        }).join(', ');
                    }
                    wrap.style.display = 'block';
                    div.innerHTML = data.rechnungen.map(function(inv){
                        var parts = ['Typ '+(inv.invoice_type||'–'),'Brutto '+fmtEuro(inv.total_gross),'Netto '+fmtEuro(inv.total_net)];
                        if(inv.order_number!=null) parts.push('Auftrag '+inv.order_number);
                        return '<p class="small mb-1">'+parts.join(' · ')+'</p>';
                    }).join('');
                } else { wrap.style.display = 'none'; }
                var tbody = document.getElementById('provision-modal-buchungen');
                tbody.innerHTML = (data.buchungen||[]).map(function(b){
                    return '<tr><td>'+(b.nominal_account_number||'')+'</td><td>'+(b.debit_or_credit||'')+'</td><td class="text-end">'+fmtEuro(b.betrag_eur)+'</td><td>'+(b.document_type||'')+' '+(b.document_number||'')+'</td><td>'+(b.document_date||b.accounting_date||'')+'</td><td>'+(b.clearing_number!=null&&b.clearing_number!==''&&b.clearing_number!==0?b.clearing_number:'OP')+'</td><td>'+(b.employee_number||'')+'</td><td class="small">'+escapeHtml(b.posting_text||'')+'</td></tr>';
                }).join('');
                contentEl.style.display = 'block';
                document.querySelectorAll('.provision-auftrag-link').forEach(function(a){
                    a.addEventListener('click', function(ev){ ev.preventDefault(); openAuftragModal(this.getAttribute('data-auftrag')); });
                });
                bootstrap.Modal.getOrCreateInstance(modalEl).show();
            })
            .catch(function(err) {
                loadingEl.style.display = 'none';
                errorEl.textContent = 'Fehler: '+(err.message||'Unbekannt'); errorEl.style.display = 'block';
                bootstrap.Modal.getOrCreateInstance(modalEl).show();
            });
    }
    function openAuftragModal(auftragNr) {
        if (!auftragNr) return;
        var modalEl = document.getElementById('provision-auftrag-modal');
        var bodyEl = document.getElementById('provision-auftrag-modal-body');
        bodyEl.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary"></div></div>';
        bootstrap.Modal.getOrCreateInstance(modalEl).show();
        fetch('/api/werkstatt/live/auftrag/'+encodeURIComponent(String(auftragNr)),{credentials:'same-origin'})
            .then(function(r){if(!r.ok) throw new Error('HTTP '+r.status); return r.json();})
            .then(function(data){
                if(!data.success||!data.auftrag){bodyEl.innerHTML='<div class="alert alert-danger mb-0">'+escapeHtml(data.error||'Auftrag nicht gefunden')+'</div>';return;}
                var a=data.auftrag||{},f=a.fahrzeug||{},s=a.summen||{};
                bodyEl.innerHTML='<div class="row g-3"><div class="col-md-6"><h6>Fahrzeug</h6><p class="mb-2"><strong>'+escapeHtml(f.kennzeichen||'-')+'</strong><br>'+escapeHtml((f.marke||'')+' '+(f.modell||''))+'</p><h6>Kunde</h6><p class="mb-0">'+escapeHtml(a.kunde||'-')+'</p></div><div class="col-md-6"><h6>Auftrag</h6><p class="mb-2">Nr.: <strong>'+escapeHtml(String(auftragNr))+'</strong><br>Datum: '+escapeHtml(a.datum||'-')+'<br>Serviceberater: '+escapeHtml(a.serviceberater||'-')+'</p><h6>AW-Summen</h6><p class="mb-0">Gesamt: '+escapeHtml(String(s.total_aw||0))+' AW<br>Fakturiert: '+escapeHtml(String(s.fakturiert_aw||0))+' AW<br>Offen: '+escapeHtml(String(s.offen_aw||0))+' AW</p></div></div>';
            })
            .catch(function(err){bodyEl.innerHTML='<div class="alert alert-danger mb-0">Fehler: '+escapeHtml(err.message||'Unbekannt')+'</div>';});
    }

    // ── Hauptlauf laden ──
    fetch('/api/provision/lauf/'+id,{credentials:'same-origin'}).then(function(r){return r.json();})
    .then(function(d){
        L.style.display='none';
        if(!d.success){ E.textContent=d.error||'Fehler'; E.style.display='block'; return; }
        C.style.display='block';
        var l = d.lauf;
        aktiveVerkaeufer = d.aktive_verkaeufer || [];

        // Header
        document.getElementById('vName').textContent = l.verkaufer_name || '–';
        document.getElementById('vMonat').textContent = l.abrechnungsmonat || '–';
        var statusEl = document.getElementById('vStatus');
        var statusUpper = (l.status||'').toUpperCase();
        statusEl.textContent = l.status || '–';
        statusEl.classList.add(statusUpper === 'VORLAUF' ? 'vorlauf' : statusUpper === 'FREIGEGEBEN' ? 'freigegeben' : statusUpper === 'ENDLAUF' ? 'endlauf' : '');

        // KPIs
        document.getElementById('kpiI').textContent = fmt(l.summe_kat_i) + ' €';
        document.getElementById('kpiII').textContent = fmt(l.summe_kat_ii) + ' €';
        document.getElementById('kpiIII').textContent = fmt(l.summe_kat_iii) + ' €';
        document.getElementById('kpiIV').textContent = fmt(l.summe_kat_iv) + ' €';
        document.getElementById('kpiStueck').textContent = fmt(l.summe_stueckpraemie) + ' €';
        document.getElementById('kpiGesamt').textContent = fmt(l.summe_gesamt) + ' €';

        // KPI Fahrzeug-Counts
        var pos = d.positionen || [];
        var counts = {};
        pos.forEach(function(p){ counts[p.kategorie] = (counts[p.kategorie]||0)+1; });
        if (counts['I_neuwagen']) document.getElementById('kpiICount').textContent = counts['I_neuwagen'] + ' Fahrzeuge';
        if (counts['II_testwagen']) document.getElementById('kpiIICount').textContent = counts['II_testwagen'] + ' Fahrzeuge';
        if (counts['III_gebrauchtwagen']) document.getElementById('kpiIIICount').textContent = counts['III_gebrauchtwagen'] + ' Fahrzeuge';
        if (counts['IV_gw_bestand']) document.getElementById('kpiIVCount').textContent = counts['IV_gw_bestand'] + ' Fahrzeuge';

        // Accordion
        buildAccordion(pos, l);

        // PDF-Button
        if (pvUserCanPdf && statusUpper !== 'ENDLAUF') {
            document.getElementById('btnPdfDownload').style.display = 'inline-block';
        }

        // Vorlauf löschen
        if (statusUpper === 'VORLAUF') {
            var btnDel = document.getElementById('btnLoeschen');
            btnDel.style.display = 'inline-block';
            btnDel.onclick = function(){
                if (!confirm('Vorlauf wirklich löschen?')) return;
                btnDel.disabled = true;
                fetch('/api/provision/vorlauf/'+id+'/loeschen',{method:'POST',credentials:'same-origin'}).then(function(r){return r.json();})
                .then(function(res){ if(res.success) window.location.href='/provision/dashboard'; else { alert(res.error||'Fehler'); btnDel.disabled=false; }});
            };
        }

        // Endlauf-Formular (FREIGEGEBEN + Berechtigung)
        if (statusUpper === 'FREIGEGEBEN' && pvUserCanEndlauf) {
            var ef = document.getElementById('endlaufBereich');
            ef.style.display = 'block';
            document.getElementById('belegnummerVorschau').textContent = 'VK' + (l.verkaufer_id||'') + '-' + (l.abrechnungsmonat||'');
            document.getElementById('efSumI').value = l.summe_kat_i || 0;
            document.getElementById('efSumII').value = l.summe_kat_ii || 0;
            document.getElementById('efSumIII').value = l.summe_kat_iii || 0;
            document.getElementById('efSumIV').value = l.summe_kat_iv || 0;
            document.getElementById('efSumV').value = l.summe_kat_v || 0;
            document.getElementById('efSumGesamt').value = l.summe_gesamt || 0;
            document.getElementById('btnEndlauf').onclick = function(){
                if (!confirm('Endlauf wirklich erstellen? Der Lauf wird danach gesperrt.')) return;
                this.disabled = true;
                var body = {
                    summe_gesamt: parseFloat(document.getElementById('efSumGesamt').value),
                    summe_kat_i: parseFloat(document.getElementById('efSumI').value),
                    summe_kat_ii: parseFloat(document.getElementById('efSumII').value),
                    summe_kat_iii: parseFloat(document.getElementById('efSumIII').value),
                    summe_kat_iv: parseFloat(document.getElementById('efSumIV').value),
                    summe_kat_v: parseFloat(document.getElementById('efSumV').value)
                };
                fetch('/api/provision/vorlauf/'+id+'/endlauf', {method:'POST', headers:{'Content-Type':'application/json'}, credentials:'same-origin', body:JSON.stringify(body)})
                .then(function(r){return r.json();})
                .then(function(res){
                    if(res.success){ alert('Endlauf erstellt: '+(res.belegnummer||'')); window.location.reload(); }
                    else { alert(res.error||'Fehler'); document.getElementById('btnEndlauf').disabled=false; }
                });
            };
        }

        // Endlauf-Info (ENDLAUF)
        if (statusUpper === 'ENDLAUF') {
            document.getElementById('endlaufInfo').style.display = 'flex';
            document.getElementById('endlaufBelegnummer').textContent = l.belegnummer || '–';
            document.getElementById('endlaufDatum').textContent = l.endlauf_am ? 'Abgerechnet am ' + new Date(l.endlauf_am).toLocaleDateString('de-DE') + (l.endlauf_von ? ' von ' + l.endlauf_von : '') : '';
            if (!pvUserCanPdf) document.getElementById('btnPdfEndlauf').style.display = 'none';
            document.getElementById('btnPdfDownload').style.display = 'none';
        }
    })
    .catch(function(err){ L.style.display='none'; E.textContent=err.message; E.style.display='block'; });
})();
</script>
{% endblock %}
```

- [ ] **Step 2: Visuell prüfen**

Im Browser öffnen: `http://drive:5002/provision/detail/<lauf_id>`

Prüfen:
- Header mit Icon, Breadcrumb, Status-Badge
- KPI-Karten zeigen korrekte Summen
- Keine "Kumuliert"-Zeile
- Kategorien sind eingeklappt (Accordion)
- Aufklappen zeigt Fahrzeuge mit Bemessungsgrundlage-Spalte
- Einkäufer-Spalte nur bei Kat. IV
- Edit-Button öffnet Modal mit Berechnungszeile
- Provisionssatz/Bemessungsgrundlage live-recalc im Modal
- Kat. IV: Einkäufer-Dropdown sichtbar

- [ ] **Step 3: Commit**

```bash
git add templates/provision/provision_detail.html
git commit -m "feat(provision): Detail-Seite komplett neu im Dashboard-Design (Accordion, KPIs, Edit-Modal)"
```

---

### Task 5: Restart und Abschlusstest

- [ ] **Step 1: Develop-Service neustarten**

```bash
sudo -n /usr/bin/systemctl restart greiner-test
```

- [ ] **Step 2: E2E-Test im Browser**

1. Dashboard öffnen → Lauf auswählen → Detail prüfen
2. Accordion aufklappen → Positionen prüfen
3. Bearbeiten-Modal: Provisionssatz ändern → Live-Recalc prüfen → Speichern
4. Bei Kat. IV: Einkäufer ändern → Fehlermeldung wenn kein Ziel-Vorlauf
5. PDF-Button testen

- [ ] **Step 3: Commit alles zusammen (falls Fixes nötig)**

```bash
git add -A && git commit -m "fix(provision): Detail-Seite Fixes nach E2E-Test"
```
