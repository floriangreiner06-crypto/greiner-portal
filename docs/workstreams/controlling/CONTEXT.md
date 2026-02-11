# Controlling (BWA, Bankenspiegel, Finanzreporting) — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-11

## Beschreibung

Controlling umfasst BWA-Berechnung, Bankenspiegel mit Konten und Transaktionen, den Finanzreporting-Cube sowie Kontenmapping. MT940/CAMT/PDF-Import, Umsatz-Bereinigung, Stundensatz-Kalkulation und Zins-Optimierung gehören ebenfalls in diesen Workstream.

## Module & Dateien

### APIs
- `api/bankenspiegel_api.py` — Dashboard, Konten, Transaktionen, Einkaufsfinanzierung, Fahrzeuge mit Zinsen
- `api/controlling_api.py` — BWA, BWA v2, Drilldown, DB1-Entwicklung
- `api/controlling_data.py` — Datenlayer BWA
- `api/finanzreporting_api.py` — Finanzreporting-Cube
- `api/kontenmapping_api.py` — Kontenmapping
- `api/stundensatz_kalkulation_api.py` — Stundensatz-Kalkulation
- `api/zins_optimierung_api.py` — Zins-Optimierung

### Templates
- `templates/bankenspiegel_*.html`
- `templates/controlling/*.html`

### Parser / Daten
- `parsers/` — MT940, CAMT, PDF-Import

### Celery Tasks
- `import_mt940`, `import_hvb_pdf`, `umsatz_bereinigung`, `bwa_berechnung`, `refresh_finanzreporting_cube`

## DB-Tabellen (PostgreSQL drive_portal)

- `konten`, `banken`, `transaktionen`, `daily_balances`, `kategorien`, `kreditlinien`, `fibu_buchungen`, `bwa_monatswerte`

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ Bankenspiegel, BWA, Finanzreporting-Cube im Einsatz
- ✅ MT940/HVB-PDF-Import, Umsatz-Bereinigung
- 🔧 Kontenmapping und Stundensatz-Kalkulation je nach Projektstand
- ❌ Offene Punkte ggf. in Session-TODOs

## Offene Entscheidungen

- (Keine festgehalten)

## Abhängigkeiten

- Infrastruktur (PostgreSQL, Celery), ggf. auth-ldap für Berechtigungen
