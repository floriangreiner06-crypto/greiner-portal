# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Arbeitsumgebung

**Server:** 10.80.80.20 (auto-greiner.de)
**SSH User:** ag-admin
**VS Code / Claude Code:** Verbindet sich per SSH direkt auf den Server und editiert Dateien dort.

### Umgebungen

| Umgebung | URL | Pfad | Git-Branch | Datenbank |
|----------|-----|------|------------|-----------|
| Produktion | http://drive | /opt/greiner-portal/ | main | drive_portal |
| Develop | http://drive:5002 | /opt/greiner-test/ | develop | drive_portal_dev |

## Server ist Master

- **Der Server ist die einzige Quelle der Wahrheit.** Es gibt keine Windows-Sync-Architektur mehr.
- Dateien werden direkt auf dem Server editiert (via SSH / Claude Code / VS Code Remote).
- Deployment erfolgt ausschliesslich per Git (kein cp, kein rsync von Windows-Pfaden).
- Kein Bezug auf `/mnt/greiner-portal-sync/` oder Windows-SMB-Pfade.

## Sudo-Konfiguration (NOPASSWD)

Fur ag-admin sind NOPASSWD-Regeln in `/etc/sudoers.d/greiner-portal` hinterlegt.
**Kein Passwort im Klartext verwenden!** Stattdessen immer vollen Pfad + `-n` Flag:

```bash
sudo -n /usr/bin/systemctl restart greiner-portal   # RICHTIG
sudo -n /usr/bin/systemctl status greiner-portal     # RICHTIG
sudo -n /usr/bin/journalctl -u greiner-portal -f     # RICHTIG
# FALSCH: echo 'password' | sudo -S systemctl ...
# FALSCH: sudo systemctl ... (ohne -n und vollen Pfad)
```

Erlaubte Befehle ohne Passwort: systemctl (start/stop/restart/status) fur greiner-portal, greiner-test, celery-worker, celery-beat, flower, metabase; journalctl.

## Git-Workflow

### Branch-Strategie

```
main        ──────────────────────────────────────>  Produktion (/opt/greiner-portal/)
               \                         /
develop     ────\───────────────────────/──────────>  Develop (/opt/greiner-test/)
                 \                     /
feature/*   ──────\───────────────────/              Feature-Branches (kurzlebig)
```

### Regeln

| Regel | Detail |
|-------|--------|
| main = Produktion | Nur stabile, getestete Anderungen landen auf main |
| develop = Testumgebung | Neue Features zuerst auf develop mergen und testen |
| feature/* | Werden von develop abgezweigt, nach Test in develop gemergt |
| Hotfixes | Direkt auf main (mit sofortigem Backmerge in develop) |
| Kein force-push main | Nie `git push --force` auf main |

### Normaler Deploy-Workflow

```bash
# 1. Feature-Branch von develop
git checkout develop && git pull
git checkout -b feature/mein-feature

# 2. Entwickeln, committen
git add <dateien>
git commit -m "feat(bereich): beschreibung"

# 3. In develop mergen + Develop-Dienst neustarten
git checkout develop && git merge feature/mein-feature
sudo -n /usr/bin/systemctl restart greiner-test

# 4. Nach Test: in main mergen + Produktion neustarten
git checkout main && git merge develop
sudo -n /usr/bin/systemctl restart greiner-portal
```

### Hotfix-Workflow

```bash
git checkout main
git checkout -b hotfix/beschreibung
# Fix...
git commit -m "fix(bereich): beschreibung"
git checkout main && git merge hotfix/beschreibung
sudo -n /usr/bin/systemctl restart greiner-portal
# Backmerge in develop
git checkout develop && git merge main
```

## Agent-Arbeitsweise

- **Migrationen:** Wenn der Agent eine neue oder geanderte SQL-Migration anlegt (`migrations/*.sql`), soll er sie **selbst auf beiden Datenbanken ausfuhren**:
  ```bash
  PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -f migrations/<datei>.sql
  PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev -f migrations/<datei>.sql
  ```
- **Neustarts:** Nach Anderungen an Python/Backend den betroffenen Service **selbst neustarten** (z. B. `sudo -n /usr/bin/systemctl restart greiner-portal` oder bei Celery-Tasks `sudo -n /usr/bin/systemctl restart celery-worker celery-beat`). Nicht nur in der Doku erwahnen - den Befehl ausfuhren.
- **Templates brauchen KEINEN Neustart** - nur Browser-Refresh (Strg+F5).

## Kein SQLite (verbindlich)

- **Scripts und API:** Es darf kein Code mehr sqlite3 oder data/greiner_controlling.db verwenden. Alle Zugriffe auf die Portal-Datenbank ausschliesslich uber `api.db_connection.get_db()` bzw. `api.db_utils.db_session()`. Locosoft weiterhin uber `api.db_utils.get_locosoft_connection()`.
- **Hintergrund:** Haupt-DB ist seit TAG 135 PostgreSQL; Scripts die in SQLite schrieben, haben die App nicht gefuttert. Details: docs/NO_SQLITE.md, docs/SQLITE_VERWEISE_AUDIT.md.

## SSOT (Single Source of Truth) - gilt fur alle Workstreams

- **Immer SSOT fur alle KPIs und alle Berechnungen:** Jede Kennzahl und jede fachliche Berechnung hat genau eine Quelle (eine Funktion, ein Modul). Alle Nutzer (Portal, PDF, E-Mail, Scripts, Reports) beziehen daraus - es gibt keine parallele oder abweichende Berechnung fur dieselbe Kennzahl.
- **Immer auf eine SSOT bauen:** Berechnungen, Konfigurationen und fachliche Logik nur an einer Stelle definieren; bei neuen Anforderungen zuerst prufen, ob bereits eine passende SSOT existiert - nicht parallel neu implementieren.
- **TEK (Tagliche Erfolgskontrolle):** SSOT fur alle TEK-KPIs (Umsatz, Einsatz, DB1, Marge, Prognose, Breakeven, Werktage) ist `api/controlling_data.py` (`get_tek_data`, `berechne_breakeven_prognose`). **4-Lohn-Einsatz:** Vereinbart ist der **rollierende 6-Monats-Schnitt** (Einsatz_aktuell = Umsatz_aktuell x (Einsatz_6M / Umsatz_6M)); diese Logik lebt in `get_tek_data`. Portal und alle Reports mussen dieselbe Quelle nutzen - keine eigene Aggregation in den Routes.

## Architektur

### Tech-Stack

- **Backend:** Flask 3.0 + Gunicorn (4 workers)
- **Frontend:** Jinja2 + Bootstrap 5.3 + Chart.js
- **Auth:** LDAP/Active Directory via Flask-Login
- **Datenbank:** PostgreSQL (seit TAG 135)
- **Scheduler:** Celery + Redis

### Request-Flow

```
Browser -> Flask Routes (routes/) -> API-Layer (api/) -> PostgreSQL
                 |
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
3. OU-basiertes Role-Mapping (z.B. OU=Geschaftsleitung -> admin)
4. Permission-Check: `current_user.can_access_feature('modulname')`

### Job-Scheduler (Celery)

- **Task-Definitionen:** `celery_app/tasks.py`
- **Celery-Config:** `celery_app/celery_config.py`
- **Web-UI:** `/admin/celery/` (Task Manager)
- **Flower Dashboard:** Port 5555
- **Redis:** Message Broker fur Celery

## Services & Ports

| Service | Port | URL | Beschreibung |
|---------|------|-----|--------------|
| greiner-portal (Produktion) | 5000 | http://drive | Haupt-App (hinter Apache) |
| greiner-test (Develop) | 5002 | http://drive:5002 | Develop-/Testumgebung |
| Flower | 5555 | http://drive:5555 | Celery Web-UI |
| Metabase | 3001 | http://drive:3001 | BI / Auswertungen |
| Redis | 6379 | intern | Celery Message Broker |
| PostgreSQL | 5432 | 127.0.0.1:5432 | Hauptdatenbank |
| Locosoft DB | 5432 | 10.80.80.8:5432 | Locosoft (read-only) |

## Datenbanken

### PostgreSQL DRIVE Portal - Produktion

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
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -c "SELECT ..."
```

### PostgreSQL DRIVE Portal - Develop

**Host:** 127.0.0.1:5432
**Database:** drive_portal_dev
**User:** drive_user
**Password:** DrivePortal2024

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev -c "SELECT ..."
```

### PostgreSQL Locosoft (extern, read-only)

**Host:** 10.80.80.8:5432
**Database:** loco_auswertung_db
**User:** loco_auswertung_benutzer
**Password:** loco
**Schema:** `docs/DB_SCHEMA_LOCOSOFT.md`

```bash
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

## Workstream-Dokumentation

### Arbeitskontext laden

Wenn Florian einen Workstream nennt, lies:
`docs/workstreams/{workstream}/CONTEXT.md`

### Verfugbare Workstreams

| Workstream | Pfad | Scope |
|------------|------|-------|
| Controlling | docs/workstreams/controlling/ | BWA, Bankenspiegel, TEK, Finanzreporting, MT940 |
| Werkstatt | docs/workstreams/werkstatt/ | Stempeluhr, ML, Gudat, Serviceberater, Garantie |
| Verkauf | docs/workstreams/verkauf/ | Auftragseingang, Profitabilitat, Gewinnplanung, eAutoSeller |
| Teile & Lager | docs/workstreams/teile-lager/ | Bestellungen, Renner/Penner, MOBIS, Scraper |
| Urlaubsplaner | docs/workstreams/urlaubsplaner/ | Urlaubsantrage, Genehmigung, Outlook-Kalender |
| HR & Personal | docs/workstreams/hr/ | Organigramm, Jahrespraemie, Mitarbeiterverwaltung |
| Planung | docs/workstreams/planung/ | Budget, Unternehmensplan, KST-Ziele |
| Finanzierungen | docs/workstreams/fahrzeugfinanzierungen/ | Zinsen, Santander, Leasys |
| Infrastruktur | docs/workstreams/infrastruktur/ | Celery, PostgreSQL, Redis, Deployment, MCP |
| Auth/LDAP | docs/workstreams/auth-ldap/ | Login, Rollen, RBAC |
| Integrations | docs/workstreams/integrations/ | WhatsApp, eAutoSeller, SOAP, Scraper, Mail |
| Marketing | docs/workstreams/marketing/ | Kampagnen, Kundenkommunikation, WhatsApp Marketing, Leads |
| Vergutung | docs/workstreams/verguetung/ | Werkstatt-Praemien, Verkaufer-Provisionen, Jahrespraemie |

### Bei Session-Ende

1. Aktualisiere die CONTEXT.md des bearbeiteten Workstreams
2. Git commit: feat(workstream): Beschreibung

### Archiv

Historische Session-Docs: docs/archive/sessions/

## Diagnose-Befehle

```bash
# Portal-Dienste
sudo -n /usr/bin/systemctl status greiner-portal
sudo -n /usr/bin/systemctl status greiner-test
sudo -n /usr/bin/systemctl restart greiner-portal
sudo -n /usr/bin/systemctl restart greiner-test

# Celery Worker & Beat
sudo -n /usr/bin/systemctl status celery-worker
sudo -n /usr/bin/systemctl status celery-beat
sudo -n /usr/bin/systemctl restart celery-worker celery-beat

# Logs (live)
sudo -n /usr/bin/journalctl -u greiner-portal -f
sudo -n /usr/bin/journalctl -u greiner-test -f
sudo -n /usr/bin/journalctl -u celery-worker -f

# Redis Status (Message Broker)
redis-cli ping

# PostgreSQL DRIVE Portal (Produktion)
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -c "\dt"

# PostgreSQL DRIVE Portal (Develop)
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev -c "\dt"

# PostgreSQL Locosoft
PGPASSWORD=loco psql -h 10.80.80.8 -U loco_auswertung_benutzer -d loco_auswertung_db -c "SELECT 1"
```

## Navigation (DB-basiert - verbindliche Regel)

**Die Menupunkte (Navi) kommen aus der Datenbank, nicht aus dem Template.**

- **Quelle:** Tabelle **`navigation_items`** (PostgreSQL). Die Menuleiste wird aus dieser Tabelle geladen, sobald `USE_DB_NAVIGATION=true` (config/.env) - was in Produktion der Fall ist.
- **Navi-Punkte nicht in base.html hardcoden.** Neue Eintrage werden ausschliesslich uber die DB angelegt (Migration + ggf. `migrate_navigation_items.py`). In `base.html` steht nur Fallback-Code fur den Fall, dass keine DB-Navigation geladen wird.

**Neue Menupunkte so anlegen:**

1. **Migration anlegen:** z. B. `migrations/add_navigation_<name>.sql` mit `INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, role_restriction, ...)` - `parent_id` = ID des ubergeordneten Menupunkts (z. B. Controlling); `requires_feature` und `role_restriction` steuern die Sichtbarkeit.
2. **Migration ausfuhren (beide DBs):**
   ```bash
   PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -f migrations/add_navigation_<name>.sql
   PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev -f migrations/add_navigation_<name>.sql
   ```
3. **Optional:** `scripts/migrate_navigation_items.py` um den Eintrag erganzen (fur Neuaufbau der DB).

Referenz: `migrations/add_navigation_verkaeufer_zielplanung.sql`, `migrations/add_navigation_opos.sql`, `migrations/migration_tag211_whatsapp_navigation.sql`. Filterlogik: `api/navigation_utils.py` (Feature + Rolle).

## Besonderheiten

- **Static-Version Cache-Busting:** `STATIC_VERSION` in app.py andern bei CSS/JS-Updates
- **Gunicorn:** 4 sync workers, 120s timeout
- **DB_TYPE:** `postgresql` in `/opt/greiner-portal/config/.env`
- **HybridRow:** Unterstutzt `row[0]` (Index) UND `row['name']` (Dict) Zugriff
- **Git:** Kein `git push --force` auf main; kein `--no-verify`; immer auf feature/* entwickeln

## SQL-Syntax (PostgreSQL)

| Konvention | PostgreSQL |
|------------|------------|
| Platzhalter | `%s` |
| Aktuelles Datum | `CURRENT_DATE` |
| Aktuelle Zeit | `NOW()` |
| Boolean | `= true` / `= false` |
| Jahr extrahieren | `EXTRACT(YEAR FROM col)` |
| Auto-ID | `SERIAL` |
