# Fahrzeugfinanzierungen & Zinsen — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-25

## Beschreibung

Fahrzeugfinanzierungen umfassen Zinssatz-Tracking, Einkaufsfinanzierung, Santander/Stellantis/Hyundai Finance, Leasys-Kalkulator, Zins-Optimierung und Zins-Analyse.

## Module & Dateien

### APIs
- `api/zins_optimierung_api.py` — Zins-Optimierung, Zins-Analyse
- `api/leasys_api.py` — Leasys-Kalkulator

### Templates
- `templates/fahrzeugfinanzierungen.html`
- `templates/einkaufsfinanzierung.html`
- `templates/leasys_*.html`
- `templates/zinsen_analyse.html`

### Tools
- `tools/scrapers/hyundai_*.py`, `tools/scrapers/leasys_*.py`

### Celery Tasks
- `import_santander`, `import_hyundai`, `scrape_hyundai`, `leasys_cache_refresh`

## DB-Tabellen (PostgreSQL drive_portal)

- `fahrzeugfinanzierungen`, `zinssaetze_historie`, `fahrzeuge_mit_zinsen`

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ Einkaufsfinanzierung, Leasys, Zins-Analyse im Einsatz
- ✅ **Fahrzeugdetails Typ (2026-02-25):** Anzeige aus Locosoft `out_sale_type`/`pre_owned_car_code`/`is_rental` (wie Provisions-/AfA-Modul).
- ✅ **Modell in Listen (2026-02-25):** Listen (Stellantis/Santander/Hyundai), Warnungen, Top10, Fahrzeuge mit Zinsen mit Modell aus Locosoft angereichert, wenn in DB leer.
- ✅ **Kennzeichen (2026-02-25):** Spalte `kennzeichen` in `fahrzeugfinanzierungen` (Migration), Sync in `sync_stammdaten`/`sync_fahrzeug_stammdaten` aus Locosoft.
- ✅ **Zinsfreiheit-Doku:** `docs/workstreams/controlling/ZINSFREIHEIT_STELLANTIS_HYUNDAI.md` (Stellantis/Santander/Hyundai).
- 🔧 Santander/Hyundai-Import, Scraper je nach Projektstand

## Offene Entscheidungen

- (Keine festgehalten)

## Abhängigkeiten

- Controlling (Zins-Optimierung API), Integrations (Hyundai, Leasys), Infrastruktur (Celery)
