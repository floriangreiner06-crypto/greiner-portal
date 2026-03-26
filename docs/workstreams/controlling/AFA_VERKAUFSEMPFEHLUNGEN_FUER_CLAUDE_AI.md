# AfA-Modul Verkaufsempfehlungen – Dateien für claude.ai (ohne GitHub-Zugriff)

**Zweck:** Relevante neue/geänderte Dateien des AfA Verkaufsempfehlungen-Features zum Copy-Paste oder Hochladen für Fine-Tuning/Bugfix bei claude.ai. Repo ist privat, web_fetch kommt nicht rein.

---

## 1. Neue Python-Datei: API PDF

**Pfad:** `api/afa_verkaufsempfehlungen_pdf.py`

```python
"""
AfA Verkaufsempfehlungen — PDF-Report „20 älteste Fahrzeuge“.
Nutzt reportlab wie api/provision_pdf.py. Daten aus api.afa_api._get_verkaufsempfehlungen_liste (SSOT).
"""
from datetime import date
from io import BytesIO
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER


def _fmt_eur(value) -> str:
    """Geldbetrag: 23.399,84 €"""
    if value is None:
        return "–"
    try:
        return f"{float(value):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "–"


def generate_verkaufsempfehlungen_20_pdf() -> Optional[bytes]:
    """
    Erstellt PDF „20 älteste AfA-Fahrzeuge“ (Standzeit absteigend).
    Returns: PDF-Bytes oder None bei Fehler.
    """
    from api.afa_api import _get_verkaufsempfehlungen_liste

    liste = _get_verkaufsempfehlungen_liste()
    # Nach Standzeit absteigend (längste zuerst), None/0 am Ende
    sorted_list = sorted(
        liste,
        key=lambda f: (f.get('standzeit_tage') is None, -(f.get('standzeit_tage') or 0))
    )
    top20 = sorted_list[:20]

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'AfaReportTitle', parent=styles['Heading1'], fontSize=16, alignment=TA_LEFT, spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'AfaReportSubtitle', parent=styles['Normal'], fontSize=11, textColor=colors.grey, spaceAfter=12
    )
    normal_style = ParagraphStyle('AfaReportNormal', parent=styles['Normal'], fontSize=9, spaceAfter=6)

    elements.append(Paragraph("Greiner DRIVE — Verkaufsempfehlungen", title_style))
    elements.append(Paragraph(
        "VFW &amp; Mietwagen · 20 älteste Fahrzeuge nach Standzeit",
        subtitle_style
    ))
    elements.append(Paragraph(
        "<b>Rascher Umschlag und gezielte Vermarktung verbessern Ihren Liquiditätszugang und den Cashflow.</b> "
        "Jedes verkaufte Fahrzeug setzt Buchwert frei, reduziert Zinslast und schafft Spielraum für Neubeschaffung.",
        normal_style
    ))
    elements.append(Paragraph(
        "Die folgenden 20 ältesten Fahrzeuge (längste Standzeit) mit Empfehlung. "
        "Bitte priorisieren Sie die rot markierten Positionen — hier ist die Zinsenrückholung sonst gefährdet.",
        normal_style
    ))
    elements.append(Spacer(1, 0.5*cm))

    # Tabelle: #, Bezeichnung, Tage, Buchwert (€), Empfehlung
    table_data = [['#', 'Bezeichnung', 'Tage', 'Buchwert (€)', 'Empfehlung']]
    for i, f in enumerate(top20, 1):
        bezeichnung = (f.get('fahrzeug_bezeichnung') or '-')[:50]
        tage = f.get('standzeit_tage')
        tage_str = str(tage) if tage is not None else '–'
        buch = _fmt_eur(f.get('buchwert'))
        empfehlung = (f.get('empfehlung') or '-')[:60]
        table_data.append([str(i), bezeichnung, tage_str, buch, empfehlung])

    col_widths = [1.2*cm, 7*cm, 1.8*cm, 2.5*cm, 6*cm]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.8*cm))
    elements.append(Paragraph(
        f"Stand: {date.today().strftime('%d.%m.%Y')} · Quelle: DRIVE Portal AfA Verkaufsempfehlungen",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
    ))

    doc.build(elements)
    return buffer.getvalue()
```

---

## 2. E-Mail-Report-Script

**Pfad:** `scripts/send_afa_verkaufsempfehlungen_report.py`  
(Vollständiger Inhalt siehe Projekt – gleiche Logik wie oben: `get_report_data()` → `_get_verkaufsempfehlungen_liste()`, Top 20, `build_email_html()`, `generate_verkaufsempfehlungen_20_pdf()` als Anhang, `get_subscriber_emails('afa_verkaufsempfehlungen_report')`, GraphMailConnector.)

---

## 3. API-Route + Datenlogik (Auszug aus api/afa_api.py)

**Route:** `GET /api/afa/verkaufsempfehlungen`  
**Feature:** `afa_verkaufsempfehlungen` (nur GF/VKL).

Empfehlungstexte (Konstante + Funktion):

```python
STANDZEIT_ZWANG_VERMARKTUNG_TAGE = 300

def _empfehlung_texte(differenz, zinsen_monat, standzeit_tage=None):
    """differenz = VK netto − Buchwert; zinsen_monat = Zinsen/Monat."""
    if standzeit_tage is not None and standzeit_tage >= STANDZEIT_ZWANG_VERMARKTUNG_TAGE:
        return 'Zwang zur Vermarktung (Zinsenrückholung fraglich)'
    if differenz is None:
        return 'Verkaufspreis in Locosoft prüfen'
    if differenz >= 2000:
        return 'Aktiv vermarkten – Auktion prüfen'
    if differenz >= 0:
        return 'Absoluten Mindestpreis in mobile.de, jetzt verkaufen'
    if differenz >= -1000:
        return 'Prüfen: Verkauf oder halten'
    return 'Unter Buchwert – bewusste Entscheidung'
```

Kernfunktion für Liste (von Route + PDF + E-Mail-Report genutzt):

```python
def _get_verkaufsempfehlungen_liste():
    """Baut Liste aller aktiven AfA-Fahrzeuge mit Buchwert, Zinsen, Empfehlung. Returns list of dicts."""
    heute = date.today()
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, vin, kennzeichen, fahrzeug_bezeichnung, marke, modell,
                   fahrzeugart, betriebsnr, anschaffungskosten_netto, afa_monatlich,
                   nutzungsdauer_monate, anschaffungsdatum, tageszulassung
            FROM afa_anlagevermoegen
            WHERE status = 'aktiv'
            ORDER BY anschaffungsdatum ASC, betriebsnr, fahrzeugart, fahrzeug_bezeichnung
        """)
        rows = cur.fetchall()
        colnames = [c[0] for c in (cur.description or [])]
        liste = []
        vins = []
        for r in rows:
            row = row_to_dict(r, cur) if hasattr(r, 'keys') else dict(zip(colnames, r))
            # ... pro Zeile: berechne_restbuchwert(row, heute), standzeit_tage, f = {id, vin, kennzeichen, fahrzeug_bezeichnung, ..., buchwert, afa_bisher, standzeit_tage, ...}
            liste.append(f)
            if vin: vins.append(vin)
    # Außerhalb with: preise = _hole_locosoft_verkaufspreise_fuer_vins(vins), zinsen_map = _hole_zinsen_pro_vin(vins),
    # ez_map, brief_map, placements = _hole_eautoseller_bwa_placements_from_db(vins)
    # for f in liste: VK, differenz_vk_minus_buchwert, zinsen, brief, eAutoSeller-Felder, "Brief im Haus" 5% kalk., abverkaufspreis_vorschlag, f['empfehlung'] = _empfehlung_texte(...)
    return liste

@afa_api.route('/api/afa/verkaufsempfehlungen', methods=['GET'])
def verkaufsempfehlungen():
    if not current_user.is_authenticated or not current_user.can_access_feature('afa_verkaufsempfehlungen'):
        return jsonify({'ok': False, 'error': '...'}), 403
    liste = _get_verkaufsempfehlungen_liste()
    return jsonify({'ok': True, 'fahrzeuge': liste, 'eautoseller_bwa_status': ...})
```

(Die vollständige Implementierung von `_get_verkaufsempfehlungen_liste` mit allen Hilfsfunktionen steht in `api/afa_api.py` ab Zeile 727; sie nutzt `berechne_restbuchwert`, `row_to_dict`, `db_session`, `_hole_locosoft_verkaufspreise_fuer_vins`, `_hole_zinsen_pro_vin`, `_hole_erstzulassung_fuer_vins`, `_hole_brief_locosoft_fuer_vins`, `_hole_eautoseller_bwa_placements_from_db`.)

---

## 4. Routes (Seite Verkaufsempfehlungen)

**Pfad:** `routes/afa_routes.py`

```python
@afa_bp.route('/afa/verkaufsempfehlungen')
@login_required
def afa_verkaufsempfehlungen():
    if not current_user.can_access_feature('afa_verkaufsempfehlungen'):
        abort(403)
    return render_template(
        'controlling/afa_verkaufsempfehlungen.html',
        page_title='Verkaufsempfehlungen AfA',
        active_page='controlling',
    )
```

---

## 5. Template (vollständig)

**Pfad:** `templates/controlling/afa_verkaufsempfehlungen.html`

```html
{% extends "base.html" %}
{% block title %}Verkaufsempfehlungen AfA{% endblock %}
{% block extra_css %}
<style>
    .afa-table { font-size: 0.9rem; border-collapse: collapse; }
    .afa-table th { background: #343a40; color: #fff; padding: 0.5rem; white-space: nowrap; position: sticky; top: 0; z-index: 2; box-shadow: 0 1px 0 #495057; }
    .afa-table td { padding: 0.4rem 0.5rem; vertical-align: middle; }
    .afa-table tbody tr:hover { background: #f8f9fa; }
    .afa-table-wrap { max-height: min(75vh, 800px); overflow: auto; }
    .afa-table .col-bezeichnung { max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .empf-zwang { color: #b02a37; font-weight: 700; }
    .empf-aktiv { color: #198754; font-weight: 600; }
    .empf-sinnvoll { color: #0d6efd; }
    .empf-pruefen { color: #fd7e14; }
    .empf-unter-bw { color: #dc3545; }
</style>
{% endblock %}
{% block content %}
<div class="container-fluid py-3">
    <div class="d-flex justify-content-between align-items-center mb-3">
        <div>
            <h4 class="mb-0"><i class="bi bi-graph-up-arrow text-success"></i> Verkaufsempfehlungen AfA</h4>
            <small class="text-muted">VFW & Mietwagen — Ziele: positiver Cashflow, hoher Umschlag. Inkl. verursachte Zinsen (Einkaufsfinanzierung).</small>
        </div>
        <button type="button" class="btn btn-primary" id="btn-laden" title="Daten aktualisieren"><i class="bi bi-arrow-clockwise"></i> Aktualisieren</button>
    </div>
    <div class="card">
        <div class="card-body">
            <p class="text-muted small mb-3">Differenz = Verkaufspreis (netto) − Buchwert. Zinsen aus <strong>fahrzeugfinanzierungen</strong>. Bei „im Haus“ / „Brief im Haus“: <strong>5 % kalkulatorisch</strong>. <strong>Brief (Locosoft)</strong> = Zusatzcode BRIEF. <strong>mobile.de Platz</strong> und <strong>Treffer</strong> aus eAutoSeller Bewerter (BWA). <strong>Abverkauf</strong> = Buchwert + 50 % Zinsen (netto).</p>
            <div id="eautoseller-warnung" class="alert alert-warning small py-2 mb-2 d-none" role="alert"></div>
            <div class="table-responsive afa-table-wrap">
                <table class="table table-sm afa-table mb-0">
                    <thead>
                        <tr>
                            <th>VIN</th><th>Kz.</th><th>Bezeichnung</th><th>Standort</th><th>Art</th><th>Erstzul.</th><th>Einkauf</th>
                            <th class="text-end">Tage</th><th class="text-end">Einstand (€)</th><th class="text-end">Buchwert (€)</th><th class="text-end">AfA (€)</th><th class="text-end">VK netto (€)</th><th class="text-end">Diff. (€)</th><th class="text-end">Buchgewinn/Verlust (€)</th><th class="text-end">Z/M (€)</th><th class="text-end">Z ges. (€)</th><th>Brief</th><th class="text-end">mobile.de Platz</th><th class="text-end">Treffer</th><th class="text-end">Platz 1 (€)</th><th class="text-end">Abverkauf (€)</th><th>Empfehlung</th><th></th>
                        </tr>
                    </thead>
                    <tbody id="tbody">
                        <tr><td colspan="23" class="text-center text-muted py-4">Klick auf „Aktualisieren“ zum Laden.</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    <p class="small text-muted mt-2"><a href="{{ url_for('afa.afa_dashboard') }}"><i class="bi bi-arrow-left"></i> Zurück zum AfA-Dashboard</a></p>
</div>
<!-- Modal für Fahrzeugdetail (id vempf-detail-modal) mit vempf-detail-titel, vempf-detail-kpis, vempf-detail-chart, vempf-detail-buchgewinn, vempf-detail-buchungen, vempf-detail-link-afa -->
<script>
(function() {
    const API = '/api/afa';
    const tbody = document.getElementById('tbody');
    function fmtEuro(v) { if (v == null || v === '' || isNaN(v)) return '–'; return Number(v).toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
    function empfehlungClass(empf) {
        if (!empf) return '';
        if (empf.indexOf('Zwang zur Vermarktung') !== -1) return 'empf-zwang';
        if (empf.indexOf('Aktiv') !== -1) return 'empf-aktiv';
        if (empf.indexOf('Mindestpreis') !== -1 || empf.indexOf('jetzt verkaufen') !== -1) return 'empf-sinnvoll';
        if (empf.indexOf('Prüfen') !== -1) return 'empf-pruefen';
        if (empf.indexOf('Unter Buchwert') !== -1) return 'empf-unter-bw';
        return '';
    }
    document.getElementById('btn-laden').addEventListener('click', load);
    function load() {
        tbody.innerHTML = '<tr><td colspan="23" class="text-center py-3">Lade …</td></tr>';
        fetch(API + '/verkaufsempfehlungen').then(r => r.json()).then(function(data) {
            if (!data.ok) { tbody.innerHTML = '<tr><td colspan="23" class="text-danger">' + (data.error || 'Fehler') + '</td></tr>'; return; }
            var list = data.fahrzeuge || [];
            if (list.length === 0) { tbody.innerHTML = '<tr><td colspan="23" class="text-center text-muted py-3">Keine aktiven AfA-Fahrzeuge.</td></tr>'; return; }
            tbody.innerHTML = list.map(function(f) {
                var empf = (f && f.empfehlung) || '–';
                var empfCl = empfehlungClass(empf);
                return '<tr><td>' + (f.vin || '–') + '</td><td>' + (f.kennzeichen || '–') + '</td><td class="col-bezeichnung">' + (f.fahrzeug_bezeichnung || '–') + '</td><td>' + (f.standort || '–') + '</td><td>' + (f.art_kurz || '–') + '</td><td>' + (f.erstzulassungsdatum || '–') + '</td><td>' + (f.einkaufsdatum || '–') + '</td><td class="text-end">' + (f.standzeit_tage != null ? f.standzeit_tage : '–') + '</td><td class="text-end">' + fmtEuro(f.einstandspreis) + '</td><td class="text-end">' + fmtEuro(f.buchwert) + '</td><td class="text-end">' + fmtEuro(f.afa_bisher) + '</td><td class="text-end">' + fmtEuro(f.verkaufspreis_aktuell) + '</td><td class="text-end">' + fmtEuro(f.differenz_vk_minus_buchwert) + '</td><td class="text-end">' + fmtEuro(f.zinsen_monat) + '</td><td class="text-end">' + fmtEuro(f.zinsen_gesamt) + '</td><td>' + (f.brief_locosoft || '–') + '</td><td class="text-end">' + (f.mobile_platz != null ? f.mobile_platz : '–') + '</td><td class="text-end">' + (f.total_hits != null ? f.total_hits : '–') + '</td><td class="text-end">' + fmtEuro(f.platz_1_retail_gross) + '</td><td class="text-end">' + fmtEuro(f.abverkaufspreis_vorschlag) + '</td><td class="' + empfCl + '">' + empf + '</td><td><button type="button" class="btn btn-sm btn-outline-primary detail-btn" data-id="' + (f.id || '') + '">Detail</button></td></tr>';
            }).join('');
            tbody.querySelectorAll('.detail-btn').forEach(function(btn) {
                btn.addEventListener('click', function() { openDetail(parseInt(btn.getAttribute('data-id'), 10)); });
            });
        }).catch(function(e) { tbody.innerHTML = '<tr><td colspan="23" class="text-danger">' + (e.message || 'Fehler') + '</td></tr>'; });
    }
    function openDetail(id) { /* fetch(API + '/fahrzeug/' + id) → Modal mit KPIs, Chart, Buchungen */ }
    load();
})();
</script>
{% endblock %}
```
*(Im echten Template sind außerdem: vollständige Tabellen-Header, Buchgewinn/Verlust-Spalte, Detail-Modal mit Chart.js und Buchungstabelle, fmtDate. API: GET /api/afa/verkaufsempfehlungen → data.fahrzeuge; GET /api/afa/fahrzeug/<id> für Detail.)*

---

## 6. DB-Schema (Auszug)

**PostgreSQL DB:** `drive_portal`

### afa_anlagevermoegen

```sql
CREATE TABLE IF NOT EXISTS afa_anlagevermoegen (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(20),
    kennzeichen VARCHAR(15),
    fahrzeug_bezeichnung VARCHAR(100),
    marke VARCHAR(50),
    modell VARCHAR(50),
    fahrzeugart VARCHAR(20) NOT NULL,
    betriebsnr INTEGER DEFAULT 1,
    firma VARCHAR(50),
    anschaffungsdatum DATE NOT NULL,
    anschaffungskosten_netto NUMERIC(12,2) NOT NULL,
    nutzungsdauer_monate INTEGER DEFAULT 72,
    afa_methode VARCHAR(20) DEFAULT 'linear',
    afa_monatlich NUMERIC(10,2),
    status VARCHAR(20) DEFAULT 'aktiv',
    abgangsdatum DATE,
    abgangsgrund VARCHAR(50),
    verkaufspreis_netto NUMERIC(12,2),
    restbuchwert_abgang NUMERIC(12,2),
    buchgewinn_verlust NUMERIC(12,2),
    locosoft_fahrzeug_id INTEGER,
    finanzierung_id INTEGER,
    erstellt_am TIMESTAMP DEFAULT NOW(),
    erstellt_von VARCHAR(50),
    aktualisiert_am TIMESTAMP DEFAULT NOW(),
    notizen TEXT
);
-- Spalte tageszulassung kann in neueren Migrationen existieren (BOOLEAN).
```

### afa_buchungen

```sql
CREATE TABLE IF NOT EXISTS afa_buchungen (
    id SERIAL PRIMARY KEY,
    anlage_id INTEGER REFERENCES afa_anlagevermoegen(id),
    buchungsmonat DATE NOT NULL,
    afa_betrag NUMERIC(10,2) NOT NULL,
    restbuchwert NUMERIC(12,2) NOT NULL,
    kumuliert NUMERIC(12,2) NOT NULL,
    ist_anteilig BOOLEAN DEFAULT false,
    erstellt_am TIMESTAMP DEFAULT NOW()
);
```

### eautoseller_bwa_placement (Cache für BWA/mobile.de)

```sql
CREATE TABLE IF NOT EXISTS eautoseller_bwa_placement (
    vin VARCHAR(17) PRIMARY KEY,
    mobile_platz INTEGER,
    total_hits INTEGER,
    platz_1_retail_gross NUMERIC(12,2),
    mobile_url TEXT,
    error_message TEXT,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 7. Report-Verwaltung

- Report-ID: `afa_verkaufsempfehlungen_report`
- Registry: `reports/registry.py` (Eintrag mit name, description, script, schedule 20:15 Mo–Fr, icon, category controlling)
- Empfänger: Tabelle `report_subscriptions` (report_type = `afa_verkaufsempfehlungen_report`)
- Celery-Task: `email_afa_verkaufsempfehlungen_report` (ruft Script auf)

---

**Ende der Datei.** Du kannst dieses Markdown an claude.ai schicken oder die genannten Dateien aus dem Repo kopieren.
