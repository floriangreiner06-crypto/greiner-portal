# Externe Integrationen — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-20 (KI-Analyse, Versionsstand-Doc, .cursorrules Markdown-Sync)

## Beschreibung

Integrationen umfassen WhatsApp Business API, eAutoSeller API, ecoDMS, FinTS/HBCI, Microsoft Graph (Mail), Locosoft SOAP, Stellantis ServiceBox und Hyundai CCC/GWMS.

## Module & Dateien

### APIs
- `api/whatsapp_api.py` — WhatsApp Business API (Twilio)
- `api/eautoseller_api.py` — eAutoSeller API
- `api/mail_api.py` — Mail (Microsoft Graph)
- `api/graph_mail_connector.py` — Graph-Connector
- `api/locosoft_addressbook_api.py` — Kunden-Suche für WhatsApp Verkauf

### Tools
- `tools/locosoft_soap_client.py`
- `tools/scrapers/*.py` — ServiceBox, Hyundai, Leasys etc.

### Templates
- `templates/whatsapp/verkauf_chat.html` — Verkäufer-Chat
- `templates/whatsapp/messages.html`, `templates/whatsapp/contacts.html` — Teile-Bereich

### Celery Tasks
- `send_whatsapp_message`, `fetch_whatsapp_inbound_polling` (WhatsApp), `sync_eautoseller_data`

## DB-Tabellen (PostgreSQL drive_portal)

- **WhatsApp:** `whatsapp_contacts`, `whatsapp_messages`, `whatsapp_conversations`, `whatsapp_parts_requests`; Views: `v_whatsapp_messages_with_contact`, `v_whatsapp_verkauf_chats`, `v_whatsapp_verkauf_messages`, `v_whatsapp_parts_requests_full`
- Weitere Integrationen: je nach Modul (z. B. eAutoSeller-Cache)

---

## WhatsApp-Integration — Stand (TAG 211)

**Detaillierter Stand:** siehe [WHATSAPP_STAND.md](WHATSAPP_STAND.md) in diesem Ordner.

### Kurzfassung
- **Implementiert:** Twilio-API (Text/Bild/Dokument), **Inbound per Polling** (kein Webhook in Nutzung), Verkäufer-Chat-UI inkl. Locosoft-Adressbuch, Teile-UI (Nachrichten/Kontakte), Celery `send_whatsapp_message` + `fetch_whatsapp_inbound_polling`, DB und Berechtigungen.
- **Konfiguration:** TWILIO_* in `config/.env`; `WHATSAPP_USE_POLLING_INSTEAD_OF_WEBHOOK=true`; Twilio Sandbox-Webhook-URL leer.
- **Migration zu hellomateo:** Geplant. Vollständiger Plan: [WHATSAPP_MIGRATION_HELLOMATEO.md](WHATSAPP_MIGRATION_HELLOMATEO.md) (Phase 0–4, Code-Checkliste).
- **Nächste Schritte (funktional):** Siehe [WHATSAPP_STAND.md → Wie geht's weiter](WHATSAPP_STAND.md#wie-gehts-weiter--funktional-werden): Polling/Senden testen, Verkauf freigeben, Teile-Nutzung klären, optionale Automatik.
- **Produktionsbetrieb:** [WHATSAPP_STAND.md → Produktionsbetrieb](WHATSAPP_STAND.md#produktionsbetrieb-stand-nach-erfolgreichem-test): Option A (Sandbox nur Test) vs. Option B (eigene Nummer).
- **Anleitung Marketing (Brigitte):** [WHATSAPP_ANLEITUNG_MARKETING.md](WHATSAPP_ANLEITUNG_MARKETING.md) — Schritte bei Meta (Verifizierung, WABA, Nummer); bei hellomateo-Migration macht hellomateo/IT die Anbindung.

### Wichtige Dateien
- API: `api/whatsapp_api.py`, `api/whatsapp_inbound.py` (gemeinsame Inbound-Verarbeitung)
- Routes: `routes/whatsapp_routes.py`
- Migrations: `migrations/add_whatsapp_tables_tag211.sql`, `migrations/add_whatsapp_verkauf_support_tag211.sql`

### Alternative ohne Webhook (für IT-Sicherheit)
- **Polling:** Kein öffentlicher Endpoint; Celery holt Nachrichten per Twilio REST-API (nur ausgehende Verbindungen).
- Aktivierung: `WHATSAPP_USE_POLLING_INSTEAD_OF_WEBHOOK=true`; dann antwortet `/whatsapp/webhook` mit 404.
- Doku: [WHATSAPP_ALTERNATIVE_OHNE_WEBHOOK.md](WHATSAPP_ALTERNATIVE_OHNE_WEBHOOK.md)

---

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ eAutoSeller, Mail, Locosoft SOAP, Scraper in Nutzung
- ✅ **WhatsApp:** Kern fertig; Inbound per Polling (Webhook deaktiviert). Offen: Betriebstests, Teile-Automatik, optionale Auto-Antworten (siehe WHATSAPP_STAND.md)
- ✅ **KI-Analyse (2026-02-20):** [KI_CLAUDE_BEDROCK_ANWENDUNGSANALYSE.md](KI_CLAUDE_BEDROCK_ANWENDUNGSANALYSE.md) – Bewertung aller DRIVE-Features auf Claude/Bedrock-Mehrwert (Unfall-Gutachten, Bankenspiegel, WhatsApp, Einkaufsfinanzierung, BWA-Erklärung, AfA/DATEV, Werkstatt text_line). Einkaufsfinanzierung und BWA als eigene Abschnitte ergänzt.
- ✅ **DRIVE_VERSIONSSTAND_AKTUELL.md** im Projektdocs + Regel in .cursorrules: .md aus docs/ automatisch ins Windows-Sync kopieren (gleicher Pfad unter /mnt/greiner-portal-sync/docs/).
- 🔧 ecoDMS, FinTS je nach Projektstand
- ❌ Offene Punkte ggf. in Session-TODOs

## KI (Claude/Bedrock) in DRIVE

- **Fahrzeuganlage:** Claude via AWS Bedrock (eu-central-1) für Fahrzeugschein-OCR bereits aktiv (Werkstatt-Modul).
- **Analyse weiterer Einsatzstellen:** [KI_CLAUDE_BEDROCK_ANWENDUNGSANALYSE.md](KI_CLAUDE_BEDROCK_ANWENDUNGSANALYSE.md) – Bewertung aller DRIVE-Features auf KI-Mehrwert (Unfall-Gutachten, Bankenspiegel-Kategorisierung, WhatsApp Verkauf/Teile, DATEV/AfA, Werkstatt text_line, Urlaub/Planung); keine Code-Änderungen, nur Analyse.

## Offene Entscheidungen

- **WhatsApp-Migration:** Umstellung von Twilio auf hellomateo beschlossen. Migrationsplan: [WHATSAPP_MIGRATION_HELLOMATEO.md](WHATSAPP_MIGRATION_HELLOMATEO.md)

## Abhängigkeiten

- Infrastruktur (Celery), auth-ldap (API-Zugriff)
