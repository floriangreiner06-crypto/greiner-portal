# Infrastruktur & DevOps — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-03-26

## Beschreibung

Infrastruktur umfasst Celery/RedBeat, Redis, Deployment, Locosoft-Mirror, PostgreSQL (Haupt-DB seit TAG 135), SQLite (Legacy), Metabase, Git, Systemd-Services, Flower, MCP-Server, DB-Backup und Admin-UI. **Haupt-DB ist seit TAG 135 PostgreSQL (drive_portal auf 127.0.0.1).**

## Module & Dateien

### Celery
- `celery_app/__init__.py`, `celery_app/tasks.py`, `celery_app/routes.py`, `celery_app/celery_config.py`

### Scripts
- `scripts/sync/locosoft_mirror.py`
- `scripts/mcp/server.py`

### APIs / Admin
- `api/admin_api.py` — Admin-UI, Task-Manager
- `api/mail_api.py` — Mail-Versand

### Templates
- `templates/admin/*.html`

### Celery Tasks (Auswahl)
- `locosoft_mirror`, `db_backup`, `cleanup_backups`, `email_daily_logins`

### Services
- `greiner-portal` (Produktion, Port 5000)
- `greiner-test` (Develop, Port 5001, nginx auf 5002)
- `celery-worker`, `celery-beat`, `flower`, `redis-server`, `metabase`

### Develop-Umgebung (seit 2026-03-26)
- **Pfad:** `/opt/greiner-test/` — Git-Clone, Branch `develop`
- **URL:** `drive:5002`
- **DB:** Gleiche wie Produktion (drive_portal) — bewusst geteilt fuer Redesign
- **Workflow:** develop → cherry-pick/merge → main → restart greiner-portal
- **Sudoers:** NOPASSWD fuer greiner-portal UND greiner-test in `/etc/sudoers.d/zzz-greiner-portal`

## DB-Tabellen (PostgreSQL drive_portal)

- Alle Anwendungs-Tabellen; Backup/Schema in `docs/DB_SCHEMA_POSTGRESQL.md`

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ PostgreSQL-Migration (TAG 135), Celery, Redis, Flower, Metabase, Admin-UI im Einsatz
- ✅ Qualitätscheck Phase 1 (Ruff, Bandit, pip-audit, Checkliste CONTEXT/SSOT); 2 Bandit-High behoben (siehe docs/QUALITAETSCHECK_*.md)
- 🔧 MCP, Locosoft-Mirror, Backups je nach Projektstand
- ❌ Offene Punkte ggf. in Session-TODOs

## Offene Entscheidungen

- (Keine festgehalten)

## Abhängigkeiten

- Keine (Basis für andere Workstreams)
