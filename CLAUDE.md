# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Arbeitsumgebung

**Server:** 10.80.80.20 (auto-greiner.de)
**Projekt-Pfad:** `/opt/greiner-portal/`
**Test-Umgebung:** `/data/greiner-test/` (Port 5001)
**SSH User:** ag-admin
**Sudo PW:** OHL.greiner2025

### Sync-Architektur
Claude editiert Dateien im Windows-Sync-Verzeichnis. Diese sind auf dem Linux-Server gemountet:
```
Windows:  \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\
Server:   /mnt/greiner-portal-sync/
```

## Deployment-Befehle (für User auf Server)

```bash
# Einzelne Datei syncen
cp /mnt/greiner-portal-sync/api/vacation_api.py /opt/greiner-portal/api/

# Ordner syncen (WICHTIG: --exclude '.git' bei rsync!)
rsync -av --exclude '.git' /mnt/greiner-portal-sync/scheduler/ /opt/greiner-portal/scheduler/

# Nach Python-Änderungen: Neustart erforderlich!
sudo systemctl restart greiner-portal

# Logs
journalctl -u greiner-portal -f

# Service-Status
sudo systemctl status greiner-portal
```

**Templates brauchen KEINEN Neustart** - nur Browser-Refresh (Strg+F5)

## Architektur

### Tech-Stack
- **Backend:** Flask 3.0 + Gunicorn (4 workers)
- **Frontend:** Jinja2 + Bootstrap 5 + Chart.js
- **Auth:** LDAP/Active Directory via Flask-Login
- **Datenbank:** PostgreSQL (seit TAG 135)
- **Scheduler:** Celery + Redis

### Request-Flow
```
Browser → Flask Routes (routes/) → API-Layer (api/) → PostgreSQL
                ↓
         Templates (templates/)
```

### Modul-Struktur
| Bereich | API | Routes | Templates |
|---------|-----|--------|-----------|
| Finanzen | `bankenspiegel_api.py`, `controlling_api.py` | `bankenspiegel_routes.py` | `bankenspiegel_*.html` |
| Verkauf | `verkauf_api.py`, `leasys_api.py`, `budget_api.py` | `verkauf_routes.py` | `verkauf_*.html` |
| Urlaub | `vacation_api.py`, `vacation_chef_api.py`, `vacation_admin_api.py` | in app.py | `urlaubsplaner_*.html` |
| Werkstatt | `werkstatt_api.py`, `werkstatt_live_api.py` | `werkstatt_routes.py` | `aftersales/*.html` |
| Teile | `parts_api.py`, `teile_api.py`, `teile_status_api.py` | in routes | `aftersales/*.html` |
| Admin | `admin_api.py`, `organization_api.py` | `admin_routes.py` | `admin_*.html` |

### Authentifizierung
1. LDAP-Login via `auth/ldap_connector.py`
2. Session-Management in `auth/auth_manager.py`
3. OU-basiertes Role-Mapping (z.B. OU=Geschäftsleitung → admin)
4. Permission-Check: `current_user.can_access_feature('modulname')`

### Job-Scheduler (Celery)
- **Task-Definitionen:** `celery_app/tasks.py`
- **Celery-Config:** `celery_app/celery_config.py`
- **Web-UI:** `/admin/celery/` (Task Manager)
- **Flower Dashboard:** Port 5555
- **Redis:** Message Broker für Celery

## Datenbanken

### PostgreSQL DRIVE Portal (Hauptdatenbank)
**Host:** 127.0.0.1:5432
**Database:** drive_portal
**User:** drive_user
**Password:** DrivePortal2024
**Schema:** `docs/DB_SCHEMA_POSTGRESQL.md`
**161 Tabellen** - wichtigste:
- `konten`, `transaktionen`, `banken` - Bankenspiegel
- `employees`, `vacation_bookings`, `vacation_approval_rules` - Urlaubsplaner
- `fahrzeugfinanzierungen` - Fahrzeug-Zinsen
- `users`, `ldap_employee_mapping` - Auth
- `budget_plan` - Verkaufs-Budget (TAG 143)

```bash
# DRIVE Portal DB
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -c "SELECT ..."
```

### PostgreSQL Locosoft (extern, read-only)
**Host:** 10.80.80.8:5432
**Database:** loco_auswertung_db
**User:** loco_auswertung_benutzer
**Password:** loco
**Schema:** `docs/DB_SCHEMA_LOCOSOFT.md`

```bash
# Locosoft DB
PGPASSWORD=loco psql -h 10.80.80.8 -U loco_auswertung_benutzer -d loco_auswertung_db -c "SELECT ..."
```

### DB-Verbindung in Python

```python
from api.db_connection import get_db, get_db_type

# DRIVE Portal (PostgreSQL)
conn = get_db()  # Automatisch PostgreSQL via DB_TYPE=postgresql
cursor = conn.cursor()
cursor.execute("SELECT * FROM employees WHERE active = true")
rows = cursor.fetchall()  # HybridRow: row[0] UND row['name'] funktionieren!
conn.close()

# Locosoft
from api.db_utils import get_locosoft_connection
conn = get_locosoft_connection()
```

### Standort-Mapping
```
1 = Deggendorf Opel (DEG)
2 = Deggendorf Hyundai (HYU)
3 = Landau (LAN)
```

## Wichtige Dateien

| Zweck | Datei |
|-------|-------|
| Flask Entry | `app.py` (Blueprints, Routes, Login) |
| Base Template | `templates/base.html` (Navigation) |
| Auth-System | `auth/auth_manager.py` |
| LDAP-Connector | `auth/ldap_connector.py` |
| DB-Connection | `api/db_connection.py` (PostgreSQL + HybridRow) |
| DB-Schema | `docs/DB_SCHEMA_POSTGRESQL.md` |
| Locosoft-Schema | `docs/DB_SCHEMA_LOCOSOFT.md` |

## Session-Dokumentation

Bei Session-Start lesen:
1. Diese Datei (`CLAUDE.md`)
2. `docs/sessions/TODO_FOR_CLAUDE_SESSION_START_TAG[X].md`
3. `docs/sessions/SESSION_WRAP_UP_TAG[X-1].md`
4. **Standards für neue Features beachten** (siehe `.claude/commands/session-start.md`)

Bei Session-Ende erstellen:
1. **Qualitätscheck durchführen** (Redundanzen, SSOT, Code-Duplikate)
2. `docs/sessions/SESSION_WRAP_UP_TAG[X].md` (inkl. Qualitätscheck-Ergebnisse)
3. `docs/sessions/TODO_FOR_CLAUDE_SESSION_START_TAG[X+1].md`
4. **Git-Commit lokal** (Windows)
5. **Git-Commit auf Server** (siehe unten)

**Qualitätscheck-Template:** `docs/QUALITAETSCHECK_TEMPLATE.md`

### Git auf Server aktualisieren (IMMER am Session-Ende!)
```bash
ssh ag-admin@10.80.80.20 "cd /opt/greiner-portal && git add -A && git commit -m 'chore: Sync TAG[X] - [Kurzbeschreibung]'"
```

## Diagnose-Befehle

```bash
# Celery Worker Status
sudo systemctl status celery-worker

# Celery Beat Status (Scheduler)
sudo systemctl status celery-beat

# Flower Dashboard (Web-UI für Celery)
# http://10.80.80.20:5555

# Redis Status (Message Broker)
redis-cli ping

# PostgreSQL DRIVE Portal
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -c "\\dt"

# PostgreSQL Locosoft
PGPASSWORD=loco psql -h 10.80.80.8 -U loco_auswertung_benutzer -d loco_auswertung_db -c "SELECT 1"
```

## Besonderheiten

- **Static-Version Cache-Busting:** `STATIC_VERSION` in app.py ändern bei CSS/JS-Updates
- **Sync-Pfad:** `/mnt/greiner-portal-sync/` (NICHT `/mnt/greiner-sync/`)
- **rsync:** Immer `--exclude '.git'` verwenden
- **Gunicorn:** 4 sync workers, 120s timeout
- **DB_TYPE:** `postgresql` in `/opt/greiner-portal/config/.env`
- **HybridRow:** Unterstützt `row[0]` (Index) UND `row['name']` (Dict) Zugriff

## PostgreSQL Migration (TAG 135-139)

SQLite wurde vollständig auf PostgreSQL migriert:
- SQLite-Datei archiviert unter `/opt/greiner-portal/data/backups/`
- Alte Doku: `docs/archiv/DB_SCHEMA_SQLITE_ARCHIVED.md`
- Neue Doku: `docs/DB_SCHEMA_POSTGRESQL.md`

### SQL-Unterschiede beachten:
| SQLite | PostgreSQL |
|--------|------------|
| `?` | `%s` |
| `date('now')` | `CURRENT_DATE` |
| `datetime('now')` | `NOW()` |
| `= 1` (boolean) | `= true` |
| `strftime('%Y', col)` | `EXTRACT(YEAR FROM col)` |
| `AUTOINCREMENT` | `SERIAL` |
