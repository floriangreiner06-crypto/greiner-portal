# Websms/LINK Mobility WhatsApp API - Integrationsplan

**TAG:** 211  
**Datum:** 2026-01-26  
**Status:** 📊 **PLANUNG - Bereits Kunde!**

---

## 🎯 SITUATION

**Wichtig:** Ihr seid bereits Websms/LINK Mobility Kunde! ✅

**Vorteile:**
- ✅ **Keine neue Registrierung** - Bereits Kunde
- ✅ **Bekanntes System** - Team kennt sich aus
- ✅ **Deutscher Anbieter** - Support auf Deutsch
- ✅ **WhatsApp API verfügbar** - Über LINK Mobility
- ✅ **Multiple Channels** - Separate Nummern möglich

---

## 📋 WEBSMS/LINK MOBILITY WHATSAPP API

### **Verfügbare APIs:**

1. **WhatsApp REST API**
   - REST-basiert
   - Für Software/App-Integration
   - Dokumentation: https://developer.linkmobility.eu/whatsapp-api/rest-api

2. **WhatsApp SMTP API**
   - E-Mail-zu-WhatsApp
   - Weniger relevant für unsere Integration

3. **Receive WhatsApp Messages**
   - Event-basiert
   - Webhook-Support
   - E-Mail-Forwarding möglich
   - Dokumentation: https://developer.linkmobility.eu/whatsapp-api/receive-whatsapp-messages

### **Features:**
- ✅ Senden von WhatsApp-Nachrichten
- ✅ Empfangen von WhatsApp-Nachrichten (Webhook)
- ✅ Delivery Status Tracking
- ✅ Multiple WhatsApp Channels
- ✅ JSON-basiert (Meta-Format)

---

## 🔧 SETUP-SCHRITTE

### **Schritt 1: WhatsApp Channel erstellen**

**Wo:**
- https://app.linkmobility.eu/ (falls Account dort)
- ODER: https://app.websms.com/ (falls Account dort)

**Vorgehen:**
1. Login mit bestehendem Account
2. "Create WhatsApp Channel" oder "WhatsApp Channels" öffnen
3. Facebook Business Account verknüpfen
4. Telefonnummer verifizieren
5. Channel aktivieren

**Wichtig:** 
- Mehrere WhatsApp Channels möglich (für separate Nummern)
- Jeder Channel hat eine eigene Channel ID

### **Schritt 2: API-Zugang prüfen**

**Fragen:**
- Habt ihr bereits API-Zugang?
- API-Credentials vorhanden?
- Welche API-URL wird verwendet?

**Mögliche URLs:**
- `https://api.linkmobility.eu/`
- `https://api.websms.com/`
- Oder andere (muss in Account geprüft werden)

### **Schritt 3: Webhook konfigurieren**

**Webhook-URL:**
- `https://auto-greiner.de/whatsapp/webhook` (für Teile-Channel)
- ODER: `https://auto-greiner.de/whatsapp/teile/webhook` (separater Endpoint)

**Events:**
- Incoming messages
- Delivery status

---

## 📊 API-STRUKTUR (basierend auf Recherche)

### **REST API (vermutlich):**

**Base URL:**
- Vermutlich: `https://api.linkmobility.eu/` oder `https://api.websms.com/`
- Muss in Account geprüft werden

**Authentifizierung:**
- Vermutlich: API Key oder Basic Auth
- Muss in Dokumentation geprüft werden

**Endpoints:**
- Send message: Vermutlich `POST /whatsapp/messages` oder ähnlich
- Receive messages: Webhook-basiert

**Request-Format:**
- JSON-basiert
- Meta-Format (vermutlich ähnlich wie Meta API)

---

## 💡 CODE-ANPASSUNG

### **Geschätzter Aufwand:**

**Minimal (wenn API ähnlich MessengerPeople):**
- API-Client anpassen: **4-6 Stunden**
- Webhook-Struktur anpassen: **2-3 Stunden**
- Testing: **2-3 Stunden**
- **Gesamt: ~9-12 Stunden**

**Vollständig (wenn API anders):**
- API-Client neu: **6-8 Stunden**
- Webhook neu: **3-4 Stunden**
- Testing: **3-4 Stunden**
- **Gesamt: ~12-16 Stunden**

---

## 📋 WAS ICH BRAUCHE

### **1. API-Dokumentation:**
- [ ] REST API Endpoints (send message)
- [ ] Authentifizierung (API Key, Basic Auth, etc.)
- [ ] Request/Response-Format
- [ ] Webhook-Struktur (receive messages)
- [ ] Error-Handling

### **2. Credentials:**
- [ ] API Key oder ähnlich
- [ ] API-URL (Base URL)
- [ ] WhatsApp Channel ID

### **3. Channel:**
- [ ] WhatsApp Channel erstellt?
- [ ] Telefonnummer verifiziert?
- [ ] Channel aktiviert?

---

## 🚀 NÄCHSTE SCHRITTE

### **Sofort (du):**

1. **Login prüfen:**
   - https://app.linkmobility.eu/ ODER https://app.websms.com/
   - Prüfen ob WhatsApp Channel vorhanden
   - Falls nicht: Channel erstellen

2. **API-Dokumentation öffnen:**
   - https://developer.linkmobility.eu/whatsapp-api/rest-api
   - Screenshot oder Link teilen
   - Oder: API-Dokumentation herunterladen/teilen

3. **API-Credentials prüfen:**
   - Habt ihr bereits API-Zugang?
   - API Key vorhanden?
   - Falls nicht: API-Zugang beantragen

### **Dann (ich):**

1. **API-Struktur analysieren**
2. **Code-Anpassung planen**
3. **Integration implementieren**

---

## 🎯 VORTEILE WEBSMS/LINK MOBILITY

### **Warum Websms die beste Wahl ist:**

1. ✅ **Bereits Kunde** - Keine neue Registrierung nötig
2. ✅ **Deutscher Anbieter** - Support auf Deutsch, DSGVO
3. ✅ **Bekanntes System** - Team kennt sich aus
4. ✅ **WhatsApp API verfügbar** - Über LINK Mobility
5. ✅ **Multiple Channels** - Separate Nummern möglich
6. ✅ **Omnichannel** - SMS + WhatsApp + RCS
7. ✅ **Intelligenter Fallback** - WhatsApp → SMS automatisch

---

## ⚠️ WICHTIGE FRAGEN

### **Für die Integration brauche ich:**

1. **API-Dokumentation:**
   - Könnt ihr mir die REST API Dokumentation teilen?
   - Oder: Link zu https://developer.linkmobility.eu/whatsapp-api/rest-api

2. **Credentials:**
   - Habt ihr bereits API-Zugang?
   - API Key vorhanden?
   - Welche API-URL wird verwendet?

3. **Channel:**
   - Habt ihr bereits einen WhatsApp Channel?
   - Oder muss ein neuer erstellt werden?
   - Welche Telefonnummer soll verwendet werden?

---

**Status:** 📊 Planung gestartet  
**Vorteil:** Bereits Kunde - keine neue Registrierung nötig!  
**Nächster Schritt:** API-Dokumentation prüfen und WhatsApp Channel erstellen/prüfen
