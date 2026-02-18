# Teile & Lager — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-17

## Beschreibung

Teile und Lager umfassen Teile-Bestellungen, Teile-Status, Renner/Penner-Analyse, MOBIS Teilebezug (Hyundai) und Teilekatalog-Scraper (z. B. Schaeferbarthold, Dello, Repdoc). Stellantis ServiceBox-Zugang für Bestellungen und geplante DRIVE-Features.

## Module & Dateien

### APIs
- `api/teile_api.py`, `api/teile_data.py` — Teile-Kern
- `api/teile_status_api.py` — Teile-Status
- `api/parts_api.py` — Parts (inkl. ServiceBox-URL mit Auth)
- `api/renner_penner_api.py` — Renner/Penner
- `api/mobis_teilebezug_api.py` — MOBIS (Hyundai)
- `api/admin_api.py` — GET/POST `/api/admin/servicebox-config` (Passwort & Ablaufdatum)

### Templates
- `templates/aftersales/teilebestellungen*.html`
- `templates/aftersales/renner_penner*.html`
- `templates/admin/servicebox_zugang.html` — Admin: ServiceBox Passwort & Ablaufdatum

### Tools
- `tools/scrapers/` (schaeferbarthold, dello, repdoc, servicebox_*)

### Celery Tasks
- `sync_teile`, `import_teile`, `import_stellantis`, `update_penner_marktpreise`, `email_penner_weekly`
- `servicebox_scraper`, `servicebox_matcher`, `servicebox_import`, `servicebox_master`
- `check_servicebox_password_expiry` — täglich 8:00, E-Mail an Servicelieter bei ablaufendem Passwort

## ServiceBox-Zugang (Stellantis)

- **Credentials:** `config/credentials.json` → `external_systems.stellantis_servicebox` (username, password, portal_url, password_expires_at, reminder_emails)
- **Admin-UI:** Admin → ServiceBox Zugang — Passwort ändern, Ablaufdatum setzen, Erinnerungs-E-Mails (z. B. Matthias König, Florian Greiner)
- **Erinnerung:** Task `check_servicebox_password_expiry` sendet E-Mail, wenn Passwort abgelaufen oder in ≤14 Tagen abläuft

## DB-Tabellen (PostgreSQL drive_portal)

- `delivery_notes`, `parts`, `parts_orders`

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ Teilebestellungen, Renner/Penner, MOBIS in Nutzung
- ✅ ServiceBox-Zugang: Admin-Eingabe Passwort/Ablaufdatum, E-Mail-Erinnerung an Servicelieter (Matthias König, Florian Greiner)
- ✅ ServiceBox-Nav-Punkt in DB-Navigation (Migration ausgeführt), kein Hardcoding in base.html
- 🔧 Scraper und Automatisierung je nach Projektstand
- ❌ Vanessa testet ServiceBox-Zugang (Admin → ServiceBox Zugang) morgen

## Offene Entscheidungen

- (Keine festgehalten)

## Abhängigkeiten

- Werkstatt (Lieferscheine), Integrations (Stellantis, Hyundai), Infrastruktur (Celery)
