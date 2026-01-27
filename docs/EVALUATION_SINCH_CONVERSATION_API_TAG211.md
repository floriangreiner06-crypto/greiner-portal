# Evaluation: Sinch Conversation API

**TAG:** 211  
**Datum:** 2026-01-26  
**Status:** 📊 **EVALUATION - Keine Implementierung**

---

## 🎯 ZWECK DER EVALUATION

Bewertung von Sinch Conversation API als Alternative zu MessengerPeople für:
- WhatsApp-Integration im Teile-Bereich
- Langfristige Lösung (nach MessengerPeople-Einstellung)
- Vergleich mit bestehender MessengerPeople-Integration

---

## 📋 ÜBER SINCH CONVERSATION API

### **Was ist Sinch Conversation API?**

- **Nachfolger** von MessengerPeople API (Sinch hat MessengerPeople 2021 gekauft)
- **Unified Messaging API** - 14+ Messenger-Plattformen
- **Enterprise-fokussiert** - Für größere Unternehmen und Channel-Partner
- **API-basiert** - Programmatische Integration

### **Unterstützte Kanäle:**

- ✅ WhatsApp Business API
- ✅ SMS
- ✅ RCS
- ✅ Facebook Messenger
- ✅ Instagram
- ✅ Telegram
- ✅ Viber
- ✅ Apple iMessage
- ✅ WeChat
- ✅ Und weitere...

---

## 🔍 API-STRUKTUR ANALYSE

### **Base URL & Versionierung:**

```
https://conversation.api.sinch.com/v1/
```

**Hinweis:** Aktuelle Version ist v1, aber API ist aktiv weiterentwickelt.

### **Authentifizierung:**

**Methode:** Basic Authentication (nicht Bearer Token wie MessengerPeople)

```
Authorization: Basic base64(service_plan_id:api_token)
```

**Oder:**
```
X-Sinch-Service-Plan-ID: service_plan_id
X-Sinch-API-Token: api_token
```

**Unterschied zu MessengerPeople:**
- MessengerPeople: Bearer Token (OAuth)
- Sinch: Basic Auth (Service Plan ID + API Token)

### **Nachricht senden (WhatsApp):**

**Sinch Conversation API:**
```http
POST https://conversation.api.sinch.com/v1/projects/{project_id}/messages:send
Content-Type: application/json
Authorization: Basic base64(service_plan_id:api_token)

{
  "app_id": "app-id",
  "recipient": {
    "identified_by": {
      "channel_identities": [
        {
          "channel": "WHATSAPP",
          "identity": "491234567890"
        }
      ]
    }
  },
  "message": {
    "text_message": {
      "text": "Nachrichtentext"
    }
  },
  "channel_priority_order": ["WHATSAPP"]
}
```

**MessengerPeople (aktuell):**
```http
POST https://rest.messengerpeople.com/api/v17/messages
Authorization: Bearer api_key

{
  "sender": "channel-id",
  "recipient": "491234567890",
  "payload": {
    "type": "text",
    "text": "Nachrichtentext"
  }
}
```

**Unterschiede:**
- ✅ **Komplexere Struktur** - Mehr verschachtelt
- ✅ **App ID erforderlich** - Zusätzliche Konfiguration
- ✅ **Project-basiert** - Projekte statt direkte Channels
- ⚠️ **Mehr Parameter** - Mehr Konfiguration nötig

### **Bild senden:**

**Sinch:**
```json
{
  "message": {
    "media_message": {
      "url": "https://example.com/image.jpg",
      "caption": "Bildtext"
    }
  }
}
```

**MessengerPeople:**
```json
{
  "payload": {
    "type": "image",
    "image": {
      "link": "https://example.com/image.jpg",
      "caption": "Bildtext"
    }
  }
}
```

### **Webhook-Struktur:**

**Sinch:**
```json
{
  "app_id": "app-id",
  "accepted_time": "2026-01-26T10:00:00Z",
  "event": {
    "conversation_start_event": {...},
    "message_event": {
      "direction": "TO_APP",
      "message": {
        "text_message": {
          "text": "Nachrichtentext"
        }
      },
      "channel_identity": {
        "channel": "WHATSAPP",
        "identity": "491234567890"
      }
    }
  }
}
```

**MessengerPeople:**
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

**Unterschiede:**
- ✅ **Event-basiert** - Verschiedene Event-Typen
- ✅ **Strukturierter** - Mehr Metadaten
- ⚠️ **Komplexer** - Mehr verschachtelt

---

## 💰 PREISE & KOSTEN

### **Sinch Conversation API:**

**Pricing-Modell:**
- **Pay-per-message** - Je nach Kanal und Land
- **WhatsApp:** ~€0.005-0.09 pro Nachricht (je nach Land)
- **Volume-Discounts** - Bei höheren Volumen
- **Keine monatliche Grundgebühr** (nur Pay-per-use)

**Vergleich MessengerPeople:**
- MessengerPeople: €0.001-0.003 pro Nachricht + €19/Monat (Small Plan)
- Sinch: ~€0.005-0.09 pro Nachricht (keine Grundgebühr)

**Fazit:** Sinch ist bei niedrigen Volumen teurer, bei hohen Volumen günstiger.

---

## 🔧 TECHNISCHE BEWERTUNG

### **Vorteile:**

1. ✅ **Zukunftssicher** - Langfristig verfügbar (keine Einstellung geplant)
2. ✅ **Multi-Channel** - 14+ Messenger-Plattformen
3. ✅ **Moderne API** - Aktuellste Features
4. ✅ **Enterprise-fokussiert** - Für größere Unternehmen
5. ✅ **Gute Dokumentation** - Umfangreiche Docs verfügbar
6. ✅ **SDKs verfügbar** - Python SDK vorhanden
7. ✅ **Unified Contact Management** - Zentrale Kontaktverwaltung
8. ✅ **Smart Conversations** - AI-Features (Intent, Sentiment)

### **Nachteile:**

1. ⚠️ **Komplexere API** - Mehr verschachtelte Strukturen
2. ⚠️ **Mehr Konfiguration** - App ID, Project ID, etc.
3. ⚠️ **Code-Anpassung nötig** - Andere API-Struktur
4. ⚠️ **Teurer bei niedrigen Volumen** - Höhere Kosten pro Nachricht
5. ⚠️ **Lernkurve** - Team muss sich einarbeiten
6. ⚠️ **Migration nötig** - Bestehender Code muss angepasst werden

---

## 📊 CODE-ANPASSUNGS-AUFWAND

### **Geschätzter Aufwand:**

**Minimal (nur Basis-Funktionen):**
- API-Client anpassen: **4-6 Stunden**
- Webhook-Struktur anpassen: **2-3 Stunden**
- Konfiguration: **1 Stunde**
- **Gesamt: ~7-10 Stunden**

**Vollständig (mit allen Features):**
- API-Client komplett: **8-12 Stunden**
- Webhook-Handler: **4-6 Stunden**
- Error-Handling: **2-3 Stunden**
- Testing: **4-6 Stunden**
- Dokumentation: **2 Stunden**
- **Gesamt: ~20-29 Stunden**

### **Hauptänderungen:**

1. **API-Client (`api/whatsapp_api.py`):**
   - Authentifizierung ändern (Basic Auth statt Bearer)
   - Request-Struktur anpassen (app_id, recipient, message)
   - Response-Parsing anpassen

2. **Webhook (`routes/whatsapp_routes.py`):**
   - Event-Struktur anpassen (conversation_start_event, message_event)
   - Channel-Identity-Parsing
   - Richtung (TO_APP vs FROM_APP)

3. **Konfiguration:**
   - Service Plan ID + API Token statt API Key
   - App ID hinzufügen
   - Project ID hinzufügen

---

## 🎯 MIGRATIONS-STRATEGIE

### **Option A: Komplett-Migration (beide Channels)**

**Vorgehen:**
1. Sinch Account erstellen
2. Beide Channels (Kunden + Teile) in Sinch migrieren
3. Code komplett auf Sinch umstellen
4. Bestehenden MessengerPeople-Webhook abschalten

**Vorteile:**
- ✅ Einheitliche Lösung
- ✅ Zukunftssicher
- ✅ Keine doppelte Wartung

**Nachteile:**
- ⚠️ Höherer Aufwand
- ⚠️ Beide Systeme müssen gleichzeitig migriert werden

### **Option B: Schrittweise Migration (Teile zuerst)**

**Vorgehen:**
1. Teile-Channel direkt in Sinch erstellen
2. Code für Sinch anpassen (nur Teile)
3. Kunden-Channel später migrieren (bis 31.12.2026)

**Vorteile:**
- ✅ Weniger Risiko
- ✅ Schrittweise Migration
- ✅ Teile-Channel sofort zukunftssicher

**Nachteile:**
- ⚠️ Temporär zwei Systeme
- ⚠️ Doppelte Wartung (kurzzeitig)

---

## 📈 EINSCHÄTZUNG

### **Technische Machbarkeit:** ⭐⭐⭐⭐⭐ **SEHR GUT**

- ✅ API ist gut dokumentiert
- ✅ Python SDK verfügbar
- ✅ Ähnliche Funktionalität wie MessengerPeople
- ✅ Code-Anpassung machbar (7-29 Stunden)

### **Aufwand:** ⭐⭐⭐ **MITTEL**

- ⚠️ Code-Anpassung nötig (7-29 Stunden)
- ⚠️ Konfiguration komplexer
- ⚠️ Team-Einarbeitung nötig

### **Kosten:** ⭐⭐⭐ **MITTEL**

- ⚠️ Teurer bei niedrigen Volumen
- ✅ Günstiger bei hohen Volumen
- ✅ Keine Grundgebühr

### **Zukunftssicherheit:** ⭐⭐⭐⭐⭐ **SEHR GUT**

- ✅ Langfristig verfügbar
- ✅ Aktive Weiterentwicklung
- ✅ Keine Einstellung geplant

### **Empfehlung:** ⭐⭐⭐⭐ **EMPFOHLEN**

**Für Teile-Channel:**
- ✅ **Direkt Sinch nutzen** (zukunftssicher)
- ✅ **Schrittweise Migration** (Kunden-Channel später)

**Für beide Channels:**
- ✅ **Komplett-Migration** (langfristig besser)

---

## 🎯 FAZIT & EMPFEHLUNG

### **Technische Einschätzung:**

**✅ Sinch Conversation API ist geeignet:**
- Moderne, gut dokumentierte API
- Ähnliche Funktionalität wie MessengerPeople
- Code-Anpassung machbar (7-29 Stunden)
- Zukunftssicher

**⚠️ Herausforderungen:**
- Komplexere API-Struktur
- Code-Anpassung nötig
- Team-Einarbeitung

### **Strategische Empfehlung:**

**Kurzfristig (Teile-Channel):**
- ✅ **Direkt Sinch nutzen** (zukunftssicher)
- ✅ **Kein MessengerPeople** (Deadline zu knapp)

**Langfristig (beide Channels):**
- ✅ **Komplett-Migration zu Sinch** (bis 31.12.2026)
- ✅ **Einheitliche Lösung**

### **Nächste Schritte (wenn Sinch gewählt):**

1. **Sinch Account erstellen**
2. **API-Dokumentation studieren**
3. **Test-Account einrichten**
4. **Code-Anpassung planen**
5. **Pilot-Integration (Teile-Channel)**

---

**Status:** 📊 Evaluation abgeschlossen  
**Empfehlung:** ✅ Sinch Conversation API nutzen (zukunftssicher)  
**Aufwand:** 7-29 Stunden (je nach Umfang)  
**Zeitrahmen:** 1-2 Wochen für vollständige Integration
