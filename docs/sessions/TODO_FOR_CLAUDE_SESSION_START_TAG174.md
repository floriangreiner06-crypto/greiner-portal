# TODO für Claude - Session Start TAG 174

**Erstellt:** 2026-01-09  
**Letzte Session:** TAG 173 (ServiceBox API-Scraper & UI-Verbesserungen)

## 📋 Kontext aus letzter Session

In TAG 173 wurden folgende Aufgaben erledigt:
- **ServiceBox Modal implementiert**: Detail-Ansicht öffnet jetzt Modal statt neuen Tab
- **API-Endpoint gefunden**: `listCommandesRepAll.do` kann direkt genutzt werden
- **API-Scraper erstellt**: Selenium nur für Login, Requests für Daten (10x schneller)
- **UI-Pagination**: 20 Bestellungen pro Seite
- **API-Standard-Filter**: 30 → 90 Tage (436 Bestellungen verfügbar)

## 🎯 Prioritäten für TAG 174

### 1. ServiceBox Scraper testen (HOCH)
- **Status:** API-Scraper erstellt, aber noch nicht vollständig getestet
- **Nächste Schritte:**
  - Scraper über UI starten: `/admin/celery/` → "ServiceBox Scraper"
  - Prüfen ob alle Seiten durchlaufen werden (nicht nur 5)
  - Logs prüfen: `journalctl -u celery-worker -f | grep servicebox`
  - Prüfen ob mehr als 50 Bestellungen gefunden werden

### 2. UI-Pagination testen (MITTEL)
- **Status:** Implementiert, aber noch nicht im Browser getestet
- **Nächste Schritte:**
  - Öffnen: `/werkstatt/teilebestellungen`
  - Prüfen ob Pagination-Controls sichtbar sind
  - Testen: Vorherige/Nächste, Seitenzahlen
  - Prüfen ob 20 Bestellungen pro Seite angezeigt werden

### 3. Service neu starten (HOCH)
- **Status:** HUP-Signal gesendet, aber vollständiger Neustart empfohlen
- **Grund:** API-Änderungen (90-Tage-Filter)
- **Aktion:** `sudo systemctl restart greiner-portal`

### 4. Git-Commit (NIEDRIG)
- **Status:** Änderungen noch nicht committed
- **Dateien:** 18 geänderte, 4 neue Dateien
- **Aktion:** Prüfen ob diese committed werden sollen

## 🔍 Wichtige Dateien

### Neue Dateien (aus TAG 173):
- `tools/scrapers/servicebox_api_scraper.py` - API-Scraper (NEU)
- `tools/scrapers/servicebox_bestellungen_network_analyzer.py` - Network-Analyzer (NEU)
- `tools/scrapers/servicebox_api_test_bestellungen.py` - API-Test (NEU)
- `docs/ANALYSE_SERVICEBOX_TAG173.md` - Analyse-Dokumentation (NEU)

### Geänderte Dateien (aus TAG 173):
- `api/parts_api.py` - 90-Tage-Filter, lieferschein_status
- `templates/aftersales/teilebestellungen.html` - Modal, Pagination
- `celery_app/tasks.py` - API-Scraper Task
- `tools/scrapers/servicebox_detail_scraper_final.py` - Pagination verbessert
- `scripts/imports/import_mt940.py` - Mount-Check mit Retry
- `scripts/scrapers/match_servicebox.py` - PostgreSQL (bereits migriert)
- `scripts/imports/import_servicebox_to_db.py` - PostgreSQL (bereits migriert)
- `requirements.txt` - beautifulsoup4 hinzugefügt

### Wichtige Endpoints:
- `/api/parts/bestellungen` - Teilebestellungen (90-Tage-Filter, Pagination)
- `/api/parts/bestellung/<bestellnummer>` - Detail mit lieferschein_status
- `/admin/celery/` - Task Manager UI

## ⚠️ Bekannte Issues

### 1. Scraper findet nur 50 Bestellungen
- **Status:** ⚠️ Möglicherweise behoben (Pagination-Logik verbessert)
- **Problem:** Scraper stoppt nach 5 Seiten (50 Bestellungen)
- **Ursache:** Unklar - möglicherweise Datumsfilter im ServiceBox Portal
- **Nächster Schritt:** Beim nächsten Scraper-Lauf prüfen ob alle Seiten durchlaufen werden

### 2. Service-Neustart erforderlich
- **Status:** ⚠️ HUP-Signal gesendet, aber vollständiger Neustart empfohlen
- **Grund:** API-Änderungen (90-Tage-Filter)
- **Aktion:** `sudo systemctl restart greiner-portal`

## 📝 Nächste Schritte

1. **Session-Start:**
   - User fragen: Was ist die Priorität heute?
   - Scraper testen?
   - UI testen?
   - Service neu starten?

2. **Entwicklung:**
   - Je nach Priorität des Users
   - Falls Scraper: Logs prüfen, alle Seiten testen
   - Falls UI: Browser-Test, Pagination testen

3. **Session-Ende:**
   - `/session-end` verwenden
   - Dokumentation erstellen
   - Git-Commit falls nötig

## 🔗 Referenzen

- Letzte Session: `docs/sessions/SESSION_WRAP_UP_TAG173.md`
- Projekt-Kontext: `CLAUDE.md`
- DB-Schema: `docs/DB_SCHEMA_POSTGRESQL.md`
- ServiceBox Analyse: `docs/ANALYSE_SERVICEBOX_TAG173.md`

## 💡 Tipps

- **Scraper testen:** Über UI starten: `/admin/celery/` → "ServiceBox Scraper"
- **Logs prüfen:** `journalctl -u celery-worker --since "10 minutes ago" | grep servicebox`
- **API testen:** `curl -s "http://localhost:5000/api/parts/bestellungen?limit=20&offset=0" | python3 -m json.tool`
- **Bestellungen prüfen:** `PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -c "SELECT COUNT(*) FROM stellantis_bestellungen;"`
- **Service-Status:** `systemctl status greiner-portal`

## 📌 Wichtige Erkenntnisse aus TAG 173

- **ServiceBox hat API-Endpoint!** Nicht nur Scraping möglich
- **API-Scraper ist 10x schneller** als Selenium-Scraper
- **Pagination funktioniert über `sort.do`** mit `pagerPage` Parameter
- **UI-Pagination verbessert Performance** (20 pro Seite)
- **Modal statt Navigation** für bessere UX

## 🎯 Offene Aufgaben

1. **Scraper vollständig testen**
   - Prüfen ob alle Seiten durchlaufen werden
   - Falls nicht: Ursache finden (Datumsfilter? Standorte?)

2. **UI-Pagination testen**
   - Browser-Test erforderlich
   - Pagination-Controls prüfen

3. **Monitoring implementieren**
   - Übersicht für gelaufene Jobs
   - Redundanz zwischen `scheduler/routes.py` und `celery_app/routes.py` analysieren

4. **Git-Commit**
   - 18 geänderte, 4 neue Dateien
   - Prüfen ob committed werden soll
