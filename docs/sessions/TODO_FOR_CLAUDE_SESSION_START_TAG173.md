# TODO für Claude - Session Start TAG 173

**Erstellt:** 2026-01-08  
**Letzte Session:** TAG 172 (Bankenspiegel Zins- und Bestandsanalyse Debugging & Import-Migration)

## 📋 Kontext aus letzter Session

In TAG 172 wurden folgende Aufgaben erledigt:
- **View `fahrzeuge_mit_zinsen` erstellt**: PostgreSQL-kompatible View für Zinsanalyse
- **API-Endpoints korrigiert**: PostgreSQL-kompatibel, Filter nach `aktiv = true`
- **Import-Skripte migriert**: Stellantis und Hyundai von SQLite → PostgreSQL
- **Zinsfreiheit-Warnungen behoben**: 25 Warnungen werden jetzt korrekt angezeigt
- **Konsistenz hergestellt**: Zinsen-Analyse und Einkaufsfinanzierung zeigen gleiche Daten

## 🎯 Prioritäten für TAG 173

### 1. Import-Jobs Monitoring (MITTEL)
- **Status:** Stellantis und Hyundai Imports laufen jetzt in PostgreSQL
- **Nächste Schritte:**
  - Prüfen ob Jobs morgen automatisch laufen (07:30 Stellantis, 09:00 Hyundai)
  - Logs prüfen: `journalctl -u celery-worker -f | grep import`
  - Prüfen ob `import_datum` in PostgreSQL aktualisiert wird

### 2. Datenqualität prüfen (NIEDRIG)
- **Stellantis:** 112 Fahrzeuge (vorher 110) - möglicherweise Duplikate?
- **Hyundai:** 47 Fahrzeuge (vorher 48) - 1 Fahrzeug fehlt?
- **Aktion:** Prüfen ob alle Fahrzeuge korrekt importiert wurden

### 3. Git-Commit (NIEDRIG)
- **Status:** Änderungen noch nicht committed
- **Dateien:**
  - `migrations/create_fahrzeuge_mit_zinsen_view.sql` (NEU)
  - `api/bankenspiegel_api.py`
  - `api/zins_optimierung_api.py`
  - `templates/zinsen_analyse.html`
  - `static/js/einkaufsfinanzierung.js`
  - `scripts/imports/import_stellantis.py`
  - `scripts/imports/import_hyundai_finance.py`
- **Aktion:** Prüfen ob diese committed werden sollen

## 🔍 Wichtige Dateien

### Geänderte Dateien (aus TAG 172):
- `migrations/create_fahrzeuge_mit_zinsen_view.sql` - View für PostgreSQL
- `api/bankenspiegel_api.py` - API-Fixes (Filter, Warnungen, Marken)
- `api/zins_optimierung_api.py` - Konsistenz-Fixes
- `templates/zinsen_analyse.html` - Frontend-Fixes
- `static/js/einkaufsfinanzierung.js` - Warnungen-Anzeige
- `scripts/imports/import_stellantis.py` - PostgreSQL-Migration
- `scripts/imports/import_hyundai_finance.py` - PostgreSQL-Migration

### Wichtige Views:
- `fahrzeuge_mit_zinsen` - Wichtig für Zinsanalyse, nicht löschen!

### Wichtige Endpoints:
- `/api/bankenspiegel/einkaufsfinanzierung` - Bestandsanalyse
- `/api/bankenspiegel/fahrzeuge-mit-zinsen` - Zinsanalyse
- `/api/zinsen/dashboard` - Zinsen-Analyse Dashboard

## ⚠️ Bekannte Issues

Keine bekannten Issues.

## 📝 Nächste Schritte

1. **Session-Start:**
   - User fragen: Was ist die Priorität heute?
   - Import-Jobs prüfen?
   - Datenqualität prüfen?
   - Git-Commit durchführen?

2. **Entwicklung:**
   - Je nach Priorität des Users
   - Falls Import-Jobs: Logs prüfen, Monitoring einrichten
   - Falls Datenqualität: Duplikate prüfen, fehlende Fahrzeuge finden

3. **Session-Ende:**
   - `/session-end` verwenden
   - Dokumentation erstellen
   - Git-Commit falls nötig

## 🔗 Referenzen

- Letzte Session: `docs/sessions/SESSION_WRAP_UP_TAG172.md`
- Projekt-Kontext: `CLAUDE.md`
- DB-Schema: `docs/DB_SCHEMA_POSTGRESQL.md`
- View-Definition: `migrations/create_fahrzeuge_mit_zinsen_view.sql`

## 💡 Tipps

- **Import-Jobs prüfen:** `journalctl -u celery-worker --since "today" | grep import`
- **View prüfen:** `PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -c "SELECT COUNT(*) FROM fahrzeuge_mit_zinsen;"`
- **Warnungen prüfen:** `curl -s "http://localhost:5000/api/bankenspiegel/einkaufsfinanzierung" | python3 -m json.tool | grep warnungen`
- **Import-Datum prüfen:** `PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -c "SELECT finanzinstitut, MAX(import_datum) FROM fahrzeugfinanzierungen GROUP BY finanzinstitut;"`

## 📌 Wichtige Erkenntnisse aus TAG 172

- **View fehlte komplett**: `fahrzeuge_mit_zinsen` existierte nicht in PostgreSQL
- **Import-Skripte verwendeten SQLite**: Stellantis und Hyundai schrieben in alte DB
- **Zinsfreiheit-Warnungen**: Query war zu restriktiv, zeigte keine überfälligen Fahrzeuge
- **Konsistenz-Problem**: Zinsen-Analyse zeigte nur Teilmenge, Einkaufsfinanzierung alle Fahrzeuge
- **PostgreSQL-Syntax**: `ROUND()` braucht `::NUMERIC` Cast, `NOW()` statt `datetime('now')`
