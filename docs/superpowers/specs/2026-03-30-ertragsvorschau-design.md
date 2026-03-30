# Modul "Umsatz- und Ertragsvorschau" — Design-Dokument

**Datum:** 2026-03-30
**Autor:** Claude Code + Florian Greiner
**Status:** Genehmigt
**Workstream:** Controlling

## Motivation

Banken (Santander, Genobank) fragen regelmäßig nach wirtschaftlichem Ausblick:
Umsatzentwicklung, erwartetes Ergebnis, Eigenkapital, ergriffene Maßnahmen.
Bisher wird das manuell aus Locosoft-FIBU, Sales-Daten und Werkstatt-Orders zusammengetragen.
Dieses Modul automatisiert das als Live-Dashboard + PDF-Report.

## Entscheidungen

| Frage | Entscheidung |
|-------|-------------|
| Primärer Anwendungsfall | Beides: internes Dashboard + Bank-Report PDF |
| Datenquelle FIBU | Täglicher Sync aus Locosoft (Celery-Task, 20:15) |
| Bilanz/EK-Daten | PDF-Import aus Steuerberater-JA (RAW-Partner) |
| Validierung JA-Import | Keine Validierungs-UI, nur Zusammenfassung nach Import |
| Berechtigungen | Nur Geschäftsleitung + Admin |
| Granularität | Monatswerte (keine Tageswerte) |
| JA-Tabelle | Flach (~20 Kennzahlen pro GJ, keine Einzelpositionen) |
| Architektur | Modularer Aufbau mit zentralem Data-Layer (SSOT) |
| Prognose Phase 1 | Lineare Hochrechnung (Ø bisherige Monate × 12) |
| Prognose Phase 2 | Auf Basis Auftragsbestand (Locosoft Bestellungen) |

## Datenquellen

### 1. Locosoft FIBU (`journal_accountings`)
- GuV-Konten: `is_profit_loss_account = 'J'` aus `nominal_accounts`
- SKR51-Mapping:
  - 810000–819999: Werkstatt-Erlöse
  - 820000–829999: Teile-Erlöse
  - 830000–839999: Sonstige Erlöse
  - 840000–899999: Fahrzeug-Erlöse
  - 710000–719999: WE Werkstatt
  - 720000–729999: WE Teile
  - 730000–739999: WE Sonstige
  - 400000–449999: Personalaufwand
  - 450000–493999: Sonstiger betrieblicher Aufwand
  - 230000–242999: Zinsen (Aufwand + Erträge)
  - 200000–229999 + 243000–293999: Neutrales Ergebnis
- Ausschluss: `document_type = 'A'` (Jahresabschluss), Konten 294000–294999 und 494000–499999 (kalkulatorische Verrechnungen)
- Subsidiaries: 1 (DEG/Opel) + 2 (Landau) — konsolidiert
- `posted_value` ist in Cent (bigint), Division durch 100 für Euro

### 2. Portal Sales-Tabelle (`sales`)
- Bereits synchronisiert via `sync_sales` (stündlich)
- Auslieferungen: `out_invoice_date IS NOT NULL`
- Auftragseingang: `out_sales_contract_date`
- Auftragsbestand (Pipeline): `out_sales_contract_date IS NOT NULL AND out_invoice_date IS NULL`
- Felder: `rechnungsbetrag_netto`, `deckungsbeitrag`, `dealer_vehicle_type` (N/T/G), `make_number`

### 3. Locosoft Werkstatt (`orders` + `labours`)
- Live-Abfrage gegen Locosoft (kein Sync nötig für Auftrags-Counts)
- Aufträge: `COUNT(DISTINCT number || '-' || subsidiary)` aus `orders`
- Abgerechnete Aufträge: `has_closed_positions = true AND has_open_positions = false`
- Erlöse/Rohertrag: aus `fibu_guv_monatswerte` (FIBU-Sync), nicht aus orders

### 4. Fahrzeugfinanzierungen (`fahrzeugfinanzierungen`)
- Bereits im Portal, kein neuer Sync nötig
- Felder: `aktiv`, Standzeit (aus `vertragsbeginn`), Bank, Saldo, Zinsen

### 5. Locosoft EK-Konten (für laufende EK-Schätzung)
- Entnahmen: Konten 190000–193999 aus `journal_accountings`
- Werden im FIBU-Sync mit erfasst (eigener Bereich `entnahmen`)

### 6. Steuerberater-JA (PDF-Import)
- Pfad: `/mnt/buchhaltung/Buchhaltung/Jahresabschlussunterlagen/Abschluss {YYYY} {YYYY+1}/Abschlüsse RAW/Autohaus Greiner GmbH & Co. KG JA {YYYY+1} signiert.pdf`
- Format: RAW-Partner (stabil seit 2021, Text-PDF, kein Scan)
- Schlüsselseiten:
  - S. 9: Mehrjahresvergleich (Bilanz + GuV-Kennzahlen + Cashflow)
  - S. 10: Vermögenslage (Bilanz Aktiva/Passiva detailliert)
  - S. 13: Ertragslage (vollständige GuV)
  - S. 15: Kennzahlen (EK-Quote, Rentabilität)
- Parser-Library: `pdfplumber` (Tabellenextraktion aus Text-PDFs)

## Datenmodell

### Tabelle `fibu_guv_monatswerte`

```sql
CREATE TABLE fibu_guv_monatswerte (
    id SERIAL PRIMARY KEY,
    geschaeftsjahr VARCHAR(10) NOT NULL,  -- '2025/26'
    monat INT NOT NULL,                   -- 1-12 (Kalendermonat)
    bereich VARCHAR(50) NOT NULL,
    betrag_cent BIGINT NOT NULL DEFAULT 0,
    synced_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(geschaeftsjahr, monat, bereich)
);
```

Bereiche:
- `werkstatt_erloese`, `teile_erloese`, `sonst_erloese`, `fz_erloese`
- `we_werkstatt`, `we_teile`, `we_sonstige`
- `personal`, `sonst_aufwand`
- `zinsen_aufwand`, `zinsen_ertrag`
- `neutral_aufwand`, `neutral_ertrag`
- `entnahmen`

### Tabelle `jahresabschluss_daten`

```sql
CREATE TABLE jahresabschluss_daten (
    id SERIAL PRIMARY KEY,
    geschaeftsjahr VARCHAR(10) NOT NULL UNIQUE,  -- '2024/25'
    stichtag DATE NOT NULL,                       -- 2025-08-31
    -- Bilanz
    bilanzsumme NUMERIC(12,1),
    anlagevermoegen NUMERIC(12,1),
    umlaufvermoegen NUMERIC(12,1),
    eigenkapital NUMERIC(12,1),
    ek_quote NUMERIC(5,1),
    rueckstellungen NUMERIC(12,1),
    verbindlichkeiten NUMERIC(12,1),
    -- GuV
    umsatz NUMERIC(12,1),
    rohertrag_pct NUMERIC(5,1),
    personalaufwand NUMERIC(12,1),
    abschreibungen NUMERIC(12,1),
    investitionen NUMERIC(12,1),
    zinsergebnis NUMERIC(12,1),
    betriebsergebnis NUMERIC(12,1),
    finanzergebnis NUMERIC(12,1),
    neutrales_ergebnis NUMERIC(12,1),
    jahresergebnis NUMERIC(12,1),
    -- Cashflow
    cashflow_geschaeft NUMERIC(12,1),
    cashflow_invest NUMERIC(12,1),
    cashflow_finanz NUMERIC(12,1),
    finanzmittel_jahresende NUMERIC(12,1),
    -- Meta
    quelldatei TEXT,
    importiert_am TIMESTAMP DEFAULT NOW(),
    importiert_von TEXT
);
```

Alle NUMERIC(12,1)-Werte in TEUR (wie im PDF).

### Tabelle `ertragsvorschau_snapshots`

```sql
CREATE TABLE ertragsvorschau_snapshots (
    id SERIAL PRIMARY KEY,
    stichtag DATE NOT NULL,
    geschaeftsjahr VARCHAR(10) NOT NULL,
    daten_json JSONB NOT NULL,
    erstellt_am TIMESTAMP DEFAULT NOW()
);
```

## Dateistruktur

```
api/
  ertragsvorschau_data.py        -- SSOT: alle Berechnungen
  ertragsvorschau_api.py         -- REST-Endpunkte
  ertragsvorschau_pdf.py         -- Bank-Report PDF (Phase 2)
  jahresabschluss_import.py      -- JA-PDF-Parser

routes/
  ertragsvorschau_routes.py      -- Dashboard-Views + Admin

templates/controlling/
  ertragsvorschau_dashboard.html -- Dashboard UI

scripts/sync/
  sync_fibu_guv.py               -- Celery-Task: Locosoft GuV -> Portal

migrations/
  add_ertragsvorschau_tables.sql -- DDL für alle 3 Tabellen
```

## Data-Layer Funktionen (`ertragsvorschau_data.py`)

### `get_guv_daten(geschaeftsjahr: str) -> dict`
Monatliche GuV aus `fibu_guv_monatswerte`. Liefert:
- Pro Monat: Erlöse (WS/Teile/Fz/Sonst), WE, Rohertrag, Personal, sonst. Aufwand, EBIT, Zinsen, EBT
- Kumuliert (bisherige Monate)
- Vorjahresvergleich (gleicher Zeitraum)
- Rohertrag-Marge (%)

### `get_verkauf_daten(geschaeftsjahr: str) -> dict`
Aus `sales`-Tabelle. Liefert:
- Auslieferungen pro Monat (Stück, Umsatz netto, DB), aufgeteilt NW/GW
- Auftragseingang pro Monat (Stück, NW/GW)
- Auftragsbestand (offene Verträge)
- VJ-Vergleich (gleicher Zeitraum)

### `get_service_daten(geschaeftsjahr: str) -> dict`
Werkstatt + Teile. Liefert:
- Erlöse, WE, Rohertrag, Marge pro Monat (aus fibu_guv_monatswerte)
- Werkstattaufträge pro Monat (Live aus Locosoft orders)
- VJ-Vergleich

### `get_standzeiten_daten() -> dict`
Aus `fahrzeugfinanzierungen` + Locosoft `vehicles`. Liefert:
- Aktive Finanzierungen nach Bank (Anzahl, Saldo, Ø Standzeit)
- Standzeit-Verteilung (0-30, 31-60, 61-90, 91-180, 181-365, >365 Tage)
- Verkaufte Fahrzeuge: Ø Standzeit pro Monat (Trend letzte 6 Monate)

### `get_eigenkapital_entwicklung(geschaeftsjahr: str) -> dict`
Kombination JA-Import + laufende Daten. Liefert:
- EK laut letztem Jahresabschluss
- + laufendes Ergebnis (EBT aus fibu_guv_monatswerte)
- - Entnahmen (aus fibu_guv_monatswerte, Bereich `entnahmen`)
- = geschätztes aktuelles EK
- EK-Zeitreihe aus allen importierten JAs

### `get_prognose(geschaeftsjahr: str) -> dict`
Hochrechnung auf 12 Monate. Liefert:
- Phase 1: Linear (Ø bisherige Monate × 12) für Umsatz, EBIT, Fz-Stück
- Phase 2: Gewichtet (letzte 3 Monate stärker) + Auftragsbestand-basiert für Fz

### `get_mehrjahresvergleich() -> list[dict]`
Aus `jahresabschluss_daten`. Liefert:
- Alle GJs als Liste mit Bilanz- + GuV-Kennzahlen
- Sortiert nach Geschäftsjahr absteigend

### `get_gesamtbild(geschaeftsjahr: str) -> dict`
Orchestriert alle obigen Funktionen. Liefert ein dict mit allen Sektionen.
Wird genutzt von: Dashboard-API, PDF-Generator, E-Mail-Report.

## JA-PDF-Import (`jahresabschluss_import.py`)

### Funktionen

```python
import_jahresabschluss(dateipfad: str) -> dict
```
1. PDF öffnen mit `pdfplumber`
2. Mehrjahresvergleich-Tabelle (S. 9) extrahieren: Bilanz-Kennzahlen + GuV-Kennzahlen
3. Ertragslage-Tabelle (S. 13) extrahieren: Detaillierte GuV
4. Werte normalisieren (deutsches Zahlenformat: 1.234,5 → 1234.5)
5. UPSERT in `jahresabschluss_daten`
6. Return: Dict mit importierten Werten + Zusammenfassung

```python
import_alle_jahresabschluesse() -> list[dict]
```
Scannt `/mnt/buchhaltung/.../Abschlüsse RAW/` für alle vorhandenen GJs.
Importiert alle die noch nicht in der DB sind.

```python
get_verfuegbare_jahresabschluesse() -> list[dict]
```
Listet alle PDFs im Buchhaltungs-Pfad mit GJ und Import-Status.

### Admin-UI

Route: `/controlling/ertragsvorschau/admin`
- Liste aller verfügbaren JA-PDFs (importiert / nicht importiert)
- Button "Importieren" pro GJ
- Button "Alle importieren" für Ersteinrichtung
- Nach Import: Zusammenfassung der erkannten Werte

## Dashboard

### Route
`/controlling/ertragsvorschau` — Feature: `ertragsvorschau`, Rollen: `geschaeftsleitung`, `admin`

### Layout

**Header:** GJ-Dropdown + "Bank-Report PDF" Button (Phase 2)

**KPI-Leiste (5 Karten):**
| KPI | Quelle | Anzeige |
|-----|--------|---------|
| Umsatz kumuliert | GuV | TEUR + Δ VJ% |
| EBIT kumuliert | GuV | TEUR + Δ VJ |
| EK aktuell | EK-Entwicklung | TEUR + EK-Quote |
| Fz-Auslieferungen | Verkauf | Stück + Δ VJ% |
| Auftragsbestand | Verkauf | Stück (NW/GW) |

**Sektionen (collapsible):**

1. **GuV-Entwicklung** — Monatstabelle + Sparklines + kumuliert + VJ
2. **Fahrzeugverkauf** — Auslieferungen + Auftragseingang (Balkendiagramm NW/GW), DB-Trend
3. **Werkstatt & Teile** — Erlöse, Rohertrag, Marge, Aufträge, VJ-Vergleich
4. **Standzeiten & Finanzierung** — Bestand nach Bank, Verteilung, Volumen-Trend
5. **Eigenkapital** — Balkendiagramm (5 Jahre + aktuelle Schätzung)
6. **Mehrjahresvergleich** — Tabelle wie S. 9 im JA-PDF
7. **Prognose** — Hochrechnung Umsatz/EBIT/Stück

### Frontend-Stack
Bootstrap 5.3 + Chart.js (wie bestehende DRIVE-Dashboards). AJAX-Calls an `/api/ertragsvorschau/*`.

## Bank-Report PDF (Phase 2)

### Auslösung
Button im Dashboard-Header. Nutzt `get_gesamtbild()` (SSOT).

### Aufbau (7 Seiten, A4, ReportLab)
1. Deckblatt (Firma, Titel, GJ, Stichtag)
2. Executive Summary (KPI-Tabelle + regelbasierter Zusammenfassungstext)
3. GuV-Übersicht (Monatstabelle + Kumuliert + VJ + Hochrechnung)
4. Fahrzeugverkauf (Stück, Umsatz, DB, Auftragsbestand)
5. Aftersales (Werkstatt + Teile, Erlöse, Rohertrag, Aufträge)
6. Standzeiten & Finanzierung (nach Bank, Verteilung, Zinslast)
7. Eigenkapital & Mehrjahresvergleich

Fußzeile: "DRIVE Portal — Autohaus Greiner GmbH & Co. KG — Stichtag: {Datum}"

## Celery-Task

### `sync_fibu_guv`
- Schedule: Täglich 20:15 Mo–Fr (nach Locosoft-Mirror 19:00)
- Ablauf:
  1. Aktuelles + Vorjahres-GJ bestimmen
  2. Für jedes GJ: Query `journal_accountings` mit SKR51-Mapping
  3. Gruppierung nach Kalendermonat + Bereich
  4. UPSERT in `fibu_guv_monatswerte`
  5. Log: Anzahl aktualisierte Zeilen
- Fehlerbehandlung: Bei Locosoft-Verbindungsfehler → Retry nach 5 Min, max 3 Versuche

## Navigation

DB-Migration: `INSERT INTO navigation_items` unter Controlling-Menü:
- "Ertragsvorschau" → `/controlling/ertragsvorschau`
- Feature: `ertragsvorschau`, Rollen: `geschaeftsleitung`, `admin`

## Phasenplan

### Phase 1 (MVP)
- DB-Tabellen + Migration (3 Tabellen + Navigation)
- `sync_fibu_guv` Celery-Task
- `ertragsvorschau_data.py` (alle get_*-Funktionen)
- `ertragsvorschau_api.py` (REST-Endpunkte)
- Dashboard mit allen 7 Sektionen
- Lineare Hochrechnung
- JA-PDF-Import (Parser + Admin-UI)
- Historischer Import aller vorhandenen JAs (2021–2025)

### Phase 2
- Bank-Report PDF (`ertragsvorschau_pdf.py`)
- Automatischer Executive-Summary-Text (regelbasiert)
- Prognose auf Basis Auftragsbestand (Locosoft Bestellungen)
- Monatlicher Snapshot (Celery-Task)
- E-Mail-Report (optional)

### Phase 3 (Nice-to-have)
- Szenario-Rechner ("Was wenn Marge um 1% steigt?")
- Budget/Plan-Vergleich (IST vs. SOLL)
- Abweichungsanalyse DRIVE-GuV vs. Steuerberater-JA

## Geschäftsjahr-Logik

- GJ beginnt September, endet August
- GJ-Bezeichnung: Startjahr/Endjahr (z.B. "2025/26" = Sep 2025 – Aug 2026)
- Bestimmung: Monat >= 9 → aktuelles Jahr ist Startjahr; Monat <= 8 → Vorjahr ist Startjahr
- Im Sync: Kalendermonat wird gespeichert, GJ-Zuordnung erfolgt über die Logik

## Abhängigkeiten

- `pdfplumber` (Python-Paket, muss installiert werden)
- Bestehend: `api/db_connection.py`, `api/db_utils.py` (DB-Zugriff)
- Bestehend: `sync_sales` (Fahrzeugdaten)
- Bestehend: `fahrzeugfinanzierungen` (Standzeiten)
- SMB-Mount: `/mnt/buchhaltung/` (für JA-PDF-Zugriff)
- Locosoft-DB: `10.80.80.8:5432` (für FIBU-Sync + Werkstatt-Aufträge)
