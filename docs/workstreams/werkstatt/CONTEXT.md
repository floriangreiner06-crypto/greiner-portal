# Werkstatt & Aftersales — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-11

## Beschreibung

Werkstatt und Aftersales umfassen TEK-Dashboard, Stempeluhr/Live-Monitoring, Mechaniker-Leistung, ML-Prognosen, Gudat-Integration, Serviceberater-Dashboard, Garantie-Aufträge und -Akte, Arbeitskarte, Reparaturpotenzial, SOAP-Schnittstellen und ServiceBox-Scraper.

## Module & Dateien

### APIs
- `api/werkstatt_api.py`, `api/werkstatt_data.py` — Werkstatt-Kern
- `api/werkstatt_live_api.py` — Stempeluhr, Live-Monitoring
- `api/serviceberater_api.py`, `api/serviceberater_data.py` — Serviceberater-Dashboard
- `api/garantie_auftraege_api.py` — Garantie-Aufträge
- `api/arbeitskarte_api.py` — Arbeitskarte
- `api/reparaturpotenzial_api.py` — Reparaturpotenzial
- `api/gudat_api.py`, `api/gudat_data.py` — Gudat-Integration
- `api/ml_api.py`, `api/ai_api.py` — ML/Prognosen

### Templates
- `templates/aftersales/*.html`
- `templates/controlling/tek_dashboard.html`

### Tools / Scripts
- `tools/gudat_*.py`
- `tools/scrapers/servicebox_*.py`
- `scripts/ml/`

### Celery Tasks
- `werkstatt_leistung`, `servicebox_*`, `email_werkstatt_tagesbericht`, `email_tek_daily`, `ml_retrain`, `benachrichtige_serviceberater_ueberschreitungen`

## DB-Tabellen (PostgreSQL drive_portal)

- `orders`, `labours`, View `times`, `employees_history`, `absence_calendar`, `werkstatt_leistung_daily`, `delivery_notes`

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ TEK-Dashboard, Stempeluhr, Serviceberater, Gudat-Anbindung in Nutzung
- 🔧 ML, Garantieakte, ServiceBox je nach Projektstand
- ❌ Offene Punkte ggf. in Session-TODOs

## Offene Entscheidungen

- (Keine festgehalten)

## Abhängigkeiten

- HR/Locosoft (Mitarbeiter), Integrations (Locosoft SOAP, ServiceBox), Infrastruktur (Celery)
