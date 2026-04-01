# Infrastruktur & DevOps — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-03-31

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

## Aktueller Stand (erledigt, in Arbeit, offen)

- Erledigt: PostgreSQL-Migration (TAG 135), Celery, Redis, Flower, Metabase, Admin-UI im Einsatz
- Erledigt: Qualitaetscheck Phase 1 (Ruff, Bandit, pip-audit, Checkliste CONTEXT/SSOT)
- Erledigt: SSH-Zugang zu Locosoft-Server (root@10.80.80.8, Key-Auth)
- Erledigt: Locosoft Docker-Container repariert (locodb, pg_hba.conf, Passwort)
- Erledigt: Locosoft DB vollstaendig analysiert (102 Tabellen, 11.3 Mio. Datensaetze)
- In Arbeit: MCP, Locosoft-Mirror, Backups je nach Projektstand
- Offen: Locosoft Export-Performance verbessern (aktuell 44 Min Full-Export)
- Offen: Werkstatt Soll-Kapazitaet aus Locosoft (employees_worktimes + times analysiert, Datenqualitaet beachten)

## Locosoft PostgreSQL Server (srvlocodb, 10.80.80.8)

- **Docker-Container:** `locodb` (PG 16.2, Image nikoksr/postgres:latest)
- **SSH:** `ssh root@10.80.80.8` (Key-Auth von ag-admin@drive)
- **PGDATA:** `/opt/postgres-data/` (persistentes Volume, ueberlebt Container-Restart!)
- **Tuning:** shared_buffers=4GB, work_mem=64MB, maintenance_work_mem=1GB, synchronous_commit=off (via ALTER SYSTEM, persistent)
- **pg_hba.conf:** Aktuell auf `trust` (Locosoft braucht das fuer Live-Zugriff)
- **Export:** Full-Export via Pr. 987 DATENBANK-Dienst, ca. 36 Min, taeglich
- **Schemas:** `public` (Export-Daten), `private` (Live-Daten: journal_accountings, times), `app2` (App-Daten)
- **Analyse:** docs/workstreams/infrastruktur/LOCOSOFT_DB_ANALYSE_2026-03-31.md
- **Spiegel-Status:** 95 von 102 Tabellen lokal gespiegelt, Daten nahezu identisch. 7 fehlende = Modell-Konfigurator (nicht geschaeftskritisch).

### Reparatur-Historie 2026-03-31

1. Container `locodb` war gestoppt, postgres-Passwort falsch (AHG1234 vs AHG1234!)
2. Alter Container hatte tmpfs (RAM-Disk) -> alles weg bei Restart
3. Neuer Container mit persistentem Volume `/opt/postgres-data/` erstellt
4. PostgreSQL-Tuning (4GB shared_buffers etc.) angewendet
5. DB-Kopplung in Locosoft neu hergestellt (locoserversetup.exe)
6. "Drittanbietern Zugriff auf aktuelle Finanzbuchhaltung" aktiviert
7. App-Geraete-Registrierungen verloren (muessen neu registriert werden)

### Erledigt (2026-04-01)

- Live-Aktualisierung der Rechnungen funktioniert (Schluessel: "Drittanbietern Zugriff auf aktuelle Finanzbuchhaltung gestatten" in Pr. 987)
- App-Geraete neu registriert (QR-Code)
- Tagesumsatz und TEK zeigen wieder korrekte Live-Daten

## Erkenntnisse Locosoft Stempelzeiten (2026-03-31)

- `employees_worktimes` = Soll-Arbeitszeiten (vertraglich), NICHT Ist-Stempelzeiten
- `times` View: Type 1 = Anwesenheit (Kommen/Gehen), Type 2 = Auftragsstempelung (produktiv)
- Type 2 hat Duplikate pro order_position - DISTINCT auf (employee, start_time, end_time) noetig
- Locosoft kann produktive Mechaniker nicht sauber von anderen Werkstatt-MA unterscheiden (kein Flag). Mapping muss aus Portal-employees kommen.
- Datenqualitaet: Ausreisser moeglich (z.B. 80h-Anwesenheitseintrag durch Doppelbuchung)
- Produktivitaet Maerz 2026: Top-Mechaniker 93-98%, Azubis/Neue 0-10%

## Werkstatt Leistungsuebersicht - KPI-Datenquellen (2026-03-31)

Die Werkstatt-Leistungsuebersicht holt alle Daten **LIVE von Locosoft** (10.80.80.8), NICHT aus dem lokalen Spiegel.

SSOT: `api/werkstatt_data.py` -> `WerkstattData.get_mechaniker_leistung()` (Zeile 280)

Drei Locosoft-Tabellen liefern alles:
1. `times` (type=1) -> Anwesenheit (Kommen/Gehen)
2. `times` (type=2) -> Stempelzeit (Auftragsstempelungen, dedupliziert per Auftrag)
3. `labours` -> Vorgabezeit (verrechnete AW auf Rechnungen)

KPI-Formeln:
- Leistungsgrad = AW x 6 / Stempelzeit x 100 (labours.time_units / times type=2)
- Produktivitaet = Stempelzeit / Anwesenheit x 100 (times type=2 / times type=1)
- Anwesenheitsgrad = Anwesend / Bezahlt x 100 (times type=1 / employees_worktimes Soll)
- Effizienz = Leistung x Produktivitaet
- Entgangener Umsatz = Verlorene Std x Durchschnitts-Stundensatz

Berechnung nach Locosoft-Logik (TAG 185/196):
- Stempelzeit = Zeitspanne (erste bis letzte Stempelung pro Tag) minus Luecken minus Pausen
- Fallback wenn type=1 unvollstaendig: Zeitspanne aus type=2 oder Stempelzeit x 1.2

## Offene Entscheidungen

- Soll Export-Haeufigkeit reduziert werden (z.B. 1x/Woche statt taeglich)? Live-Aktualisierung ist fuer Kunden+Fahrzeuge bereits aktiv.
- Soll die Werkstatt-Produktivitaet aus Locosoft-times berechnet werden statt manuell?

## Abhaengigkeiten

- Keine (Basis fuer andere Workstreams)
