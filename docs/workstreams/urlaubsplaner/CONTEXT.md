# Urlaubsplaner — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-11

## Beschreibung

Urlaubsplaner deckt Urlaubsanträge, Genehmigungsprozess, Chef-Übersicht, Urlaubsguthaben, Feiertage, Outlook-Kalender und E-Mail-Benachrichtigungen ab.

## Module & Dateien

### APIs
- `api/vacation_api.py` — Kern-API Urlaub
- `api/vacation_chef_api.py` — Chef-Übersicht, Genehmigungen
- `api/vacation_admin_api.py` — Admin-Funktionen
- Zugehörige Services: `vacation_approver_service.py`, `vacation_calendar_service.py`, `vacation_locosoft_service.py`, `vacation_year_utils.py`

### Templates
- `templates/urlaubsplaner*.html`

## DB-Tabellen (PostgreSQL drive_portal)

- `vacation_entitlements`, `vacation_bookings`, `vacation_types`, `holidays`

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ Anträge, Genehmigung, Chef-Übersicht, Guthaben, Feiertage im Einsatz
- 🔧 Outlook-Kalender, E-Mails je nach Projektstand
- ❌ Offene Punkte ggf. in Session-TODOs

## Offene Entscheidungen

- (Keine festgehalten)

## Abhängigkeiten

- HR (Mitarbeiterstammdaten), auth-ldap (Rollen), Integrations (Microsoft Graph für Kalender/Mail)
