# WhatsApp-Integration für Teile-Handelsgeschäft

**TAG:** 211  
**Datum:** 2026-01-26  
**Status:** ✅ **Testumsetzung abgeschlossen**

---

## 📋 Übersicht

WhatsApp-Integration für Kommunikation mit externen Werkstätten im Teile-Handelsgeschäft.

**Features:**
- ✅ Textnachrichten senden/empfangen
- ✅ Bilder senden/empfangen
- ✅ Status-Tracking (gesendet, zugestellt, gelesen)
- ✅ Webhook für eingehende Nachrichten
- ✅ Kontakt-Verwaltung
- ✅ Nachrichten-Historie

---

## 🔧 Konfiguration

### 1. Meta Developer Account einrichten

1. **Account erstellen:** https://developers.facebook.com
2. **App erstellen:** Neue App → Business → WhatsApp
3. **WhatsApp Business Account verbinden**
4. **Phone Number ID notieren** (aus App Dashboard)
5. **Access Token generieren** (aus App Dashboard → WhatsApp → API Setup)

### 2. Environment-Variablen in `.env`

Füge folgende Variablen in `/opt/greiner-portal/config/.env` hinzu:

```bash
# WhatsApp Business API (TAG 211)
WHATSAPP_API_URL=https://graph.facebook.com/v18.0
WHATSAPP_PHONE_NUMBER_ID=DEINE_PHONE_NUMBER_ID
WHATSAPP_ACCESS_TOKEN=DEIN_ACCESS_TOKEN
WHATSAPP_VERIFY_TOKEN=whatsapp_verify_token_change_me
WHATSAPP_WEBHOOK_URL=https://auto-greiner.de/whatsapp/webhook
```

**Wichtig:**
- `WHATSAPP_VERIFY_TOKEN`: Beliebiger String (für Webhook-Verifizierung)
- `WHATSAPP_WEBHOOK_URL`: Öffentliche URL zu deinem Server (HTTPS erforderlich!)

### 3. Webhook konfigurieren

1. **Meta App Dashboard** → WhatsApp → Configuration
2. **Webhook URL:** `https://auto-greiner.de/whatsapp/webhook`
3. **Verify Token:** Gleicher Wert wie `WHATSAPP_VERIFY_TOKEN` in `.env`
4. **Webhook Fields:** `messages`, `message_status` abonnieren

---

## 🗄️ Datenbank-Migration

Migration ausführen:

```bash
cd /opt/greiner-portal
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -f migrations/add_whatsapp_tables_tag211.sql
```

**Erstellte Tabellen:**
- `whatsapp_contacts` - Kontakte (externe Werkstätten)
- `whatsapp_messages` - Nachrichten-Historie
- `whatsapp_parts_requests` - Teile-Anfragen (Verknüpfung)

**Views:**
- `v_whatsapp_messages_with_contact` - Nachrichten mit Kontakt-Info
- `v_whatsapp_parts_requests_full` - Teile-Anfragen mit Details

---

## 📦 Installation

### Python-Pakete installieren

```bash
cd /opt/greiner-portal
source venv/bin/activate
pip install requests --break-system-packages
```

**Hinweis:** `requests` sollte bereits in `requirements.txt` sein.

### Service neustarten

```bash
sudo systemctl restart greiner-portal
```

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

#### Nachrichten abrufen (API)

```bash
GET /whatsapp/api/messages?contact_id=1&limit=50
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

Die API normalisiert automatisch:
- Entfernt Leerzeichen, Bindestriche, Klammern
- Entfernt führendes `+` oder `00`

---

## 🔍 Webhook-Verifizierung

Meta sendet GET-Request zur Verifizierung:

```
GET /whatsapp/webhook?hub.mode=subscribe&hub.verify_token=DEIN_TOKEN&hub.challenge=CHALLENGE_STRING
```

Die Route prüft automatisch den `verify_token` und gibt `challenge` zurück.

---

## 🐛 Troubleshooting

### Webhook funktioniert nicht

1. **HTTPS erforderlich:** Meta akzeptiert nur HTTPS-Webhooks
2. **Verify Token prüfen:** Muss in `.env` und Meta Dashboard identisch sein
3. **Logs prüfen:**
   ```bash
   journalctl -u greiner-portal -f | grep whatsapp
   ```

### Nachrichten werden nicht gesendet

1. **Access Token prüfen:** Gültig und nicht abgelaufen?
2. **Phone Number ID prüfen:** Korrekt in `.env`?
3. **Telefonnummer-Format:** Internationales Format ohne `+`?

### Eingehende Nachrichten werden nicht verarbeitet

1. **Webhook abonniert?** In Meta Dashboard prüfen
2. **Webhook-URL erreichbar?** HTTPS und öffentlich?
3. **Logs prüfen:** Fehler in Webhook-Verarbeitung?

---

## 📊 Datenbank-Struktur

### whatsapp_contacts

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | SERIAL | Primary Key |
| workshop_name | VARCHAR(255) | Name der Werkstatt |
| phone_number | VARCHAR(20) | Telefonnummer (UNIQUE) |
| contact_name | VARCHAR(255) | Ansprechpartner |
| active | BOOLEAN | Aktiv? |

### whatsapp_messages

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | SERIAL | Primary Key |
| contact_id | INTEGER | FK zu whatsapp_contacts |
| message_id | VARCHAR(255) | WhatsApp Message ID (UNIQUE) |
| direction | VARCHAR(10) | 'inbound' oder 'outbound' |
| message_type | VARCHAR(20) | 'text', 'image', 'document', etc. |
| content | TEXT | Nachrichtentext |
| media_url | TEXT | URL zum Media |
| status | VARCHAR(20) | 'sent', 'delivered', 'read', 'failed' |

### whatsapp_parts_requests

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | SERIAL | Primary Key |
| message_id | INTEGER | FK zu whatsapp_messages |
| part_number | VARCHAR(100) | Teilenummer |
| part_name | VARCHAR(255) | Teilename |
| status | VARCHAR(20) | 'pending', 'quoted', 'ordered', etc. |

---

## 🔐 Sicherheit

- ✅ Webhook-Verifizierung (Verify Token)
- ✅ Login-Required für UI-Endpoints
- ✅ Access Token in `.env` (nicht im Code!)
- ⚠️ **HTTPS erforderlich** für Webhooks

---

## 📚 Weitere Informationen

- **WhatsApp Business API Docs:** https://developers.facebook.com/docs/whatsapp
- **Meta Developer Dashboard:** https://developers.facebook.com/apps

---

## ✅ Nächste Schritte

1. **Meta Developer Account einrichten**
2. **Webhook konfigurieren**
3. **Migration ausführen**
4. **Service neustarten**
5. **Test-Nachricht senden**

---

**Status:** ✅ Testumsetzung abgeschlossen  
**Nächste TAG:** 212 (Integration mit Teile-Handel, automatische Antworten)
