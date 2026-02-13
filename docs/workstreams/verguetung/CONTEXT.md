# Vergütung & Prämien — Arbeitskontext
## Status: Neu
## Letzte Aktualisierung: 2026-02-13
## Beschreibung
Zentrales Modul für alle leistungsbasierten Vergütungskomponenten:
Werkstatt-Prämien (TEK-KPIs), Verkäufer-Provisionen (Locosoft/Deckungsbeitrag),
und Jahresprämie (Migration aus HR). Einheitliche Berechnung, Konfiguration und Abrechnung.

## Geplante Module
### 1. Werkstatt-Prämien (als erstes umsetzen)
- 3 KPIs: Produktivität, Leistungsgrad, Effektivität
- Stufen-Prämien (Mechaniker: 50/100/150€, Azubis: 25/50/75€)
- Monatliche Team-Berechnung
- Datenquelle: werkstatt DB (times, orders, labours, absence_calendar)

### 2. Verkäufer-Provisionen (geplant)
- Aktuell: Locosoft CSV-Export → manuelle Excel-Aufbereitung → Abrechnung
- Ziel: Automatischer Import, Berechnung, Dashboard
- Datenquelle: Locosoft sales/Deckungsbeitrag

### 3. Jahresprämie (Migration aus HR-Workstream)
- Bereits vorhanden: api/jahrespraemie_api.py
- Migration hierher geplant

## Module & Dateien
### APIs (noch zu erstellen)
- api/praemien_api.py (Werkstatt-Prämien)
- api/provisionen_api.py (Verkäufer, geplant)
- api/jahrespraemie_api.py (Migration aus HR)
### Templates (noch zu erstellen)
- templates/verguetung/werkstatt_praemien.html
- templates/verguetung/provisionen.html (geplant)
- templates/verguetung/uebersicht.html (Gesamt-Dashboard)
### Celery Tasks (geplant)
- monatliche Prämienberechnung Werkstatt
- Provisionsimport Verkauf
### Scripts
- Import Locosoft CSV (geplant)

## DB-Tabellen (PostgreSQL drive_portal, noch zu erstellen)
- praemien_config (KPI-Schwellwerte, Stufen, Beträge pro Gruppe)
- praemien_berechnungen (monatliche Ergebnisse pro Mitarbeiter)
- provisionen_config (Verkäufer-Regeln, geplant)
- provisionen_berechnungen (geplant)

## Aktueller Stand
- ❌ Werkstatt-Prämien: Konzept in Excel vorhanden, Umsetzung steht aus
- ❌ Verkäufer-Provisionen: Noch manueller Excel-Prozess
- ✅ Jahresprämie: Existiert in HR, Migration geplant

## Abhängigkeiten
- werkstatt (TEK-Daten, Stunden, Anwesenheit)
- verkauf (Deckungsbeitrag, Aufträge für Provisionen)
- hr (Mitarbeiter-Stammdaten, Funktionen/Gruppen)
- controlling (Kostenauswirkung, Reporting)
