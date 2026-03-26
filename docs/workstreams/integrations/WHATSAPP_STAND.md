# WhatsApp-Integration — Aktueller Stand

**Stand:** 2026-02-12  
**Workstream:** integrations  
**Referenz:** TAG 211 (Twilio WhatsApp Business API)

---

## Bisherige Entwicklung (Kontext)

| Phase | Inhalt |
|-------|--------|
| **TAG 211** | Twilio WhatsApp Business API angebunden: Senden (Text/Bild/Dokument), Webhook für eingehende Nachrichten und Status-Updates, DB-Tabellen (`whatsapp_contacts`, `whatsapp_messages`, …), Views. |
| **Verkauf** | Chat-UI für Verkäufer: Kontaktliste, Nachrichtenverlauf, Senden, Locosoft-Adressbuch für „Neuer Chat“, Polling (5 s) für neue Nachrichten. Berechtigung `whatsapp_verkauf`. |
| **Teile** | Nachrichten- und Kontaktlisten unter After Sales, Berechtigung `whatsapp_teile`. Celery-Task `send_whatsapp_message` für asynchrones Senden. |
| **Sicherheit** | Webhook als Risiko bewertet (öffentlicher Inbound). Alternative: **Polling** — Celery holt Nachrichten per Twilio REST-API (nur ausgehende Verbindungen). |
| **Umstellung 2026-02-12** | Twilio Sandbox: „When a message comes in“ und „Status callback URL“ geleert. Server: `WHATSAPP_USE_POLLING_INSTEAD_OF_WEBHOOK=true` in `config/.env`, Celery-Task `fetch_whatsapp_inbound_polling` alle 2 Min. Webhook antwortet mit 404. |

**Aktueller Betrieb:** Inbound ausschließlich über Polling (kein Webhook-Endpoint in Nutzung). Senden unverändert über Twilio API.

---

## Kurzüberblick

| Bereich | Status | Beschreibung |
|--------|--------|--------------|
| **API (Twilio)** | ✅ Implementiert | `api/whatsapp_api.py` — Text, Bild, Dokument, Teile-Channel optional |
| **Webhook** | 🔒 Deaktiviert (Polling) | Bei Polling antwortet `/whatsapp/webhook` mit 404; Inbound über `fetch_whatsapp_inbound_polling` |
| **Verkauf-Chat** | ✅ Implementiert | Chat-UI für Verkäufer, Locosoft-Adressbuch, Polling |
| **Teile-UI** | ✅ Basis | Nachrichten/Kontakte unter After Sales (whatsapp_teile) |
| **Celery** | ✅ Task vorhanden | `send_whatsapp_message` (text/image) |
| **DB** | ✅ Tabellen/Views | contacts, messages, conversations, parts_requests, Views |
| **Konfiguration** | ✅ Gesetzt | TWILIO_* in `config/.env`; `WHATSAPP_USE_POLLING_INSTEAD_OF_WEBHOOK=true`; Twilio Webhook-URL leer |
| **Teile-Automatik** | ❌ Offen | Keine automatische Teile-Anfrage-Erkennung/Antwort |
| **Dokumentation** | ✅ Vorhanden | docs/WHATSAPP_*.md, TWILIO_*.md, LOCOSOFT_ADDRESSBOOK |

---

## Implementiert (fertig / in Nutzung)

### 1. API-Layer (`api/whatsapp_api.py`)
- **WhatsAppClient:** Twilio-Client für Text, Bild, Dokument
- **Konfiguration:** `get_whatsapp_config()` — TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER, TWILIO_WEBHOOK_URL
- **WhatsAppTeileClient:** optionale separate Nummer via TWILIO_WHATSAPP_NUMBER_TEILE
- **Hilfsfunktionen:** `normalize_phone_number`, `format_phone_number_for_display`, Telefonformatierung für Twilio

### 2. Routes (`routes/whatsapp_routes.py`)
- **Webhook:** `POST /whatsapp/webhook` — Twilio-Signatur, Request-Limit 1MB, Status-Updates + eingehende Nachrichten → DB
- **Webhook-Test:** `GET/POST /whatsapp/webhook/test` — lokales Testen ohne Signatur
- **Send-API:** `POST /whatsapp/send` — Nachricht senden (JSON: to, message, type, ggf. image_url/caption)
- **UI:** `/whatsapp/messages`, `/whatsapp/contacts` — Listen (nutzen `v_whatsapp_messages_with_contact`)
- **Verkauf:**  
  - `GET /whatsapp/verkauf/chat` — Chat-Seite  
  - `GET /whatsapp/verkauf/chats` — Chat-Liste (mit Fallback wenn contact_type/assigned_user_id fehlen)  
  - `GET /whatsapp/verkauf/messages/<contact_id>` — Verlauf  
  - `POST /whatsapp/verkauf/send` — Senden  
  - `GET /whatsapp/verkauf/updates` — Polling (contact_id, last_message_id)  
  - `GET /whatsapp/verkauf/locosoft-addressbook` — Kunden-Suche (Locosoft)  
  - `POST /whatsapp/verkauf/contact` — Neuer Chat (Kontakt anlegen)

### 3. Berechtigungen (`config/roles_config.py`)
- **whatsapp_teile:** admin, lager, werkstatt_leitung, service_leitung, serviceberater → Menü „WhatsApp Teile“ (After Sales) → `/whatsapp/messages`
- **whatsapp_verkauf:** admin, verkauf_leitung, verkauf → Menü „WhatsApp Chat“ (Verkauf) → `/whatsapp/verkauf/chat`

### 4. Templates
- `templates/whatsapp/verkauf_chat.html` — Verkäufer-Chat (Kontakte links, Chat rechts, Locosoft „Neuer Chat“, Polling 5s)
- `templates/whatsapp/messages.html` — Nachrichten-Liste (Teile)
- `templates/whatsapp/contacts.html` — Kontakte (Teile)

### 5. Celery
- **Senden:** `send_whatsapp_message(to, message, message_type='text', image_url=None, caption=None)` — speichert ausgehende Nachricht in `whatsapp_messages`.
- **Inbound (Polling):** `fetch_whatsapp_inbound_polling` — alle **30 Sekunden** (nur wenn `WHATSAPP_USE_POLLING_INSTEAD_OF_WEBHOOK=true`), ruft Twilio API ab, speichert neue Nachrichten über `api.whatsapp_inbound.process_inbound_message`. Im DRIVE Task Manager (Admin → Celery) unter **Integrationen** manuell startbar.

### 6. Datenbank (PostgreSQL drive_portal)
- **Tabellen:**  
  - `whatsapp_contacts` (workshop_name, phone_number, contact_name, active; optional: contact_type, assigned_user_id via Migration TAG211)  
  - `whatsapp_messages` (contact_id, message_id, direction, message_type, content, media_url, caption, status, created_at; optional: user_id, channel_type)  
  - `whatsapp_conversations` (contact_id, user_id, channel_type, last_message_id, last_message_at, unread_count) — Migration add_whatsapp_verkauf_support_tag211  
  - `whatsapp_parts_requests` (message_id, part_number, status, …)
- **Views:**  
  - `v_whatsapp_messages_with_contact`  
  - `v_whatsapp_parts_requests_full`  
  - `v_whatsapp_verkauf_chats`, `v_whatsapp_verkauf_messages` (Migration)
- **Migrations:** `migrations/add_whatsapp_tables_tag211.sql`, `migrations/add_whatsapp_verkauf_support_tag211.sql`

### 7. Inbound & Locosoft
- Eingehende Nachrichten: werden von **Polling-Task** (oder früher Webhook) in `whatsapp_contacts` / `whatsapp_messages` gespeichert; optional Abgleich mit Locosoft-Kunden (`match_customer_by_phone`) für Anzeigenamen.

---

## Wie geht's weiter – funktional werden

**Ziel:** WhatsApp im Alltag nutzbar (Verkauf + ggf. Teile), stabil und nachvollziehbar.

### Priorität 1: Betrieb absichern (kurzfristig)
1. **Polling testen** — Nachricht von Handy an Sandbox senden, im Portal „WhatsApp Chat“ (Verkauf) prüfen, ob sie innerhalb von ~2 Min erscheint.
2. **Senden testen** — Im Verkauf-Chat eine Antwort schreiben und prüfen, ob sie beim Kunden ankommt.
3. **Celery im Blick behalten** — Sicherstellen, dass `celery-worker` und `celery-beat` laufen; bei Ausfall kommen keine neuen Inbound-Nachrichten an. Optional: Monitoring/Alarm bei Task-Fehlern.

### Priorität 2: Nutzung Verkauf (sofort möglich)
- Verkäufer mit Berechtigung `whatsapp_verkauf`: Menü **Verkauf → WhatsApp Chat**.
- „Neuer Chat“: Kunde aus Locosoft-Adressbuch suchen (oder Nummer eingeben), dann schreiben.
- Bestehende Chats: links Kontakt wählen, rechts Verlauf + Antworten. Polling alle 5 s für neue Nachrichten.
- Keine weiteren Code-Änderungen nötig für Basis-Nutzung.

### Priorität 3: Teile-Bereich (After Sales)
- Nutzer mit `whatsapp_teile`: Menü **After Sales → WhatsApp Teile** → Nachrichten / Kontakte.
- Hier vor allem: Nutzung mit Kollegen durchsprechen, ob die Listen ausreichen oder Anpassungen (Filter, Suche, Zuordnung zu Aufträgen) gewünscht sind.

### Priorität 4: Optional – Erweiterungen
- **Automatische Antwort** auf erste eingehende Nachricht (z. B. „Wir haben Ihre Nachricht erhalten.“).
- **Teile-Anfrage erkennen:** Nachrichtentext parsen (z. B. Teile-Nummer), in `whatsapp_parts_requests` eintragen, ggf. Antwort mit Lagerstand (später).
- **Status-Updates** für gesendete Nachrichten (delivered/read): aktuell nur bei Webhook; bei reinem Polling optional eigenen Abgleich mit Twilio API („Message Status“) einbauen.

### Nächster konkreter Schritt
- **Empfehlung:** Priorität 1 durchspielen (Inbound + Senden + Celery), dann Verkauf für 1–2 Nutzer freigeben und Feedback sammeln. Danach Priorität 3 (Teile) und 4 (Automatik) je nach Bedarf.

---

## Produktionsbetrieb (Stand nach erfolgreichem Test)

### Option A: Sandbox als Produktion nutzen (aktuell)

Ihr nutzt die **Twilio WhatsApp-Sandbox** dauerhaft. Technisch ist das bereits „Produktion“ (echter Server, Polling, DB).

**Checkliste für den Alltagsbetrieb:**

| Punkt | Status / Aktion |
|-------|------------------|
| **Umgebung** | `config/.env` mit TWILIO_* und `WHATSAPP_USE_POLLING_INSTEAD_OF_WEBHOOK=true`; Celery Worker mit `EnvironmentFile` (bereits erledigt). |
| **Services** | `greiner-portal`, `celery-worker`, `celery-beat` laufen; nach Änderungen ggf. Neustart. |
| **Nutzer** | Verkäufer: Berechtigung `whatsapp_verkauf`; Teile: `whatsapp_teile`. Rollen in `config/roles_config.py` prüfen. |
| **Monitoring** | Optional: Bei Ausfall von Celery fehlt Inbound. Prüfen: `systemctl status celery-worker celery-beat` oder Alarm bei Task-Fehlern (z. B. Flower/Journalctl). |

**Hinweis:** Sandbox eignet sich nur zum Testen. Für echten Kundenverkehr (ohne Join-Code) ist die eigene WhatsApp-Business-Nummer nötig (Option B); Anleitung für Marketing: [WHATSAPP_ANLEITUNG_MARKETING.md](WHATSAPP_ANLEITUNG_MARKETING.md).

---

### Option B: Eigene WhatsApp-Business-Nummer (später)

Für „normale“ Kunden ohne Join-Code braucht ihr die **offizielle WhatsApp Business API** mit eigener Nummer (über Twilio oder Meta).

**Grobe Schritte (ohne Garantie auf aktuelle Twilio/Meta-Regeln):**

1. **Twilio:** Account von Trial auf bezahlt stellen (falls noch Trial).
2. **Meta Business:** Business-Verifizierung, dann im Meta Business Manager „WhatsApp“ → Konto anlegen, Nummer anfordern (oder bestehende Nummer migrieren).
3. **Twilio + Meta:** WhatsApp-Kanal in Twilio mit eurer genehmigten Business-Nummer verbinden.
4. **Im Portal:** In `config/.env` die neue Nummer eintragen: `TWILIO_WHATSAPP_NUMBER=whatsapp:+49...` (eure neue Geschäftsnummer). Polling bleibt; Webhook-URL in Twilio weiter leer lassen.
5. **Message Templates:** Für Nachrichten, die ihr **ohne** vorherige Kunden-Nachricht sendet („Business-Initiated“), sind von Meta genehmigte Vorlagen nötig. Bei reinem Antworten auf Kunden-Nachrichten („User-Initiated“) reicht euer jetziger Sende-Code.

Dokumentation und genaue Anforderungen: [Twilio WhatsApp](https://www.twilio.com/docs/whatsapp), [Meta WhatsApp Business](https://developers.facebook.com/docs/whatsapp).

---

**Kurz:** Sandbox nur zum Testen. Für **Produktion:** Option B (eigene Nummer); Marketing-Schritte bei Meta: [WHATSAPP_ANLEITUNG_MARKETING.md](WHATSAPP_ANLEITUNG_MARKETING.md), Twilio-Konfiguration macht die IT.

---

## Offen / Optional

- **Automatische Antworten** auf eingehende Nachrichten (z. B. Bestätigung) — in Code als TODO erwähnt
- **Teile-Anfrage erkennen und verarbeiten** — z. B. Teile-Nummer aus Text parsen, `whatsapp_parts_requests` befüllen, ggf. Antwort mit Lagerinfo
- **Webhook-URL in Produktion:** In Twilio Console auf finale URL setzen (z. B. `https://api.auto-greiner.de/whatsapp/webhook`); ohne DMZ/ngrok nur Test-Endpoint nutzbar
- **Dokumentation DB:** WhatsApp-Tabellen sind in den Migrations beschrieben; zentrales DB_SCHEMA_POSTGRESQL.md enthält sie ggf. noch nicht

---

## Konfiguration (Umgebung)

In `.env` (oder Umgebung) setzen:

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_NUMBER` (Format: `whatsapp:+49...` oder nur Nummer)
- Optional: `TWILIO_WHATSAPP_NUMBER_TEILE` für Teile-Channel
- Optional: `TWILIO_WEBHOOK_URL` (Default: `https://auto-greiner.de/whatsapp/webhook`)

In Twilio Console: Webhook-URL für eingehende Nachrichten/Status auf die öffentlich erreichbare URL zeigen lassen (z. B. `https://api.auto-greiner.de/whatsapp/webhook`).

---

## Referenz-Dokumentation im Repo

- `docs/WHATSAPP_VERKAEUFER_UMGESETZT_TAG211.md` — Verkäufer-API & Chat
- `docs/WHATSAPP_INBOUND_TEST_ANLEITUNG.md` — Inbound testen
- `docs/WHATSAPP_STAND_VOR_DMZ_TAG211.md` — Stand vor DMZ
- `docs/TWILIO_WEBHOOK_TESTING_SCHNELLSTART_TAG211.md` — Webhook mit ngrok
- `docs/LOCOSOFT_ADDRESSBOOK_ANBINDUNG.md` — Adressbuch API
