# TODO für Claude - Session Start TAG 134

## Kontext
TAG 133 hat Lieferforecast-Dashboard mit DB1-Prognose implementiert.
Geplante Fahrzeugauslieferungen können jetzt mit Umsatz- und DB1-Prognose angezeigt werden.

## Neue Features TAG 133
- **Lieferforecast:** `http://drive.auto-greiner.de/verkauf/lieferforecast`
- Datenquelle: `vehicles.readmission_date` (PostgreSQL)
- DB1 aus SQLite `sales.deckungsbeitrag`

## Offene Aufgaben

### 1. TEK Report Produktion aktivieren
- `scripts/send_daily_tek.py`: TEST_MODE = False
- Cronjob einrichten (17:30 Mo-Fr)
- Entscheiden: Ein Report für alle oder pro Standort?

### 2. Carloop-Sync testen (von TAG131)
- `/test/ersatzwagen` aufrufen → "Carloop Sync" klicken
- Prüfen ob Reservierungen in Tabelle erscheinen

### 3. Automatischen Carloop-Sync-Job einrichten
- Scheduler-Task für täglichen/stündlichen Carloop-Sync
- `scheduler/job_definitions.py` erweitern

## Relevante Dateien
- `api/verkauf_api.py` - Lieferforecast API (neu)
- `templates/verkauf_lieferforecast.html` - Dashboard (neu)
- `scripts/send_daily_tek.py` - TEK Report Script
- `api/ersatzwagen_api.py` - Ersatzwagen API
- `tools/locosoft_soap_client.py` - SOAP Client (gefixt)

## Test-URLs
- Lieferforecast: `http://drive.auto-greiner.de/verkauf/lieferforecast`
- TEK: `http://drive.auto-greiner.de/controlling/tek`
- Ersatzwagen: `http://drive.auto-greiner.de/test/ersatzwagen`
