# Zinsfreiheit Stellantis / Hyundai – aktuelle Ermittlung

**Stand:** 2026-02  
**Tabelle:** `fahrzeugfinanzierungen` (Spalten `zinsfreiheit_tage`, `zins_startdatum`, `vertragsbeginn`, `alter_tage`)

---

## Stellantis

**Quelle:** Excel-Export aus dem Stellantis-Portal (ZIP mit Excel pro RRDI), Sheet **„Vertragsbestand“**, Zeilen ab Zeile 7, Spalten 3–15.

| Was | Wie ermittelt |
|-----|----------------|
| **Beginn der Zinsfreiheit** | **Vertragsbeginn** – kommt aus der Excel-Spalte **Vertragsbeginn** (Spalte 7 nach Umbenennung), wird als `vertragsbeginn` in der DB gespeichert. Die Zinsfreiheit beginnt mit dem Vertragsbeginn. |
| **Dauer der Zinsfreiheit** | **Aus der Excel-Spalte „Zinsfreiheit (Tage)“** – Spalte 6 wird als `zinsfreiheit_tage` eingelesen und in `fahrzeugfinanzierungen.zinsfreiheit_tage` gespeichert. Stellantis liefert die Laufzeit der Zinsfreiheit in Tagen also direkt. |
| **Ende Zinsfreiheit / Zinsbeginn** | Wird nicht explizit als Datum gespeichert. Nach Ablauf der Zinsfreiheit setzt der Import: `zins_startdatum = CURRENT_DATE - (alter_tage - zinsfreiheit_tage)` (nur wenn `alter_tage > zinsfreiheit_tage`). Damit ist der Zinsbeginn rechnerisch: Vertragsbeginn + `zinsfreiheit_tage` Tage. |

**Import-Script:** `scripts/imports/import_stellantis.py`  
- Liest aus Excel: `zinsfreiheit_tage`, `vertragsbeginn`, `alter_tage`, …  
- Nach dem Import: Zinsen (9,03 % p.a.) und `zins_startdatum` werden nur für Fahrzeuge mit `alter_tage > zinsfreiheit_tage` berechnet/gesetzt.

---

## Hyundai Finance

**Quelle:** CSV-Export (z. B. `stockList_*.csv` aus `/mnt/buchhaltung/.../HyundaiFinance`), Spalten u. a. „Zinsbeginn“, „Finanzierungsbeginn“, „Finanzierungsende“.

| Was | Wie ermittelt |
|-----|----------------|
| **Beginn der Zinsfreiheit** | **Finanzierungsbeginn** (Vertragsbeginn) – aus CSV-Spalte **„Finanzierungsbeginn“** → `vertragsbeginn`. Die Zinsfreiheit läuft vom Vertragsbeginn bis zum Zinsbeginn. |
| **Ende Zinsfreiheit / Zinsbeginn** | **Direkt aus der CSV-Spalte „Zinsbeginn“** – wird als `zins_startdatum` in der DB gespeichert. |
| **Dauer der Zinsfreiheit (Tage)** | Im **Hyundai-Finance-Import** (`import_hyundai_finance.py`) **nicht** berechnet und **nicht** in `zinsfreiheit_tage` geschrieben. Sie wäre ableitbar als `(zins_startdatum - vertragsbeginn).days`. Da `zinsfreiheit_tage` für Hyundai oft NULL bleibt, nutzen Warnungen/Views, die auf `zinsfreiheit_tage` filtern (z. B. „&lt; 30 Tage übrig“), diese Kennzahl für Hyundai ggf. nicht. |

**Import-Scripts:**  
- `scripts/imports/import_hyundai_finance.py` – setzt `zins_startdatum`, `vertragsbeginn`, `alter_tage`, Zinsen; **kein** `zinsfreiheit_tage`.  
- `scripts/imports/import_hyundai_data.py` (andere Quelle/Struktur) – berechnet `zinsfreiheit_tage = (zinsbeginn - finanz_beginn).days` und schreibt sie in die DB (SQLite-Syntax; bei Nutzung dieser Quelle und Migration auf PostgreSQL müsste die Spalte dort ebenfalls befüllt werden).

---

## Santander

**Quelle:** CSV-Export der Bank (Santander), Spalten u. a. **„Zins Startdatum“**, **„Zinsen Gesamt“**, **„Zinsen letzte Periode“**.

| Was | Wie ermittelt |
|-----|----------------|
| **Zinsbeginn** | **Aus der CSV-Spalte „Zins Startdatum“** → `zins_startdatum`. Keine eigene Berechnung. |
| **Zinsen gesamt / letzte Periode** | **Direkt aus der CSV** („Zinsen Gesamt“, „Zinsen letzte Periode“) → `zinsen_gesamt`, `zinsen_letzte_periode`. Die Kostenberechnung ist damit die der Bank – wir rechnen nicht nach. |
| **Zinsfreiheit (Tage)** | In der Santander-CSV **nicht** enthalten → `zinsfreiheit_tage` bleibt NULL. |

**Import-Scripts:** `scripts/imports/import_santander.py`, `import_santander_bestand.py` – lesen Zinsdaten aus der Bank-CSV, keine eigene Zinsformel.

---

## Kurzüberblick

| Institut | Beginn Zinsfreiheit | Dauer Zinsfreiheit | Ende Zinsfreiheit / Zinsbeginn | Zinskosten |
|----------|----------------------|--------------------|---------------------------------|------------|
| **Stellantis** | Vertragsbeginn (Excel) | **zinsfreiheit_tage** (Excel) | berechnet: Vertragsbeginn + zinsfreiheit_tage | **berechnet:** Saldo × 9,03 % p.a. × (alter_tage − zinsfreiheit_tage) / 365 (nur wenn alter_tage > zinsfreiheit_tage) |
| **Santander** | – | nicht in CSV (zinsfreiheit_tage = NULL) | **Zins Startdatum** (CSV) | **aus CSV:** „Zinsen Gesamt“, „Zinsen letzte Periode“ (Bank-Angaben) |
| **Hyundai Finance** | Finanzierungsbeginn (CSV) | nicht in DB gespeichert | **Zinsbeginn** (CSV) → zins_startdatum | berechnet mit 4,68 % p.a. ab Zinsbeginn |

---

## Relevante Spalten in `fahrzeugfinanzierungen`

- **zinsfreiheit_tage** – Anzahl Tage Zinsfreiheit ab Vertragsbeginn (Stellantis: aus Excel; Hyundai Finance: aktuell oft NULL).
- **zins_startdatum** – Datum, ab dem Zinsen laufen (Stellantis: berechnet; Hyundai: aus CSV „Zinsbeginn“).
- **vertragsbeginn** – Vertrags-/Finanzierungsbeginn = Start der Zinsfreiheit.

Warnungen wie „Zinsfreiheit läuft bald ab“ basieren auf `zinsfreiheit_tage` und `alter_tage` (z. B. `alter_tage > zinsfreiheit_tage` oder `zinsfreiheit_tage - alter_tage <= 30`). Damit Hyundai dort korrekt mitläuft, müsste `zinsfreiheit_tage` im Hyundai-Finance-Import gesetzt werden (z. B. als `(zins_startdatum - vertragsbeginn).days`).
