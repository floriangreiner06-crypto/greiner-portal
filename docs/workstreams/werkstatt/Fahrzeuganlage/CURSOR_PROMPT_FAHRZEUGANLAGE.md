# CURSOR PROMPT: DRIVE Fahrzeuganlage – Phase 1 MVP

## Kontext

DRIVE Portal – internes ERP für Autohaus Greiner. Flask auf Linux (10.80.80.20), PostgreSQL + Locosoft, LDAP-Auth, Bootstrap 4/jQuery.

Modul **Fahrzeuganlage:** Fahrzeugschein (ZB1) fotografieren → KI-OCR (AWS Bedrock, Claude, eu-central-1) → editierbare Maske → Copy nach Locosoft.

## Implementierungs-Stand

- Scanner: `api/fahrzeugschein_scanner.py`
- API: `api/fahrzeuganlage_api.py` (PostgreSQL drive_portal, nicht SQLite)
- Route: `/werkstatt/fahrzeuganlage` (in werkstatt_routes integriert)
- Navigation: DB-Migration unter Service → Werkstatt
- Feature: `fahrzeuganlage` in roles_config (aftersales-Rollen)

Siehe auch FAHRZEUGANLAGE_UMSETZBARKEITSPLAN_v2.md und FAHRZEUGANLAGE_VORSCHLAG_WEITERGEHEN.md im Werkstatt-Ordner.
