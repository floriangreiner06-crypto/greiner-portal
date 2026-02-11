# Infrastruktur & DevOps — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-11

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
- `greiner-portal`, `celery-worker`, `celery-beat`, `flower`, `redis-server`, `metabase`

## DB-Tabellen (PostgreSQL drive_portal)

- Alle Anwendungs-Tabellen; Backup/Schema in `docs/DB_SCHEMA_POSTGRESQL.md`

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ PostgreSQL-Migration (TAG 135), Celery, Redis, Flower, Metabase, Admin-UI im Einsatz
- 🔧 MCP, Locosoft-Mirror, Backups je nach Projektstand
- ❌ Offene Punkte ggf. in Session-TODOs

## Offene Entscheidungen

- (Keine festgehalten)

## Abhängigkeiten

- Keine (Basis für andere Workstreams)
