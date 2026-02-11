# HR & Personal — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-11

## Beschreibung

HR umfasst Organigramm, Jahresprämie, Mitarbeiterverwaltung und AD-basierte Teamstruktur. Zukünftig eigener Navigationspunkt im Portal.

## Module & Dateien

### APIs
- `api/organization_api.py` — Organigramm, Abteilungen
- `api/jahrespraemie_api.py` — Jahresprämie
- `api/employee_management_api.py`, `api/employee_sync_service.py` — Mitarbeiterverwaltung

### Templates
- `templates/organigramm.html`
- `templates/jahrespraemie/*.html`
- `templates/admin/mitarbeiterverwaltung*.html`

### Celery Tasks
- `sync_employees`, `sync_locosoft_employees`, `sync_ad_departments`

## DB-Tabellen (PostgreSQL drive_portal)

- `employees`, `departments`

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ Organigramm, Jahresprämie, Mitarbeiterverwaltung im Einsatz
- 🔧 Eigenes HR-Menü / Navigationspunkt geplant
- ❌ Offene Punkte ggf. in Session-TODOs

## Offene Entscheidungen

- (Keine festgehalten)

## Abhängigkeiten

- auth-ldap (AD-Sync, Rollen), urlaubsplaner (Mitarbeiter-Stammdaten), Infrastruktur (Celery)
