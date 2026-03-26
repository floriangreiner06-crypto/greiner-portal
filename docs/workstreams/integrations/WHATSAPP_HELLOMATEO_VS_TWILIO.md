# hellomateo vs. Twilio – Vergleich (DSGVO, Technik, Features)

**Stand:** 2026-02-13  
**Workstream:** integrations  
**Zweck:** Einschätzung für WhatsApp-Integration (Verkauf, Teile); Ergänzung zur bestehenden Twilio-Implementierung.

---

## 1. DSGVO / Datenschutz

| Kriterium | Twilio | hellomateo |
|-----------|--------|------------|
| **Anbieter-Sitz** | USA | Deutschland (Berlin, Mateo Estate GmbH) |
| **Selbstdarstellung** | DSGVO-Unterstützung, AVV, [GDPR-Seite](https://www.twilio.com/de-de/gdpr) | „100 % DSGVO-konform in Deutschland“ |
| **Datenfluss** | Greiner → Twilio (US) → Meta/WhatsApp | Greiner → hellomateo (DE) → Meta/WhatsApp |
| **Transfer-Risiko** | US-Anbieter → Schrems-II, TIA nötig | Erster Prozessor in EU; WhatsApp-Inhalt weiter über Meta |
| **AVV / Dokumentation** | Standard-AVV, Subprocessor-Liste prüfbar | Auf DACH ausgerichtet, typisch klare AVV |

---

## 2. Technik / Architektur

### 2.1 Twilio

- **Modell:** API-first – ihr baut Backend, UI, DB, Celery selbst; Twilio liefert nur WhatsApp-Transport.
- **Anbindung:** Direkt über `twilio` Python-SDK, REST; eigene Tabellen `whatsapp_*`, Routes, Celery (Polling/Senden).
- **Inbound:** Webhook oder **Polling** (Celery holt Nachrichten per REST – bei uns so umgesetzt).
- **Dokumentation:** [Twilio WhatsApp Docs](https://www.twilio.com/docs/whatsapp), Message-API, Media, Content API, Status – sehr gut auffindbar.

### 2.2 hellomateo – API (vollständig)

hellomateo stellt eine **öffentliche REST-API** mit vollständiger Dokumentation bereit.

| Aspekt | Details |
|--------|---------|
| **Dokumentation** | **https://docs.getmateo.com** (Introduction, Limits, API Reference, Recipes, Postman) |
| **Base URL** | `https://integration.getmateo.com/api/v1` |
| **Protokoll** | Nur HTTPS |
| **Authentifizierung** | `Authorization: Bearer <API_KEY>` |
| **Konzepte** | Read, Insert, Update, Upsert, Delete, Pagination, Resource Embedding |
| **Webhooks** | Setting up Webhooks, Webhook Events Reference |
| **Zusatz** | Postman Collection, Mateo Academy, Limits-Dokumentation |

**Send Message (API Reference):**

- **Endpoint:** `POST /send_message`
- **Parameter (Auszug):**
  - `from` (uuid): Channel-ID (Kanal, von dem gesendet wird)
  - `to`: Array von Empfängern mit `handle` (z. B. Telefon/WhatsApp), `contact_id`, `country_codes`, `full_name`, `external_contact_id`, `secondary_external_contact_id`
  - `text` / `html`: Nachrichteninhalt
  - `attachments`: Array von URLs (`https://` oder `media_library://`)
  - `template_id` (uuid): Message-Template
  - `send_after` (date-time): Zeitversetzter Versand
  - `reply_to_message_id` (uuid): Antwort auf eine Nachricht
  - `actions`: z. B. `quick_reply`, `call_to_action`, `list` (subtype: `url`, `phone_number`)
  - `footer`: Footer-Text
  - Für **Post** (Brief): Empfänger muss `contact_id` haben, kein `handle`
- **Response:** `conversation`, `message`, `recipients`, `actions`; u. a. `channel_type`, `status` (sent, read, scheduled, …).
- **Unterstützte Kanäle (laut Response-Schema):** `email`, `sms`, `whatsapp`, `facebook`, `instagram`, `google_business_messaging`.

**Weitere API-Bereiche (laut Doku-Struktur):**

- Kontakte (Contacts)
- Konversationen (Conversations)
- Channels
- CRUD + Upsert auf Ressourcen, Pagination, Resource Embedding
- Webhooks für Ereignisse

**Fazit Technik hellomateo:** Es handelt sich um eine **echte REST-API** mit dokumentierten Endpoints, Bearer-Auth, Webhooks und Postman-Collection. Eine Anbindung des DRIVE-Portals (z. B. Verkauf-Chat, Teile) an hellomateo wäre **technisch über deren API möglich** – dann als Client gegenüber `integration.getmateo.com`, analog zu Twilio, aber mit anderem Datenmodell (Channels, Conversations, Contacts) und ggf. Nutzung der Mateo-Inbox parallel.

---

## 3. Features (WhatsApp & Mehr)

### 3.1 Bei uns mit Twilio umgesetzt

- Senden: Text, Bild, Dokument (URL).
- Inbound: Polling, Speicherung in `whatsapp_messages` / `whatsapp_contacts`.
- UI: Verkäufer-Chat (Locosoft-Adressbuch), Teile: Nachrichten-/Kontaktlisten.
- Keine Message Templates, keine interaktiven Nachrichten, keine Status-Updates (delivered/read) im Polling-Betrieb.

### 3.2 Twilio möglich (nicht umgesetzt)

- Rich Messaging (Buttons, Listen, Cards), Content API.
- Media: Audio, Video, vCard; Message Templates (mit Meta-Freigabe); Webhook für Status.

### 3.3 hellomateo (Plattform + API)

| Bereich | Inhalt |
|--------|--------|
| **WhatsApp** | Postfach, Versand, Newsletter, Journeys; API: `POST /send_message` mit Channel, Kontakt/Handle, Text/HTML, Anhängen, Templates, Actions. |
| **Automatisierung** | Journeys (Termin, Geburtstag, Bewertung, Reaktivierung). |
| **KI / Chatbot** | KI-Assistent für Anfragen. |
| **Multi-Channel** | WhatsApp, E-Mail, Brief, Telefon, Instagram, Facebook, Google Business Messaging (in API-Response erwähnt). |
| **API** | Senden, Kontakte, Konversationen, Channels, Webhooks, Upsert, Pagination – **Integration ins DRIVE-Portal technisch möglich.** |
| **Branche** | U. a. Autohäuser (z. B. TÜV-Erinnerungen). |

---

## 4. Vergleichstabelle Technik/API

| Kriterium | Twilio | hellomateo |
|-----------|--------|------------|
| **API-Typ** | REST, Python-SDK | REST, Bearer Token |
| **Dokumentation** | Sehr gut, öffentlich | Vollständig unter docs.getmateo.com |
| **Send Message** | `client.messages.create()` (Twilio-Format) | `POST /send_message` (Channel, to, text/html, attachments, actions) |
| **Inbound** | Webhook oder Polling (REST) | Webhooks (Events Reference); Polling ob per API möglich – ggf. anfragen |
| **Kontakte/Konversationen** | Eigene DB (whatsapp_contacts, …) | API-Ressourcen (contacts, conversations) |
| **Multi-Channel** | Nur WhatsApp (über Twilio) | WhatsApp, E-Mail, SMS, Facebook, Instagram, GBM in einer API |
| **Interaktive Nachrichten** | Content API (bei uns nicht genutzt) | `actions` (quick_reply, call_to_action, list) im Send-Request |

---

## 5. Kurz-Fazit

- **DSGVO:** hellomateo mit DE-Sitz und klarer DSGVO-Ausrichtung; Twilio mit AVV und ggf. Transfer-Bewertung nutzbar.
- **Technik:** Beide bieten eine **vollwertige API**. Twilio ist bei uns bereits angebunden; hellomateo hat eine dokumentierte REST-API (docs.getmateo.com) mit Send Message, Kontakten, Konversationen, Webhooks und Postman – eine DRIVE-Integration wäre technisch machbar.
- **Features:** Twilio = solide Basis + optionale Erweiterungen durch Eigenentwicklung; hellomateo = Plattform mit Journeys, KI, Multi-Channel plus API für eigene Anwendungen.

---

## Referenzen

- Twilio WhatsApp: https://www.twilio.com/docs/whatsapp  
- hellomateo API: https://docs.getmateo.com (Introduction, API Reference, Webhooks, Limits, Postman)  
- hellomateo Produkt: https://www.hellomateo.de  
