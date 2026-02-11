# Auth & LDAP — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-11

## Beschreibung

Auth umfasst LDAP/AD-Integration, RBAC, Session-Management, Rollen-Config, Dashboard-Personalisierung, Rechte-Verwaltung und Portal-Name-Survey.

## Module & Dateien

### Auth
- `auth/auth_manager.py` — Session, Berechtigungen
- `auth/ldap_connector.py` — LDAP/AD-Anbindung

### Config
- `config/roles_config.py` — Rollen-Definition

### Decorators
- `decorators/auth_decorators.py` — Zugriffskontrollen

### Templates
- `templates/admin/rechte_verwaltung*.html`
- `templates/admin/user_dashboard_config*.html`

### Rollen
- `admin`, `finance`, `sales`, `hr`, `manager`, `employee`

## DB-Tabellen (PostgreSQL drive_portal)

- `users`, `ldap_employee_mapping` (und ggf. rollenbezogene Tabellen)

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ LDAP-Login, Rollen, RBAC, Rechte-Verwaltung im Einsatz
- 🔧 Dashboard-Personalisierung je nach Projektstand
- ❌ Offene Punkte ggf. in Session-TODOs

## Offene Entscheidungen

- (Keine festgehalten)

## Abhängigkeiten

- Infrastruktur (App-Start), HR (Mitarbeiter-Mapping)
