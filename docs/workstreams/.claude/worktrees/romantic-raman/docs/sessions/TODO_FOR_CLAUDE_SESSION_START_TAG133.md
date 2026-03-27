# TODO für Claude - Session Start TAG 133

## Kontext
TAG 132 hat TEK Daily PDF Reports implementiert (Test erfolgreich).

## Offene Aufgaben

### 1. TEK Report Produktion aktivieren
- `scripts/send_daily_tek.py`: TEST_MODE = False
- Cronjob einrichten (17:30 Mo-Fr)
- Entscheiden: Ein Report für alle oder pro Standort?

### 2. Carloop-Sync testen (von TAG131)
- `/test/ersatzwagen` aufrufen → "Carloop Sync" klicken
- Prüfen ob Reservierungen in Tabelle erscheinen
- Server hat `models`-Ordner

### 3. Automatischen Carloop-Sync-Job einrichten
- Scheduler-Task für täglichen/stündlichen Carloop-Sync
- `scheduler/job_definitions.py` erweitern

## Relevante Dateien
- `scripts/send_daily_tek.py` - TEK Report Script
- `api/pdf_generator.py` - PDF-Generator mit TEK-Funktion
- `api/ersatzwagen_api.py` - Ersatzwagen API
- `tools/carloop_scraper.py` - Carloop Web-Scraper

## Test-URLs
- TEK: `http://drive.auto-greiner.de/controlling/tek`
- Ersatzwagen: `http://drive.auto-greiner.de/test/ersatzwagen`
