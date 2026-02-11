# Implementierungsplan: Profitabilitätsmodul (TAG 219+)

**Stand:** Nach Validierung des Feature-Auftrags  
**Phase 1:** Kernmodul (Locosoft)  
**Phase 2:** eAutoseller-Anreicherung (optional, nach API-Exploration)

---

## Übersicht

| Phase | Inhalt | Geschätzter Umfang |
|-------|--------|--------------------|
| 1.1 | Kalkulations-Helpers + Refactor fahrzeug_data | 0,5 Session |
| 1.2 | profitabilitaet_data + API + Route + Template | 1 Session |
| 1.3 | Dashboard-Feinschliff, Tests, Doku | 0,5 Session |
| 2 | eAutoseller-Exploration + ggf. Anreicherung | 1 Session (nach Exploration) |

---

## Phase 1.1: Kalkulations-Helpers und Refactor fahrzeug_data

### Schritt 1.1.1 – `api/kalkulation_helpers.py` anlegen

**Zweck:** SSOT für alle SQL-Fragmente der Fahrzeug-Kalkulation (EK, VK netto, variable Kosten, VKU, Besteuerung, DB1).

**Inhalt (Funktionen, die String zurückgeben):**

| Funktion | Rückgabe | Verwendung |
|----------|----------|------------|
| `sql_ek_netto(alias='dv')` | COALESCE(dv.calc_basic_charge,0)+... | EK = Einsatzwert netto |
| `sql_variable_kosten(alias='dv')` | COALESCE(dv.calc_cost_internal_invoices,0)+COALESCE(dv.calc_cost_other,0) | Variable Kosten |
| `sql_besteuerung_art(alias='dv')` | CASE WHEN dv.dealer_vehicle_type='D' THEN 'Diff25a' ... END | Besteuerungsart |
| `sql_vk_netto(alias='dv')` | CASE ... Regel: out_sale_price/1.19, Diff: Marge/1.19 ... END | VK netto |
| `sql_vku_subquery(alias='dv')` | (SELECT SUM(claimed_amount) FROM dealer_sales_aid ...) | VKU |
| `sql_db1(alias='dv', vku_nur_bei_verkauf=True)` | DB = VK_netto - EK - Var.Kosten + VKU | Kalk. DB1 |

**Konstanten im gleichen Modul (oder Import aus gewinnplanung):**

- `ZINSSATZ_JAHR = 0.05` (eine Quelle für Portal; in helpers oder gewinnplanung_v2_gw_data, dann importieren)

**Wichtig:**

- Parameter `alias` (Default `'dv'`) für Tabellen-Alias, damit Fragmente in verschiedenen Queries (dv, s, …) nutzbar sind.
- PostgreSQL-Syntax: `%s` nicht in den Fragment-Strings (werden per f-string/format eingebaut wo nötig); nur reine SQL-Teilstrings.

**Datei-Struktur (Vorschlag):**

```text
api/kalkulation_helpers.py
├── ZINSSATZ_JAHR = 0.05   # optional hier; sonst aus gewinnplanung_v2_gw_data importieren
├── sql_ek_netto(alias='dv')
├── sql_variable_kosten(alias='dv')
├── sql_besteuerung_art(alias='dv')
├── sql_vk_netto(alias='dv')
├── sql_vku_subquery(alias='dv')
├── sql_db1(alias='dv', vku_nur_bei_verkauf=True)
└── (optional) sql_standzeit_tage(alias='dv')  # CURRENT_DATE - COALESCE(dv.in_arrival_date, dv.created_date)
```

**Checkpoint:** Unit-Test oder manueller Test: Import der Modul-Funktionen; ein Fragment in einer minimalen Locosoft-Query ausführen und EK/VK/DB prüfen (ein Fahrzeug).

---

### Schritt 1.1.2 – `api/fahrzeug_data.py` refactoren

**Ziel:** GW-Bestand-Query nutzt ausschließlich `kalkulation_helpers`; Verhalten bleibt 1:1.

**Änderungen:**

1. Oben: `from api.kalkulation_helpers import sql_ek_netto, sql_variable_kosten, sql_besteuerung_art, sql_vk_netto, sql_vku_subquery, sql_db1` (oder wie die finalen Namen lauten).
2. In `get_gw_bestand()`: Die bisherigen inline SQL-Blöcke für EK, variable Kosten, VK netto, VKU, DB1, Besteuerung durch Aufrufe der Helper ersetzen, z. B.:
   - `sql_ek_netto('dv')` → EK-Spalte
   - `sql_variable_kosten('dv')` → kosten_variable
   - `sql_vku_subquery('dv')` → verkaufsunterstuetzung
   - `sql_vk_netto('dv')` → vk_preis
   - `sql_db1('dv', vku_nur_bei_verkauf=True)` → kalk_db
   - `sql_besteuerung_art('dv')` → besteuerung
3. Keine neuen WHERE/ORDER-Logiken; nur Ersetzen von Ausdrücken.

**Checkpoint:**

- GW-Dashboard `/verkauf/gw-bestand` aufrufen.
- Vorher/Nachher: gleiche Anzahl Fahrzeuge, gleiche Summen/DB-Werte (Stichprobe).

---

## Phase 1.2: Profitabilitäts-Data, API, Route, Template

### Schritt 1.2.1 – `api/profitabilitaet_data.py` anlegen

**Klasse:** `ProfitabilitaetData` (statische Methoden, wie FahrzeugData/VerkaufData).

**Konstanten (Kopf der Datei):**

```python
# Standkosten (konfigurierbar)
ZINSSATZ_JAHR = 0.05          # oder: from api.kalkulation_helpers import ZINSSATZ_JAHR
TAGESSATZ_PAUSCHAL = 12.00    # €/Tag

# Benchmark-Schwellen
BENCHMARK_STANDZEIT_GUT = 65
BENCHMARK_STANDZEIT_MAX = 90
BENCHMARK_DB_PCT_GUT = 10.0
BENCHMARK_DB_PCT_MIN = 5.0
BENCHMARK_DB_PRO_FZG_GUT = 1500
BENCHMARK_DB_PRO_FZG_MIN = 500
```

**Methoden:**

1. **`get_verkaufte_fahrzeuge_profitabilitaet(month, year, standort=None, fahrzeugtyp=None)`**
   - **Datenquelle:** Locosoft: `dealer_vehicles dv` + `vehicles v` + `models m` + `dealer_sales_aid` (via Helper) + optional `employees_history` für Verkäufername.
   - **Filter:**
     - `dv.out_invoice_date IS NOT NULL`
     - `EXTRACT(YEAR FROM dv.out_invoice_date) = year`, `EXTRACT(MONTH FROM dv.out_invoice_date) = month`
     - Standort: `build_locosoft_filter_verkauf(standort)` → String anpassen auf `dv.out_subsidiary` (replace wie in verkauf_data).
     - Optional: `dv.dealer_vehicle_type = fahrzeugtyp` wenn `fahrzeugtyp` gesetzt (z. B. 'G','N','D').
   - **Standzeit:** `standzeit_tage = (dv.out_invoice_date - COALESCE(dv.in_arrival_date, dv.created_date))` (in Tagen).
   - **Kalkulation:** EK, VK, variable Kosten, VKU, DB1 ausschließlich über `kalkulation_helpers` (gleiche Logik wie GW-Bestand; bei verkauften Fahrzeugen VKU immer einrechnen).
   - **Standkosten:**  
     - `standkosten_zins = ek_netto * ZINSSATZ_JAHR * (standzeit_tage / 365)`  
     - `standkosten_pauschal = standzeit_tage * TAGESSATZ_PAUSCHAL`  
     - `standkosten_gesamt = standkosten_zins + standkosten_pauschal`
   - **Netto-Profitabilität:**  
     - `db_nach_standkosten = db1 - standkosten_gesamt`  
     - `db_nach_standkosten_pct = (db_nach_standkosten / vk_brutto) * 100` (falls vk_brutto > 0).
   - **Benchmark-Felder:**  
     - standzeit_bewertung: 'gut' (<65), 'ok' (65–90), 'kritisch' (>90).  
     - db_pct_bewertung: 'gut' (>10%), 'ok' (5–10%), 'schwach' (<5%).
   - **Verkäufer:** `dv.out_salesman_number_1` + LEFT JOIN `employees_history` ON employee_number → name als `verkaufer_name`.
   - **Standortname:** `STANDORT_NAMEN.get(dv.out_subsidiary)` (aus standort_utils).
   - **Return:** Liste von Dicts pro Fahrzeug; einheitliche Keys (z. B. dealer_vehicle_number, vin, license_plate, modell, ez, dealer_vehicle_type, in_arrival_date, out_invoice_date, standzeit_tage, ek_netto, vk_brutto, vk_netto, variable_kosten, vku, db1, standkosten_zins, standkosten_pauschal, standkosten_gesamt, db_nach_standkosten, db_nach_standkosten_pct, standzeit_bewertung, db_pct_bewertung, salesman_number, verkaufer_name, in_subsidiary, standort_name).

2. **`get_profitabilitaet_summary(month, year, standort=None)`**
   - Ruft intern `get_verkaufte_fahrzeuge_profitabilitaet(month, year, standort)` auf (oder eine gemeinsame Query ohne Einzelzeilen-Overhead, je nach Performance).
   - Aggregationen:
     - Gesamt: anzahl_verkauft, summe_umsatz (Summe vk_brutto), summe_db1, summe_standkosten, summe_db_netto.
     - Durchschnitte: avg_db1_pro_fzg, avg_standzeit, avg_standkosten_pro_fzg, avg_db_netto_pro_fzg.
     - Nach Fahrzeugtyp (NW/GW/VFW): anzahl, avg_db, avg_standzeit, avg_db_netto.
     - Nach Marke (out_make_number → 27/40/41): anzahl, avg_db, avg_standzeit (Marken-Mapping aus standort_utils oder verkauf_data).
   - Benchmark-Score: Anteil Fahrzeuge mit DB > 0; Anteil Standzeit < 65 Tage.

3. **`get_verkaeufer_profitabilitaet(month, year, standort=None)`**
   - Gruppierung nach Verkäufer (out_salesman_number_1 + name).
   - Pro Verkäufer: name, anzahl_verkauft, summe_db1, avg_db_pro_fzg, summe_standkosten, summe_db_netto, avg_standzeit.
   - Sortierung: absteigend nach summe_db_netto.

4. **`get_profitabilitaet_trend(year, standort=None)`**
   - Für Monate 1–12: je Monat anzahl, summe_db1, avg_db_pro_fzg, avg_standzeit, summe_standkosten, summe_db_netto.
   - Geeignet für Chart.js (Labels = Monate, Datenseries = DB1, DB netto, Standzeit).

**Imports:**  
`api.db_utils.locosoft_session`, `api.standort_utils.build_locosoft_filter_verkauf`, `STANDORT_NAMEN`, `api.kalkulation_helpers` (alle benötigten sql_*-Funktionen und ggf. ZINSSATZ_JAHR), `logging`, `datetime`.

**Checkpoint:** Kurzes Skript oder Flask-Shell: `ProfitabilitaetData.get_verkaufte_fahrzeuge_profitabilitaet(2, 2026, standort=1)` aufrufen; prüfen ob Zeilen und Summen plausibel.

---

### Schritt 1.2.2 – `api/profitabilitaet_api.py` anlegen

**Blueprint:** `profitabilitaet_api`, `url_prefix='/api/profitabilitaet'`.

**Endpoints:**

| Methode | URL | Parameter | Aktion |
|---------|-----|-----------|--------|
| GET | `/api/profitabilitaet/fahrzeuge` | month, year, standort, typ (optional) | `ProfitabilitaetData.get_verkaufte_fahrzeuge_profitabilitaet` → JSON |
| GET | `/api/profitabilitaet/summary` | month, year, standort | `ProfitabilitaetData.get_profitabilitaet_summary` → JSON |
| GET | `/api/profitabilitaet/verkaeufer` | month, year, standort | `ProfitabilitaetData.get_verkaeufer_profitabilitaet` → JSON |
| GET | `/api/profitabilitaet/trend` | year, standort | `ProfitabilitaetData.get_profitabilitaet_trend` → JSON |
| GET | `/api/profitabilitaet/health` | - | Health-Check (z. B. 200 + {"status":"ok"} oder kurzer Data-Call) |

**Response-Format:** Wie verkauf_api: `{ "success": true, "data": ..., "meta": { "standort": ..., "month": ..., "year": ... } }`. Bei Fehler: `{ "success": false, "error": "..." }`, Status 500.

**Details:**

- Query-Parameter: month/year als int; standort als int (0 oder None = alle); typ optional (G/N/D).
- Decimal-Werte vor JSON-Response in float konvertieren (z. B. Liste von Dicts durchgehen und Decimals ersetzen).
- try/except um jeden Endpoint; bei Exception loggen und jsonify(error=...) mit 500.

**Checkpoint:** Mit Browser oder curl alle 5 Endpoints aufrufen; prüfen ob JSON und Werte stimmen.

---

### Schritt 1.2.3 – Route und Navigation

**`routes/verkauf_routes.py`:**

- Neue Route:
  - `@verkauf_bp.route('/profitabilitaet')`
  - `standort, konsolidiert = parse_standort_params(request)`
  - `return render_template('verkauf_profitabilitaet.html', now=datetime.now(), standort=standort, konsolidiert=konsolidiert)`

**`templates/base.html`:**

- Im Verkauf-Dropdown **nach** „GW-Standzeit“ (Zeile ~227) einen neuen Eintrag:
  - `<li><a class="dropdown-item" href="/verkauf/profitabilitaet"><i class="bi bi-currency-euro text-success"></i> Profitabilität</a></li>`

**`app.py`:**

- `from api.profitabilitaet_api import profitabilitaet_api`
- `app.register_blueprint(profitabilitaet_api)` (passend zu den anderen API-Blueprints, z. B. nach verkauf_api).

**Checkpoint:** `/verkauf/profitabilitaet` öffnen; Seite lädt ohne 500; Menüpunkt sichtbar.

---

### Schritt 1.2.4 – Template `templates/verkauf_profitabilitaet.html`

**Basis:** `{% extends "base.html" %}`, `{% block content %}`, Bootstrap 5, Chart.js (bereits in base).

**Layout:**

1. **Kopfzeile:** Titel „Profitabilität Verkauf“; Filter: Monat, Jahr, Standort (Selects); Button „Laden“ (oder automatisch beim ersten Load).
2. **Zeile 1 – KPI-Karten (4):**
   - Verkaufte Fz (Anzahl)
   - ∅ DB pro Fz (€ + optional Trend-Pfeil)
   - ∅ Standzeit (Tage + Ampel-Farbe)
   - ∅ DB nach Standkosten (€ + Ampel)
3. **Zeile 2 – Charts (2 Spalten):**
   - Links: Line-Chart (12 Monate) – DB1 vs. DB nach Standkosten; zweite Y-Achse oder zweites Chart: Standzeit (Daten aus `/api/profitabilitaet/trend`).
   - Rechts: Horizontal Bar-Chart – Verkäufer-Ranking nach DB netto (Daten aus `/api/profitabilitaet/verkaeufer`).
4. **Zeile 3 – Tabelle (Tabs: NW | GW | Gesamt):**
   - Spalten: Kom.Nr | Modell | Kennz. | Typ | Standzeit | EK | VK | DB1 | Standkosten | DB netto | DB% | Verkäufer
   - Daten aus `/api/profitabilitaet/fahrzeuge` mit Query-Param `typ` je Tab (N / G / leer für Gesamt).
   - Clientseitig sortierbar; Footer mit Summen/Durchschnitten.
   - Farbcodierung Zeilen: grün (DB>0, Standzeit<65), gelb (DB>0, 65–90), rot (DB<0 oder Standzeit>90).
5. **Zeile 4 – Benchmark-Box:**
   - Text/Balken: „Eure ∅ Standzeit: X Tage | Branche: 65 Tage“; „Eurer DB-Anteil: X% | Branche: >10%“.

**JavaScript:**

- Beim Laden und bei „Laden“: Parameter aus den Selects lesen; nacheinander fetch auf summary, fahrzeuge, verkaeufer, trend.
- Daten in Karten, Charts und Tabelle füllen; Decimals als Zahl formatieren (z. B. toFixed(2)); Datum/Zeitraum aus meta nutzen.

**Checkpoint:** Filter wechseln (Monat/Jahr/Standort); Karten, Charts und Tabelle aktualisieren sich; keine Konsolenfehler.

---

## Phase 1.3: Feinschliff, Tests, Doku

### Schritt 1.3.1 – Qualitätscheck

- [ ] Keine SQL-Duplikate: Kalkulation nur in `kalkulation_helpers` (+ Nutzung in fahrzeug_data + profitabilitaet_data).
- [ ] Standort: Nur `build_locosoft_filter_verkauf` aus standort_utils; Alias `dv` korrekt.
- [ ] PostgreSQL: %s, EXTRACT, COALESCE, true/false.
- [ ] Decimal → float für JSON.
- [ ] Logging: `logger = logging.getLogger(__name__)` in profitabilitaet_data und profitabilitaet_api.
- [ ] Docstrings: Alle öffentlichen Methoden und Helper-Funktionen.

### Schritt 1.3.2 – Manuelle Tests

- [ ] `/verkauf/profitabilitaet` mit Standort 1, 2, 3, „Alle“.
- [ ] Monat wechseln (Monat mit und ohne Verkäufe).
- [ ] Tabs NW/GW/Gesamt; Sortierung Tabelle.
- [ ] Health-Endpoint und ein Data-Endpoint unter Last (optional).

### Schritt 1.3.3 – Dokumentation

- [ ] In `CLAUDE.md` oder Modul-Tabelle: Eintrag zu Profitabilität (api/profitabilitaet_api.py, api/profitabilitaet_data.py, Route /verkauf/profitabilitaet).
- [ ] In dieser Datei oder in SESSION_WRAP_UP: Kurzbeschreibung des neuen Moduls und der neuen Dateien.

### Schritt 1.3.4 – Git

- Commit (lokal/Server): `feat: Profitabilitätsmodul Phase 1 (TAG 219)` mit Auflistung der geänderten/neu angelegten Dateien.

---

## Phase 2: eAutoseller (optional, nach Exploration)

### Schritt 2.1 – Exploration

- Skript `scripts/explore_eautoseller_profitabilitaet.py`:
  - Ruft für 3–5 Fahrzeuge (IDs/VINs) auf:
    - `GET /dms/vehicle/{id}/statistics`
    - `GET /dms/vehicles/prices/suggestions`
    - `GET /dms/publications/vehicles/publicated?statistics=true`
    - `GET /dms/vehicle/{id}/overview` (falls details 500 gibt)
  - Gibt Response-Struktur (Keys, Beispielwerte) aus.
- Doku: `docs/EAUTOSELLER_PROFITABILITAET_EXPLORATION.md` mit Ergebnissen und Empfehlung (welche Felder für Standkosten/Conversion/Preishistorie nutzbar).

### Schritt 2.2 – Anreicherung (nur wenn Exploration sinnvoll)

- `profitabilitaet_data`: optional VIN-basierter Abgleich mit eAutoseller (z. B. Aufrufe, Leads, Preishistorie); neue Spalten nur wenn API stabil und aussagekräftig.
- Template: optionale Spalten/Karten (z. B. „∅ Aufrufe pro Fz“, „Conversion“).
- Optional: Celery-Task + Tabelle `eautoseller_vehicle_stats` wie im Feature-Auftrag beschrieben.

---

## Abhängigkeiten (Reihenfolge)

```text
1. kalkulation_helpers.py (neu)
2. fahrzeug_data.py (Refactor auf helpers)
3. profitabilitaet_data.py (nutzt helpers + standort_utils)
4. profitabilitaet_api.py (nutzt profitabilitaet_data)
5. verkauf_routes.py + base.html + app.py
6. verkauf_profitabilitaet.html
7. Tests + Doku + Commit
```

---

## Kurzreferenz: Wichtige Dateien

| Was | Datei |
|-----|--------|
| Kalkulation SSOT | api/kalkulation_helpers.py |
| GW-Bestand (angepasst) | api/fahrzeug_data.py |
| Profitabilität SSOT | api/profitabilitaet_data.py |
| REST API | api/profitabilitaet_api.py |
| Seite | routes/verkauf_routes.py, templates/verkauf_profitabilitaet.html |
| Navigation | templates/base.html |
| Registrierung | app.py |
| Standort-Filter | api/standort_utils.build_locosoft_filter_verkauf |
| Verkäufer | dealer_vehicles.out_salesman_number_1 + employees_history |

Dieser Plan kann als Checkliste während der Implementierung abgearbeitet werden.
