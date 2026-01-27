# Websms/LINK Mobility WhatsApp API - Detaillierte Analyse

**TAG:** 211  
**Datum:** 2026-01-26  
**Status:** 📊 **ANALYSE ABGESCHLOSSEN - Bereits Kunde!**

---

## 🎯 SITUATION

**Wichtig:** Ihr seid bereits Websms/LINK Mobility Kunde! ✅

**Vorteile:**
- ✅ **Keine neue Registrierung** - Bereits Kunde
- ✅ **Bekanntes System** - Team kennt sich aus
- ✅ **Deutscher Anbieter** - Support auf Deutsch
- ✅ **WhatsApp API verfügbar** - Vollständig dokumentiert

---

## 📋 API-STRUKTUR (aus OpenAPI Spec)

### **Base URLs:**
```
https://api.linkmobility.eu/
https://api.websms.com/
```

### **Authentifizierung:**
- **Methode:** Bearer Token (Access Token)
- **Header:** `Authorization: Bearer YOUR_ACCESS_TOKEN`
- **Oder:** Query Parameter `?access_token=ACCESS_TOKEN_VALUE`
- **Token:** Wird im Messaging Portal generiert

### **Endpoint: Send Message**

**URL:**
```
POST /rest/channels/{uuid}/send/whatsapp
```

**Request-Struktur:**
```json
{
  "recipientAddressList": ["4369912345678"],
  "messageContent": {
    "type": "text",
    "text": {
      "body": "Nachrichtentext"
    }
  },
  "clientMessageId": "optional-id",
  "contentCategory": "informational",
  "priority": 5,
  "test": false,
  "validityPeriode": 300
}
```

**Response:**
```json
{
  "statusCode": 2000,
  "statusMessage": "OK",
  "transferId": "00654a6251002defc350",
  "clientMessageId": "123"
}
```

**Wichtig:**
- Channel UUID ist im Endpoint-Pfad (`{uuid}`)
- `recipientAddressList` ist Array (kann mehrere Empfänger)
- `messageContent` folgt Meta-Format

---

### **Webhook: Receive Messages**

**Struktur (Meta-Format ähnlich):**
```json
{
  "customerChannelUuid": "68fd0c25-3bd7-4b03-8234-0cf112439bb8",
  "sender": "4369912345678",
  "recipient": "4369912345679",
  "type": "whatsapp",
  "whatsappNotification": {
    "object": "whatsapp_business_account",
    "entry": [{
      "changes": [{
        "value": {
          "metadata": {
            "display_phone_number": "+4369912345679"
          },
          "messages": [{
            "from": "+4369912345678",
            "timestamp": "1701878004",
            "text": {
              "body": "test"
            },
            "type": "text"
          }],
          "messaging_product": "whatsapp"
        },
        "field": "messages"
      }]
    }]
  }
}
```

**Status-Update:**
```json
{
  "customerChannelUuid": "68fd0c25-3bd7-4b03-8234-0cf112439bb8",
  "sender": "4369912345678",
  "recipient": "4369912345679",
  "transferId": "0065709970004e2a559d",
  "type": "whatsapp",
  "whatsappNotification": {
    "object": "whatsapp_business_account",
    "entry": [{
      "changes": [{
        "value": {
          "statuses": [{
            "id": "d568b5e4-8a2b-4559-ad5a-f0e85885fd99",
            "status": "delivered",
            "timestamp": "1701878134",
            "recipient_id": "4369912345678"
          }]
        }
      }]
    }]
  }
}
```

---

## 🔍 UNTERSCHIEDE ZU MESSENGERPEOPLE

### **Request-Struktur:**

**MessengerPeople:**
```json
{
  "sender": "channel-id",
  "recipient": "491234567890",
  "payload": {
    "type": "text",
    "text": "Nachricht"
  }
}
```

**Websms/LINK Mobility:**
```json
{
  "recipientAddressList": ["4369912345678"],
  "messageContent": {
    "type": "text",
    "text": {
      "body": "Nachricht"
    }
  }
}
```

**Hauptunterschiede:**
- ✅ **Channel UUID im Endpoint-Pfad** - Nicht im Body
- ✅ **recipientAddressList** - Array statt einzelner String
- ✅ **messageContent** - Statt `payload`
- ✅ **Bearer Token** - Gleiche Auth-Methode

---

### **Webhook-Struktur:**

**MessengerPeople:**
```json
{
  "type": "message",
  "id": "message-id",
  "sender": "491234567890",
  "payload": {
    "type": "text",
    "text": "Nachricht"
  }
}
```

**Websms/LINK Mobility:**
```json
{
  "customerChannelUuid": "uuid",
  "sender": "4369912345678",
  "whatsappNotification": {
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "+4369912345678",
            "text": {"body": "test"},
            "type": "text"
          }]
        }
      }]
    }]
  }
}
```

**Hauptunterschiede:**
- ⚠️ **Meta-Format** - Verschachtelter (entry → changes → value → messages)
- ⚠️ **customerChannelUuid** - Zusätzliches Feld
- ⚠️ **Komplexere Struktur** - Mehr Ebenen

---

## 💡 CODE-ANPASSUNG

### **Geschätzter Aufwand:**

**Minimal (Basis-Funktionen):**
- API-Client anpassen: **4-6 Stunden**
- Webhook-Struktur anpassen: **3-4 Stunden**
- Testing: **2-3 Stunden**
- **Gesamt: ~9-13 Stunden**

**Vollständig (alle Features):**
- API-Client komplett: **6-8 Stunden**
- Webhook-Handler: **4-5 Stunden**
- Error-Handling: **2-3 Stunden**
- Testing: **3-4 Stunden**
- **Gesamt: ~15-20 Stunden**

---

## 🔧 TECHNISCHE HERAUSFORDERUNGEN

### **1. Channel UUID im Endpoint-Pfad** ⚠️ **NIEDRIG**

**Problem:**
- Channel UUID ist im URL-Pfad: `/rest/channels/{uuid}/send/whatsapp`
- Nicht im Request-Body

**Lösung:**
- Channel UUID in Config speichern
- Im Endpoint-Pfad verwenden

**Aufwand:** +30 Minuten

---

### **2. recipientAddressList (Array)** ⚠️ **NIEDRIG**

**Problem:**
- `recipientAddressList` ist Array, nicht einzelner String
- Kann mehrere Empfänger enthalten

**Lösung:**
- Array erstellen: `[phone_number]`
- Funktioniert auch für einzelne Empfänger

**Aufwand:** +15 Minuten

---

### **3. messageContent statt payload** ⚠️ **NIEDRIG**

**Problem:**
- Feld heißt `messageContent` statt `payload`
- Struktur ist ähnlich

**Lösung:**
- Feld umbenennen
- Struktur bleibt ähnlich

**Aufwand:** +30 Minuten

---

### **4. Webhook Meta-Format** ⚠️ **MITTEL**

**Problem:**
- Verschachtelte Struktur: `whatsappNotification.entry[0].changes[0].value.messages[0]`
- Ähnlich wie Meta API, aber mit zusätzlichen Feldern

**Lösung:**
- Webhook-Parser implementieren
- Meta-Format parsen
- `customerChannelUuid` für Filterung nutzen

**Aufwand:** +2-3 Stunden

---

## 📊 VERGLEICH: MessengerPeople vs. Websms

| Feature | MessengerPeople | Websms/LINK Mobility |
|---------|----------------|---------------------|
| **Base URL** | `rest.messengerpeople.com/api/v17` | `api.linkmobility.eu` oder `api.websms.com` |
| **Auth** | Bearer Token | Bearer Token ✅ |
| **Endpoint** | `/messages` | `/rest/channels/{uuid}/send/whatsapp` |
| **Channel ID** | Im Body (`sender`) | Im Endpoint-Pfad (`{uuid}`) |
| **Recipient** | String | Array (`recipientAddressList`) |
| **Message** | `payload` | `messageContent` |
| **Webhook** | Einfach | Meta-Format (verschachtelt) |
| **Format** | Eigene Struktur | Meta-Format |

---

## 🎯 CODE-ANPASSUNG PLAN

### **1. API-Client (`api/whatsapp_api.py`)**

**Änderungen:**
1. Base URL ändern
2. Endpoint-Pfad anpassen (Channel UUID im Pfad)
3. Request-Struktur anpassen (`recipientAddressList`, `messageContent`)
4. Response-Parsing anpassen

**Geschätzt:** 4-6 Stunden

---

### **2. Webhook (`routes/whatsapp_routes.py`)**

**Änderungen:**
1. Webhook-Struktur anpassen (Meta-Format parsen)
2. `customerChannelUuid` für Filterung nutzen
3. `whatsappNotification.entry[0].changes[0].value` parsen
4. Status-Updates anpassen

**Geschätzt:** 3-4 Stunden

---

### **3. Konfiguration**

**Neue Environment-Variablen:**
```bash
WEBSMS_API_URL=https://api.linkmobility.eu
WEBSMS_ACCESS_TOKEN=DEIN_ACCESS_TOKEN
WEBSMS_CHANNEL_UUID=DEINE_CHANNEL_UUID
WEBSMS_WEBHOOK_URL=https://auto-greiner.de/whatsapp/webhook
```

---

## 📋 WAS ICH BRAUCHE

### **1. API-Credentials:**
- [ ] Access Token (aus Messaging Portal)
- [ ] Channel UUID (für Teile-Channel)
- [ ] API-URL (`api.linkmobility.eu` oder `api.websms.com`)

### **2. WhatsApp Channel:**
- [ ] Channel erstellt?
- [ ] Telefonnummer verifiziert?
- [ ] Channel aktiviert?

### **3. Webhook:**
- [ ] Webhook-URL konfiguriert?
- [ ] Events abonniert?

---

## 🚀 NÄCHSTE SCHRITTE

### **Sofort (du):**

1. **Messaging Portal öffnen:**
   - https://app.linkmobility.eu/ ODER https://app.websms.com/
   - Login mit bestehendem Account

2. **WhatsApp Channel prüfen/erstellen:**
   - Prüfen ob WhatsApp Channel vorhanden
   - Falls nicht: Channel erstellen
   - Channel UUID notieren

3. **Access Token generieren:**
   - Im Messaging Portal
   - API-Zugang prüfen
   - Access Token generieren/notieren

4. **Webhook konfigurieren:**
   - Webhook-URL: `https://auto-greiner.de/whatsapp/webhook`
   - Events: Incoming messages, Status updates

### **Dann (ich):**

1. **Code anpassen** (9-13 Stunden)
2. **Testing** (2-3 Stunden)
3. **Dokumentation** (1 Stunde)

---

## 💡 VORTEILE WEBSMS

1. ✅ **Bereits Kunde** - Keine neue Registrierung
2. ✅ **Deutscher Anbieter** - Support auf Deutsch
3. ✅ **Bekanntes System** - Team kennt sich aus
4. ✅ **Meta-Format** - Standardisiert, gut dokumentiert
5. ✅ **Multiple Channels** - Separate Nummern möglich
6. ✅ **Omnichannel** - SMS + WhatsApp + RCS

---

**Status:** 📊 Analyse abgeschlossen  
**Vorteil:** Bereits Kunde - keine neue Registrierung nötig!  
**Aufwand:** ~9-13 Stunden (minimal) bis ~15-20 Stunden (vollständig)  
**Nächster Schritt:** WhatsApp Channel prüfen/erstellen und Access Token generieren
