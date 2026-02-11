# Verkauf & Fahrzeuge — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-11

## Beschreibung

Verkauf umfasst Auftragseingang, Auslieferungen, Deckungsbeitrag, Profitabilität, Gewinnplanung V2 (GW), Fahrzeug-Daten, eAutoSeller und Ersatzwagen.

## Module & Dateien

### APIs
- `api/verkauf_api.py`, `api/verkauf_data.py` — Verkauf-Kern
- `api/profitabilitaet_api.py`, `api/profitabilitaet_data.py` — Profitabilität
- `api/fahrzeug_api.py`, `api/fahrzeug_data.py` — Fahrzeug-Daten
- `api/gewinnplanung_v2_gw_api.py`, `api/gewinnplanung_v2_gw_data.py` — Gewinnplanung V2 (GW)
- `api/eautoseller_api.py` — eAutoSeller
- `api/ersatzwagen_api.py` — Ersatzwagen

### Templates
- `templates/verkauf_*.html`
- `templates/planung/gewinnplanung_*.html`

### Celery Tasks
- `sync_sales`, `email_auftragseingang`, `sync_eautoseller_data`

## DB-Tabellen (PostgreSQL drive_portal)

- `sales`, `vehicles`, `dealer_vehicles`, `customers_suppliers`

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ Auftragseingang, Profitabilität, Gewinnplanung im Einsatz
- 🔧 eAutoSeller, Ersatzwagen je nach Projektstand
- ❌ Offene Punkte ggf. in Session-TODOs

## Offene Entscheidungen

- (Keine festgehalten)

## Abhängigkeiten

- Integrations (eAutoSeller API), Infrastruktur (Celery)
