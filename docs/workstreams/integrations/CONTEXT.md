# Externe Integrationen — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-11

## Beschreibung

Integrationen umfassen WhatsApp Business API, eAutoSeller API, ecoDMS, FinTS/HBCI, Microsoft Graph (Mail), Locosoft SOAP, Stellantis ServiceBox und Hyundai CCC/GWMS.

## Module & Dateien

### APIs
- `api/whatsapp_api.py` — WhatsApp Business API
- `api/eautoseller_api.py` — eAutoSeller API
- `api/mail_api.py` — Mail (Microsoft Graph)
- `api/graph_mail_connector.py` — Graph-Connector

### Tools
- `tools/locosoft_soap_client.py`
- `tools/scrapers/*.py` — ServiceBox, Hyundai, Leasys etc.

### Templates
- `templates/whatsapp/*.html`

### Celery Tasks
- `send_whatsapp_message`, `sync_eautoseller_data`

## DB-Tabellen (PostgreSQL drive_portal)

- Je nach Integration (z. B. WhatsApp-Konfiguration, eAutoSeller-Cache)

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ eAutoSeller, Mail, Locosoft SOAP, Scraper in Nutzung
- 🔧 WhatsApp, ecoDMS, FinTS je nach Projektstand
- ❌ Offene Punkte ggf. in Session-TODOs

## Offene Entscheidungen

- (Keine festgehalten)

## Abhängigkeiten

- Infrastruktur (Celery), auth-ldap (API-Zugriff)
