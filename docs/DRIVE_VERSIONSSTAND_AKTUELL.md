# DRIVE Portal – Versionsstand (Kurzüberblick)

**Stand:** 2026-02-20  
**Zweck:** Prägnanter Snapshot für detaillierte Analyse (z. B. claude.ai).

---

## Version & Umgebung

| | |
|---|---|
| **Branch** | `feature/tag112-onwards` (ahead 8) |
| **Server** | 10.80.80.20 (auto-greiner.de) |
| **Portal-URL (intern)** | http://drive |
| **Projektpfad** | `/opt/greiner-portal/` |
| **Sync (Windows)** | `\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\` → Server: `/mnt/greiner-portal-sync/` |

---

## Tech-Stack

- **Backend:** Flask 3.0, Gunicorn (4 Workers)
- **Frontend:** Jinja2, Bootstrap 5, Chart.js
- **Auth:** LDAP/AD, Flask-Login, feature-basierte Rechte
- **DB:** PostgreSQL (drive_portal, 127.0.0.1), ~161 Tabellen
- **Extern read-only:** Locosoft PostgreSQL (10.80.80.8)
- **Jobs:** Celery + Redis, Flower :5555

---

## Wichtige Module (aktuell)

- **Controlling:** BWA, TEK, Bankenspiegel, AfA Vorführwagen/Mietwagen, OPOS, Kontenmapping, Zins-Optimierung
- **Verkauf:** Auftragseingang, Verkäufer-Zielplanung, Provisionsmodul (Live-Preview, Vorlauf, Dashboard)
- **Urlaub:** Urlaubsplaner, Genehmigung, Outlook-Kalender (drive@ + Mitarbeiter-Kalender)
- **Werkstatt:** Stempeluhr, Gudat, Serviceberater, Unfall-Rechnungsprüfung (M1/M4), **Fahrzeuganlage** (Fahrzeugschein-OCR via **AWS Bedrock/Claude**)
- **Integrations:** WhatsApp (Twilio, Polling), eAutoSeller, Microsoft Graph (Mail)
- **Admin/HR:** Mitarbeiterverwaltung, Rechteverwaltung, Organigramm, Navigation (DB-basiert)

---

## SSOT-Regel

- Jede Kennzahl/Berechnung hat **eine** Quelle (z. B. TEK: `api/controlling_data.py` – `get_tek_data`, `berechne_breakeven_prognose`). Keine parallelen Berechnungen.

---

## KI (Claude/Bedrock)

- **Aktiv:** Fahrzeuganlage (Fahrzeugschein-OCR, eu-central-1).
- **Analyse weiterer Einsatzstellen:** `docs/workstreams/integrations/KI_CLAUDE_BEDROCK_ANWENDUNGSANALYSE.md` (Unfall-Gutachten, Bankenspiegel, WhatsApp, Einkaufsfinanzierung, BWA-Erklärung etc.).

---

## Relevante Doku im Repo

| | |
|---|---|
| Architektur / Deployment | `CLAUDE.md` |
| DB-Schema | `docs/DB_SCHEMA_POSTGRESQL.md` |
| Workstream-Kontext | `docs/workstreams/<workstream>/CONTEXT.md` |
| Navigation (DB) | `api/navigation_utils.py`, Tabelle `navigation_items` |

---

*Dieses Dokument ist absichtlich kurz gehalten; für Code-Arbeit CLAUDE.md und jeweilige CONTEXT.md der Workstreams nutzen.*
