# Teile & Lager — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-11

## Beschreibung

Teile und Lager umfassen Teile-Bestellungen, Teile-Status, Renner/Penner-Analyse, MOBIS Teilebezug (Hyundai) und Teilekatalog-Scraper (z. B. Schaeferbarthold, Dello, Repdoc).

## Module & Dateien

### APIs
- `api/teile_api.py`, `api/teile_data.py` — Teile-Kern
- `api/teile_status_api.py` — Teile-Status
- `api/parts_api.py` — Parts
- `api/renner_penner_api.py` — Renner/Penner
- `api/mobis_teilebezug_api.py` — MOBIS (Hyundai)

### Templates
- `templates/aftersales/teilebestellungen*.html`
- `templates/aftersales/renner_penner*.html`

### Tools
- `tools/scrapers/` (schaeferbarthold, dello, repdoc)

### Celery Tasks
- `sync_teile`, `import_teile`, `import_stellantis`, `update_penner_marktpreise`, `email_penner_weekly`

## DB-Tabellen (PostgreSQL drive_portal)

- `delivery_notes`, `parts`, `parts_orders`

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ Teilebestellungen, Renner/Penner, MOBIS in Nutzung
- 🔧 Scraper und Automatisierung je nach Projektstand
- ❌ Offene Punkte ggf. in Session-TODOs

## Offene Entscheidungen

- (Keine festgehalten)

## Abhängigkeiten

- Werkstatt (Lieferscheine), Integrations (Stellantis, Hyundai), Infrastruktur (Celery)
