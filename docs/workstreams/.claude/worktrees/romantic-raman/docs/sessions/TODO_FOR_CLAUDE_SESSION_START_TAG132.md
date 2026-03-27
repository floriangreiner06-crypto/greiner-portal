# TODO für Claude - Session Start TAG 132

## Kontext
TAG 131 hat Ersatzwagen-Kalender PoC mit Carloop-Integration erstellt.

## Offene Aufgaben

### 1. Carloop-Sync testen
- Server hat jetzt `models`-Ordner
- `/test/ersatzwagen` aufrufen → "Carloop Sync" klicken
- Prüfen ob Reservierungen in Tabelle erscheinen

### 2. Automatischen Sync-Job einrichten
- Scheduler-Task für täglichen/stündlichen Carloop-Sync
- `scheduler/job_definitions.py` erweitern

### 3. Locosoft-Schreibintegration
- Carloop-Reservierung → Locosoft-Termin mit rentalCar
- SOAP `writeAppointment` nutzen

### 4. UI-Verbesserungen
- Drag&Drop: Ersatzwagen → Termin zuweisen
- Timeline-Ansicht für Belegungskalender
- Filter nach Fahrzeugtyp/Modell

## Relevante Dateien
- `api/ersatzwagen_api.py` - API-Endpoints
- `tools/carloop_scraper.py` - Carloop Web-Scraper
- `models/carloop_models.py` - SQLite-Tabellen
- `templates/test/ersatzwagen_kalender.html` - Test-UI

## Test-URL
`https://drive.auto-greiner.de/test/ersatzwagen`
