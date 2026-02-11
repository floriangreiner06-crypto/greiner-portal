# TODO für Claude - Session Start TAG 172

**Erstellt:** 2026-01-08  
**Letzte Session:** TAG 171 (ServiceBox Sync Debugging & TEST_MODE Entfernung)

## 📋 Kontext aus letzter Session

In TAG 171 wurden folgende Aufgaben erledigt:
- **ServiceBox Scraper Debugging**: Tasks waren nicht definiert, jetzt alle 4 Tasks implementiert
- **ServiceBox Passwort aktualisiert**: `Okto2025` → `Janu2026`
- **TEST_MODE entfernt**: Task sendet nur noch bei echten Überschreitungen
- **Abgeschlossene Überschreitungen**: Werden jetzt auch erkannt

## 🎯 Prioritäten für TAG 172

### 1. ServiceBox Scraper weiter debuggen (HOCH)
- **Problem:** Scraper findet "0 eindeutige Bestellungen"
- **Status:** Login funktioniert, Navigation funktioniert
- **Mögliche Ursachen:**
  - Keine neuen Bestellungen vorhanden
  - Seitenstruktur hat sich geändert
  - Scraper-Logik muss angepasst werden
- **Nächste Schritte:**
  - Screenshot der Historie-Seite prüfen
  - Scraper-Logik für Bestellungs-Extraktion prüfen
  - `tools/scrapers/servicebox_detail_scraper_final.py` analysieren

### 2. Uncommittete Änderungen prüfen (MITTEL)
- **Status:** Es gibt uncommittete Änderungen aus vorherigen Sessions
- **Dateien:**
  - `api/parts_api.py` - Serviceberater-Filter für Teilebestellungen
  - `api/werkstatt_live_api.py` - Modal-Endpoint mit Mechaniker/Auftragsdatum/SB
  - `app.py` - Serviceberater-Redirect-Logik
  - `routes/app.py` - Serviceberater-Redirect-Logik
  - `templates/base.html` - Globales Modal
  - `templates/sb/mein_bereich.html` - Serviceberater-Dashboard-Anpassungen
  - `celery_app/tasks.py` - TEST_MODE entfernt, ServiceBox Tasks
  - `config/credentials.json` - ServiceBox Passwort aktualisiert
- **Aktion:** Prüfen ob diese committed werden sollen
- **Befehl:** `git diff` um Änderungen zu sehen

### 3. Monitoring & Logs (NIEDRIG)
- **Celery Task-Logs prüfen**
  - Prüfen ob E-Mails korrekt versendet werden
  - `journalctl -u celery-worker -f | grep ueberschreitung`
- **ServiceBox Sync-Logs prüfen**
  - Prüfen ob Scraper regelmäßig läuft
  - `journalctl -u celery-worker -f | grep servicebox`
- **Celery Beat prüfen**
  - `sudo systemctl status celery-beat`

## 🔍 Wichtige Dateien

### Geänderte Dateien (aus TAG 171):
- `celery_app/tasks.py` - TEST_MODE entfernt, ServiceBox Tasks definiert
- `config/credentials.json` - ServiceBox Passwort aktualisiert

### Geänderte Dateien (aus vorherigen Sessions, noch uncommittet):
- `api/parts_api.py` - Serviceberater-Filter für Teilebestellungen
- `api/werkstatt_live_api.py` - Modal-Endpoint mit Mechaniker/Auftragsdatum/SB
- `app.py` - Serviceberater-Redirect-Logik
- `routes/app.py` - Serviceberater-Redirect-Logik
- `templates/base.html` - Globales Modal
- `templates/sb/mein_bereich.html` - Serviceberater-Dashboard-Anpassungen

### ServiceBox Scraper:
- `tools/scrapers/servicebox_detail_scraper_final.py` - Haupt-Scraper
- `tools/scrapers/servicebox_locosoft_matcher.py` - Matcher
- `scripts/imports/import_servicebox_to_db.py` - Import
- `tools/scrapers/servicebox_scraper_complete.py` - Master-Scraper

### Wichtige Endpoints:
- `/api/werkstatt/live/meine-ueberschreitungen` - Prüft User-Überschreitungen
- `/api/parts/bestellungen` - Teilebestellungen (gefiltert nach Serviceberater)

## ⚠️ Bekannte Issues

1. **ServiceBox Scraper findet keine Bestellungen**
   - Status: Login funktioniert, Navigation funktioniert
   - Problem: "0 eindeutige Bestellungen gefunden"
   - Mögliche Ursachen:
     - Keine neuen Bestellungen vorhanden
     - Seitenstruktur hat sich geändert
     - Scraper-Logik muss angepasst werden
   - Nächster Schritt: Screenshot der Historie-Seite prüfen und Scraper-Logik anpassen

2. **Uncommittete Änderungen**
   - Mehrere Dateien haben uncommittete Änderungen
   - Sollten diese committed werden?

## 📝 Nächste Schritte

1. **Session-Start:**
   - User fragen: Was ist die Priorität heute?
   - ServiceBox Scraper weiter debuggen?
   - Uncommittete Änderungen prüfen/committen?
   - Monitoring prüfen?

2. **Entwicklung:**
   - Je nach Priorität des Users
   - Falls ServiceBox: Screenshot prüfen, Scraper-Logik analysieren
   - Falls Git: Änderungen prüfen und committen

3. **Session-Ende:**
   - `/session-end` verwenden
   - Dokumentation erstellen
   - Git-Commit falls nötig

## 🔗 Referenzen

- Letzte Session: `docs/sessions/SESSION_WRAP_UP_TAG171.md`
- Projekt-Kontext: `CLAUDE.md`
- Celery-Config: `celery_app/__init__.py`
- ServiceBox Scraper: `tools/scrapers/servicebox_detail_scraper_final.py`

## 💡 Tipps

- **Git Status:** `git status` zeigt uncommittete Änderungen
- **Git Diff:** `git diff` zeigt Änderungen in Dateien
- **Celery Beat prüfen:** `sudo systemctl status celery-beat`
- **ServiceBox Logs:** `journalctl -u celery-worker -f | grep servicebox`
- **ServiceBox Scraper testen:** Manuell ausführen und Screenshot machen
- **TEST_MODE:** Wurde entfernt, Task sendet nur noch bei echten Überschreitungen

## 📌 Wichtige Erkenntnisse aus TAG 171

- **ServiceBox Tasks waren nicht definiert**: Alle 4 Tasks sind jetzt in `celery_app/tasks.py` definiert
- **ServiceBox Passwort abgelaufen**: Aktualisiert auf `Janu2026`
- **TEST_MODE entfernt**: Task sendet nur noch bei echten Überschreitungen
- **Abgeschlossene Überschreitungen**: Werden jetzt auch erkannt durch direkte DB-Abfrage
- **Scraper findet keine Bestellungen**: Möglicherweise Seitenstruktur geändert oder keine neuen Bestellungen
