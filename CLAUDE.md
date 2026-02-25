# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Arbeitsumgebung

**Server:** 10.80.80.20 (auto-greiner.de)
**Interne Portal-URL:** http://drive (nicht 10.80.80.20:5000 oder auto-greiner.de für internen Zugriff)
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

### Agent-Arbeitsweise: Migrationen und Neustarts selbst ausführen
- **Migrationen:** Wenn der Agent eine neue oder geänderte SQL-Migration anlegt (`migrations/*.sql`), soll er sie **selbst ausführen**:  
  `PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -f migrations/<datei>.sql`
- **Neustarts:** Nach Änderungen an Python/Backend den betroffenen Service **selbst neustarten** (z. B. `sudo systemctl restart greiner-portal` oder bei Celery-Tasks `sudo systemctl restart celery-worker celery-beat`). Nicht nur in der Doku erwähnen – den Befehl ausführen.

## Kein SQLite (verbindlich)
- **Scripts und API:** Es darf kein Code mehr sqlite3 oder data/greiner_controlling.db verwenden. Alle Zugriffe auf die Portal-Datenbank ausschließlich über `api.db_connection.get_db()` bzw. `api.db_utils.db_session()`. Locosoft weiterhin über `api.db_utils.get_locosoft_connection()`.
- **Hintergrund:** Haupt-DB ist seit TAG 135 PostgreSQL; Scripts die in SQLite schrieben, haben die App nicht gefüttert. Details: docs/NO_SQLITE.md, docs/SQLITE_VERWEISE_AUDIT.md.

## SSOT (Single Source of Truth) – gilt für alle Workstreams

- **Immer SSOT für alle KPIs und alle Berechnungen:** Jede Kennzahl und jede fachliche Berechnung hat genau eine Quelle (eine Funktion, ein Modul). Alle Nutzer (Portal, PDF, E-Mail, Scripts, Reports) beziehen daraus – es gibt keine parallele oder abweichende Berechnung für dieselbe Kennzahl.
- **Immer auf eine SSOT bauen:** Berechnungen, Konfigurationen und fachliche Logik nur an einer Stelle definieren; bei neuen Anforderungen zuerst prüfen, ob bereits eine passende SSOT existiert – nicht parallel neu implementieren.
- **TEK (Tägliche Erfolgskontrolle):** SSOT für alle TEK-KPIs (Umsatz, Einsatz, DB1, Marge, Prognose, Breakeven, Werktage) ist `api/controlling_data.py` (`get_tek_data`, `berechne_breakeven_prognose`). **4-Lohn-Einsatz:** Vereinbart ist der **rollierende 6-Monats-Schnitt** (Einsatz_aktuell = Umsatz_aktuell × (Einsatz_6M / Umsatz_6M)); diese Logik lebt in `get_tek_data`. Portal und alle Reports müssen dieselbe Quelle nutzen – keine eigene Aggregation in den Routes.

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
| Base Template | `templates/base.html` (Fallback-Navigation, wenn USE_DB_NAVIGATION=false) |
| DB-Navigation | `api/navigation_utils.py`, Tabelle `navigation_items` (siehe unten) |
| Auth-System | `auth/auth_manager.py` |
| LDAP-Connector | `auth/ldap_connector.py` |
| DB-Connection | `api/db_connection.py` (PostgreSQL + HybridRow) |
| DB-Schema | `docs/DB_SCHEMA_POSTGRESQL.md` |
| Locosoft-Schema | `docs/DB_SCHEMA_LOCOSOFT.md` |

## WORKSTREAM-DOKUMENTATION

### Arbeitskontext laden:
Wenn Florian einen Workstream nennt, lies:
`docs/workstreams/{workstream}/CONTEXT.md`

### Verfügbare Workstreams:
| Workstream | Pfad | Scope |
|------------|------|-------|
| Controlling | docs/workstreams/controlling/ | BWA, Bankenspiegel, TEK, Finanzreporting, MT940 |
| Werkstatt | docs/workstreams/werkstatt/ | Stempeluhr, ML, Gudat, Serviceberater, Garantie |
| Verkauf | docs/workstreams/verkauf/ | Auftragseingang, Profitabilität, Gewinnplanung, eAutoSeller |
| Teile & Lager | docs/workstreams/teile-lager/ | Bestellungen, Renner/Penner, MOBIS, Scraper |
| Urlaubsplaner | docs/workstreams/urlaubsplaner/ | Urlaubsanträge, Genehmigung, Outlook-Kalender |
| HR & Personal | docs/workstreams/hr/ | Organigramm, Jahresprämie, Mitarbeiterverwaltung |
| Planung | docs/workstreams/planung/ | Budget, Unternehmensplan, KST-Ziele |
| Finanzierungen | docs/workstreams/fahrzeugfinanzierungen/ | Zinsen, Santander, Leasys |
| Infrastruktur | docs/workstreams/infrastruktur/ | Celery, PostgreSQL, Redis, Deployment, MCP |
| Auth/LDAP | docs/workstreams/auth-ldap/ | Login, Rollen, RBAC |
| Integrations | docs/workstreams/integrations/ | WhatsApp, eAutoSeller, SOAP, Scraper, Mail |
| Marketing | docs/workstreams/marketing/ | Kampagnen, Kundenkommunikation, WhatsApp Marketing, Leads |
| Vergütung | docs/workstreams/verguetung/ | Werkstatt-Prämien, Verkäufer-Provisionen, Jahresprämie |

### Bei Session-Ende:
1. Aktualisiere die CONTEXT.md des bearbeiteten Workstreams
2. Git commit: feat(workstream): Beschreibung

### Archiv:
Historische Session-Docs: docs/archive/sessions/

## Diagnose-Befehle

```bash
# Celery Worker Status
sudo systemctl status celery-worker

# Celery Beat Status (Scheduler)
sudo systemctl status celery-beat

# Flower Dashboard (Web-UI für Celery)
# Intern: http://drive:5555 (oder je nach Apache-Konfiguration)

# Redis Status (Message Broker)
redis-cli ping

# PostgreSQL DRIVE Portal
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -c "\\dt"

# PostgreSQL Locosoft
PGPASSWORD=loco psql -h 10.80.80.8 -U loco_auswertung_benutzer -d loco_auswertung_db -c "SELECT 1"
```

## Navigation (DB-basiert – verbindliche Regel)

**Die Menüpunkte (Navi) kommen aus der Datenbank, nicht aus dem Template.**

- **Quelle:** Tabelle **`navigation_items`** (PostgreSQL). Die Menüleiste wird aus dieser Tabelle geladen, sobald `USE_DB_NAVIGATION=true` (config/.env) – was in Produktion der Fall ist.
- **Navi-Punkte sind nicht in base.html hardcoden.** Neue Einträge werden ausschließlich über die DB angelegt (Migration + ggf. `migrate_navigation_items.py`). In `base.html` steht nur Fallback-Code für den Fall, dass keine DB-Navigation geladen wird.

**Neue Menüpunkte so anlegen:**

1. **Migration anlegen:** z. B. `migrations/add_navigation_<name>.sql` mit `INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, role_restriction, ...)` – `parent_id` = ID des übergeordneten Menüpunkts (z. B. Controlling); `requires_feature` und `role_restriction` steuern die Sichtbarkeit.
2. **Migration ausführen:** `PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -f migrations/add_navigation_<name>.sql`
3. **Optional:** `scripts/migrate_navigation_items.py` um den Eintrag ergänzen (für Neuaufbau der DB).

Referenz: `migrations/add_navigation_verkaeufer_zielplanung.sql`, `migrations/add_navigation_opos.sql`, `migrations/migration_tag211_whatsapp_navigation.sql`. Filterlogik: `api/navigation_utils.py` (Feature + Rolle).

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
