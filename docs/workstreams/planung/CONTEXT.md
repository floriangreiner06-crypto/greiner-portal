# Planung & Unternehmenssteuerung — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-11

## Beschreibung

Planung umfasst Budget-Planung, Unternehmensplan, Kostenstellen-Ziele, Abteilungsleiter-Planung und Kundenzentrale.

## Module & Dateien

### APIs
- `api/budget_api.py`, `api/budget_data.py` — Budget
- `api/unternehmensplan_api.py`, `api/unternehmensplan_data.py` — Unternehmensplan
- `api/kst_ziele_api.py` — KST-Ziele
- `api/abteilungsleiter_planung_api.py`, `api/abteilungsleiter_planung_data.py` — Abteilungsleiter-Planung
- `api/kundenzentrale_api.py` — Kundenzentrale

### Templates
- `templates/controlling/kst_ziele*.html`
- `templates/planung/*.html`
- `templates/verkauf/budget*.html`

## DB-Tabellen (PostgreSQL drive_portal)

- `budget_plan`, `kst_ziele`

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ Budget, Unternehmensplan, KST-Ziele, Abteilungsleiter-Planung in Nutzung
- 🔧 Kundenzentrale je nach Projektstand
- ❌ Offene Punkte ggf. in Session-TODOs

## Offene Entscheidungen

- (Keine festgehalten)

## Abhängigkeiten

- Controlling (BWA/Kennzahlen), auth-ldap (Rollen)
