# WhatsApp-Integration mit MessengerPeople

**TAG:** 211  
**Datum:** 2026-01-26  
**Status:** ✅ **Auf MessengerPeople umgestellt**

---

## 📋 Übersicht

WhatsApp-Integration für Teile-Handelsgeschäft über **MessengerPeople API**.

**Vorteile:**
- ✅ Einheitliche Lösung (bereits im Einsatz)
- ✅ Professioneller Support
- ✅ Multi-Channel (WhatsApp, Instagram, Telegram, etc.)
- ✅ Vereinfachtes Setup

---

## 🔧 Konfiguration

### Environment-Variablen in `.env`

Füge folgende Variablen in `/opt/greiner-portal/config/.env` hinzu:

```bash
# MessengerPeople API (TAG 211)
MESSENGERPEOPLE_API_URL=https://rest.messengerpeople.com/api/v17
MESSENGERPEOPLE_API_KEY=DEIN_API_KEY
MESSENGERPEOPLE_CHANNEL_ID=DEINE_CHANNEL_ID
MESSENGERPEOPLE_WEBHOOK_TOKEN=webhook_verify_token_change_me
MESSENGERPEOPLE_WEBHOOK_URL=https://auto-greiner.de/whatsapp/webhook
```

**Benötigte Zugangsdaten:**
1. **API Key** - OAuth Token von MessengerPeople
2. **Channel ID** - WhatsApp Channel ID von MessengerPeople
3. **Webhook Token** - Beliebiger String für Webhook-Verifizierung

---

## 🗄️ Datenbank-Migration

Migration ausführen (falls noch nicht geschehen):

```bash
cd /opt/greiner-portal
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -f migrations/add_whatsapp_tables_tag211.sql
```

---

## 🔗 Webhook konfigurieren

### In MessengerPeople Dashboard:

1. **Webhook URL:** `https://auto-greiner.de/whatsapp/webhook`
2. **Verify Token:** Gleicher Wert wie `MESSENGERPEOPLE_WEBHOOK_TOKEN` in `.env`
3. **Events abonnieren:**
   - `message` (Eingehende Nachrichten)
   - `status` (Status-Updates)

---

## 🚀 Verwendung

### API-Endpoints

#### Nachricht senden

```bash
POST /whatsapp/send
Content-Type: application/json

{
    "to": "491234567890",
    "message": "Hallo, wir haben das Teil auf Lager.",
    "type": "text"
}
```

#### Bild senden

```bash
POST /whatsapp/send
Content-Type: application/json

{
    "to": "491234567890",
    "type": "image",
    "image_url": "https://example.com/image.jpg",
    "caption": "Hier ist das Teil"
}
```

### UI-Endpoints

- `/whatsapp/messages` - Nachrichten-Liste
- `/whatsapp/contacts` - Kontakte verwalten

### Celery-Task (async)

```python
from celery_app.tasks import send_whatsapp_message

# Async senden
send_whatsapp_message.delay(
    to="491234567890",
    message="Hallo!",
    message_type="text"
)
```

---

## 📝 Telefonnummer-Format

**Wichtig:** Telefonnummern müssen im internationalen Format sein (ohne +):

- ✅ `491234567890` (Deutschland)
- ❌ `+49 123 4567890`
- ❌ `00491234567890`

Die API normalisiert automatisch.

---

## 🔍 Webhook-Verifizierung

MessengerPeople sendet GET-Request zur Verifizierung:

```
GET /whatsapp/webhook?token=DEIN_TOKEN&challenge=CHALLENGE_STRING
```

Die Route prüft automatisch den `token` und gibt `challenge` zurück.

---

## 🐛 Troubleshooting

### Nachrichten werden nicht gesendet

1. **API Key prüfen:** Gültig und nicht abgelaufen?
2. **Channel ID prüfen:** Korrekt in `.env`?
3. **Telefonnummer-Format:** Internationales Format ohne `+`?

### Eingehende Nachrichten werden nicht verarbeitet

1. **Webhook abonniert?** In MessengerPeople Dashboard prüfen
2. **Webhook-URL erreichbar?** HTTPS und öffentlich?
3. **Logs prüfen:**
   ```bash
   journalctl -u greiner-portal -f | grep whatsapp
   ```

---

## 📊 API-Struktur (MessengerPeople)

### Senden von Nachrichten

**Endpoint:** `POST https://rest.messengerpeople.com/api/v17/messages`

**Request:**
```json
{
    "sender": "channel-id",
    "recipient": "491234567890",
    "payload": {
        "type": "text",
        "text": "Nachrichtentext"
    }
}
```

**Response:**
```json
{
    "id": "message-id",
    "status": "sent"
}
```

### Webhook-Events

**Eingehende Nachricht:**
```json
{
    "type": "message",
    "id": "message-id",
    "sender": "491234567890",
    "payload": {
        "type": "text",
        "text": "Nachrichtentext"
    }
}
```

**Status-Update:**
```json
{
    "type": "status",
    "id": "message-id",
    "status": "delivered"
}
```

---

## 🔐 Sicherheit

- ✅ Webhook-Verifizierung (Token)
- ✅ Login-Required für UI-Endpoints
- ✅ API Key in `.env` (nicht im Code!)
- ⚠️ **HTTPS erforderlich** für Webhooks

---

## 📚 Weitere Informationen

- **MessengerPeople API Docs:** https://rest.messengerpeople.com/docs/v17/
- **MessengerPeople Dashboard:** https://www.messengerpeople.dev/

---

## ✅ Nächste Schritte

1. **Zugangsdaten von MessengerPeople besorgen:**
   - API Key
   - Channel ID
2. **Konfiguration in `.env` setzen**
3. **Webhook in MessengerPeople Dashboard konfigurieren**
4. **Service neustarten:**
   ```bash
   sudo systemctl restart greiner-portal
   ```
5. **Test-Nachricht senden**

---

**Status:** ✅ Auf MessengerPeople umgestellt  
**Nächste TAG:** 212 (Integration mit Teile-Handel, automatische Antworten)
