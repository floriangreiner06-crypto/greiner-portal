# WhatsApp-Migration: Twilio → hellomateo

**Stand:** 2026-02-13  
**Workstream:** integrations  
**Ziel:** Bestehende WhatsApp-Integration (Verkauf, Teile) von Twilio auf hellomateo umstellen.

---

## Übersicht: Was heute läuft

| Komponente | Aktuell (Twilio) |
|------------|------------------|
| **Senden** | `api/whatsapp_api.py` → `WhatsAppClient` (Text, Bild, Dokument) |
| **Inbound** | Celery `fetch_whatsapp_inbound_polling` holt Nachrichten per Twilio REST-API (Polling) |
| **Speicherung** | PostgreSQL: `whatsapp_contacts`, `whatsapp_messages`, `whatsapp_conversations`, Views |
| **UI** | Verkauf: `/whatsapp/verkauf/chat` (Locosoft-Adressbuch, Chats). Teile: `/whatsapp/messages`, `/whatsapp/contacts` |
| **Config** | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`, `WHATSAPP_USE_POLLING_INSTEAD_OF_WEBHOOK` |

Die **DB und die UI** bleiben erhalten; nur der **Transport** (Twilio) wird durch hellomateo ersetzt.

---

## Phase 0: Voraussetzungen (ohne Code)

### 0.1 hellomateo-Account und WhatsApp-Kanal

- [ ] **Account** bei hellomateo anlegen (z. B. über [hellomateo.de](https://www.hellomateo.de)).
- [ ] **WhatsApp-Business-Nummer** klären:
  - Entweder bei hellomateo neue Nummer/Verbindung einrichten (Meta-Verifizierung ggf. nötig, siehe [WHATSAPP_ANLEITUNG_MARKETING.md](WHATSAPP_ANLEITUNG_MARKETING.md) für Meta-Seite),
  - oder bestehende Nummer von Twilio/Meta zu hellomateo migrieren (mit hellomateo klären).
- [ ] **Channel-ID (WhatsApp)** in hellomateo ermitteln – wird für `POST /send_message` als `from` (UUID) benötigt.
- [ ] **API-Key** in der hellomateo-Oberfläche erzeugen (Dokumentation: [docs.getmateo.com](https://docs.getmateo.com)).

### 0.2 Inbound: Webhook oder Polling

- [ ] **Klären:** Liefert hellomateo eingehende Nachrichten nur per **Webhook**, oder gibt es eine **API zum Abrufen** (z. B. „list messages“ / „list conversations“)?
  - **Webhook:** Wir müssen einen **öffentlich erreichbaren Endpoint** bereitstellen (z. B. `https://api.auto-greiner.de/whatsapp/webhook/mateo`), den hellomateo bei neuen Nachrichten aufruft. Signaturprüfung laut [docs.getmateo.com/webhooks](https://docs.getmateo.com/webhooks/setting-up-webhooks) einbauen.
  - **Polling/API:** Falls hellomateo eine „list messages“- oder „list conversations“-API hat, können wir den bestehenden Celery-Polling-Ansatz beibehalten (nur Aufruf von Twilio durch hellomateo ersetzen).

---

## Phase 1: Konfiguration

### 1.1 Umgebungsvariablen

In `config/.env` (oder Server-Environment):

**Neu für hellomateo:**

```bash
# hellomateo (WhatsApp)
HELLOMATEO_API_KEY=<API-Key aus hellomateo>
HELLOMATEO_CHANNEL_ID=<UUID des WhatsApp-Channels>
# Optional, Default: https://integration.getmateo.com/api/v1
HELLOMATEO_BASE_URL=https://integration.getmateo.com/api/v1
```

**Provider-Umschaltung (empfohlen für Rollback):**

```bash
# Welcher Provider: twilio | hellomateo
WHATSAPP_PROVIDER=hellomateo
```

**Twilio-Variablen** vorerst beibehalten (für Rollback):

- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`, ggf. `TWILIO_WHATSAPP_NUMBER_TEILE`

### 1.2 Keine DB-Migration nötig

Die Tabellen `whatsapp_contacts`, `whatsapp_messages`, `whatsapp_conversations` und die Views bleiben unverändert. Nur die **Quelle** der Nachrichten (Twilio vs. hellomateo) und die **Sende-API** wechseln.

---

## Phase 2: Code-Änderungen

### 2.1 Neuer hellomateo-API-Client

**Neue Datei:** `api/hellomateo_api.py` (oder `api/whatsapp_hellomateo_client.py`)

- **Funktionen:**
  - Konfiguration aus `HELLOMATEO_API_KEY`, `HELLOMATEO_CHANNEL_ID`, `HELLOMATEO_BASE_URL` lesen.
  - **Senden:** `POST {base_url}/send_message` mit Body:
    - `from`: Channel-ID (UUID)
    - `to`: Array mit z. B. `[{"handle": "491234567890", "country_codes": ["49"]}]` (Format laut [docs.getmateo.com](https://docs.getmateo.com/api-reference/send-message/send-a-message))
    - `text` oder `html`
    - `attachments`: optional für Bild/Dokument (URLs)
  - **Methoden:** `send_text_message(to, message)`, `send_image_message(to, image_url, caption=None)`, `send_document_message(to, document_url, filename, caption=None)` – gleiche Signatur wie bisheriger `WhatsAppClient`, Rückgabe z. B. `{success, message_id, error}`.
  - **Inbound (falls API vorhanden):** z. B. `fetch_inbound_messages(since)` → Liste von Nachrichten im **gleichen Format** wie Twilio (MessageSid, From, To, Body, NumMedia, MediaUrl0, MediaContentType0), damit `process_inbound_message(data)` unverändert nutzbar ist.  
    Falls hellomateo **nur Webhook** anbietet: diese Methode weglassen oder leer returnen; Inbound dann nur über Webhook.

### 2.2 Abstraktion in `api/whatsapp_api.py`

- **Option A (empfohlen):** `get_whatsapp_client()` (oder eine Factory) liefert je nach `WHATSAPP_PROVIDER`:
  - `twilio` → bestehenden `WhatsAppClient` (Twilio),
  - `hellomateo` → neuen hellomateo-Client (gleiche Methodennamen: `send_text_message`, `send_image_message`, `send_document_message`, ggf. `fetch_inbound_messages`).
- **Option B:** Twilio-Code komplett durch hellomateo ersetzen (kein Umschalt, weniger Code, aber Rollback nur durch Git/Config).

Alle Aufrufer (Routes, Celery) nutzen weiterhin **eine** Schnittstelle (z. B. `get_whatsapp_client()`), sodass nur die Implementierung wechselt.

### 2.3 Inbound-Verarbeitung

**Datei:** `api/whatsapp_inbound.py`

- **process_inbound_message(data)** erwartet aktuell ein Twilio-ähnliches Dict (`MessageSid`, `From`, `Body`, `NumMedia`, …).
- **Wenn hellomateo Webhook:** Neue Route z. B. `POST /whatsapp/webhook/mateo` empfängt den hellomateo-Payload; **Mapping** von hellomateo-Format → dieses Dict; dann `process_inbound_message(mapped_data)` aufrufen. Signaturprüfung laut hellomateo-Doku.
- **Wenn hellomateo Polling/API:** Der hellomateo-Client in `fetch_inbound_messages()` liefert bereits gemappte Dicts; `process_inbound_message(data)` bleibt unverändert.

**Datei:** `routes/whatsapp_routes.py`

- Webhook-Route für hellomateo hinzufügen (falls Webhook gewählt).
- Bestehende Twilio-Webhook-Route `/whatsapp/webhook` kann für Twilio-Rollback erhalten bleiben; bei `WHATSAPP_PROVIDER=hellomateo` wird sie nicht von hellomateo aufgerufen.

### 2.4 Celery

**Datei:** `celery_app/tasks.py`

- **send_whatsapp_message:** Statt fest `WhatsAppClient()` den gewählten Client nutzen (z. B. über `get_whatsapp_client()`). Rest (DB-Schreiblogik für ausgehende Nachrichten) unverändert.
- **fetch_whatsapp_inbound_polling:**
  - Wenn hellomateo eine **Abruf-API** hat: Client auf hellomateo umstellen, gleiche `process_inbound_message(data)`-Aufrufe.
  - Wenn **nur Webhook:** Task deaktivieren (z. B. nur ausführen wenn `WHATSAPP_PROVIDER=twilio`) oder entfernen; Inbound läuft ausschließlich über hellomateo-Webhook.

**Datei:** `celery_app/__init__.py` (Beat-Schedule)

- `fetch-whatsapp-inbound-polling` nur noch ausführen, wenn Inbound per Polling (hellomateo mit API) oder weiter Twilio. Bei reiner Webhook-Nutzung mit hellomateo: Task aus dem Schedule nehmen.

### 2.5 Abhängigkeiten

- **Twilio:** `pip install twilio` – kann vorerst bleiben (für Rollback). Später entfernen, wenn nur noch hellomateo genutzt wird.
- **hellomateo:** Nur `requests` (HTTP) nötig; kein separates SDK.

---

## Phase 3: Inbound-Strategie (konkret)

| Szenario | Aktion |
|----------|--------|
| **hellomateo bietet „list messages“ / „list conversations“** | Neuer Client implementiert `fetch_inbound_messages(since)`; Celery-Polling-Task ruft hellomateo-API auf und übergibt gemappte Daten an `process_inbound_message`. Kein öffentlicher Webhook nötig. |
| **hellomateo nur Webhook** | Öffentlich erreichbarer Endpoint (z. B. hinter Apache): `POST /whatsapp/webhook/mateo`. Payload von hellomateo → in Twilio-ähnliches Format mappen → `process_inbound_message(mapped_data)`. Webhook-URL in hellomateo eintragen. Celery-Polling für WhatsApp deaktivieren. |

---

## Phase 4: Test und Cutover

### 4.1 Tests (mit hellomateo aktiv)

- [ ] **Senden (Verkauf):** Im Portal „WhatsApp Chat“ eine Nachricht an eine Test-Nummer senden → Erfolg in hellomateo und in DB.
- [ ] **Senden (Teile):** Nachricht über Teile-UI oder Celery-Task `send_whatsapp_message` → Erfolg.
- [ ] **Inbound:** Entweder Test-Nachricht an eure Nummer senden und im Portal prüfen (Webhook oder Polling), oder hellomateo-Test-Webhook auslösen.

### 4.2 Cutover

- [ ] `WHATSAPP_PROVIDER=hellomateo` setzen (bzw. Twilio-Config auskommentieren, wenn keine Abstraktion).
- [ ] Services neu starten: `sudo systemctl restart greiner-portal`, `sudo systemctl restart celery-worker celery-beat`.
- [ ] Kurz Verkauf/Teile im Alltag beobachten.

### 4.3 Rollback

- [ ] `WHATSAPP_PROVIDER=twilio` setzen (oder Twilio-Config wieder aktivieren).
- [ ] Services neu starten.
- [ ] Twilio-Sandbox/eigene Nummer weiterhin nutzbar, sofern nicht gekündigt.

---

## Checkliste: Betroffene Dateien

| Datei | Aktion |
|-------|--------|
| `config/.env` | Neue Variablen: `HELLOMATEO_API_KEY`, `HELLOMATEO_CHANNEL_ID`, `WHATSAPP_PROVIDER` |
| `api/hellomateo_api.py` | **Neu:** Client für Send + ggf. fetch_inbound (REST-Calls zu docs.getmateo.com) |
| `api/whatsapp_api.py` | Abstraktion: `get_whatsapp_client()` je nach Provider; oder komplett durch hellomateo ersetzen |
| `api/whatsapp_inbound.py` | Unverändert, wenn Daten ins bestehende Format gemappt werden |
| `routes/whatsapp_routes.py` | Webhook-Route für hellomateo (falls Webhook); Senden/Routes nutzen gemeinsamen Client |
| `celery_app/tasks.py` | `send_whatsapp_message` + `fetch_whatsapp_inbound_polling` nutzen gewählten Client |
| `celery_app/__init__.py` | Beat: Polling-Task nur bei Polling-Betrieb aktiv |
| `requirements.txt` | Optional: `twilio` später entfernen |

---

## Referenzen

- hellomateo API: https://docs.getmateo.com  
- Vergleich Twilio vs. hellomateo: [WHATSAPP_HELLOMATEO_VS_TWILIO.md](WHATSAPP_HELLOMATEO_VS_TWILIO.md)  
- Aktueller WhatsApp-Stand (Twilio): [WHATSAPP_STAND.md](WHATSAPP_STAND.md)
