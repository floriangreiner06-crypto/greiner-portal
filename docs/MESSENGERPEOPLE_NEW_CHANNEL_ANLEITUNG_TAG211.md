# Anleitung: Neuen WhatsApp-Channel in MessengerPeople erstellen

**TAG:** 211  
**Datum:** 2026-01-26  
**Zweck:** Separater Channel für Teile-Bereich

---

## 🎯 ZIEL

Einen neuen WhatsApp-Channel in MessengerPeople erstellen, um:
- Separate WhatsApp-Nummer für Teile-Bereich zu erhalten
- Getrennte Kommunikation von Kunden- und Teile-Bereich
- Eigene Channel-ID für DRIVE-Integration

---

## 📋 VORAUSSETZUNGEN

1. **MessengerPeople Account** - Bereits vorhanden (für bestehenden Kunden-Channel)
2. **Facebook Business Manager** - Account vorhanden
3. **WhatsApp Business Account** - Bereits verifiziert (für bestehenden Channel)

---

## 🚀 SCHRITT-FÜR-SCHRITT ANLEITUNG

### **Schritt 1: MessengerPeople Dashboard öffnen**

1. **Login:** https://app.messengerpeople.dev/ (oder dein MessengerPeople Dashboard)
2. **Navigation:** Channels → WhatsApp (oder Settings → Channels)

### **Schritt 2: Neuen Channel erstellen**

**Option A: Über Channels-Übersicht**
1. Klicke auf **"+ New Channel"** oder **"Add Channel"**
2. Wähle **"WhatsApp Business"** aus
3. Folge dem Setup-Wizard

**Option B: Über Settings**
1. Gehe zu **Settings** → **Channels**
2. Klicke auf **"Add WhatsApp Channel"**
3. Folge dem Setup-Wizard

### **Schritt 3: WhatsApp Business Account verbinden**

1. **Facebook Business Manager verbinden:**
   - Falls noch nicht verbunden: Facebook Business Manager Account verknüpfen
   - Berechtigungen erteilen (MessengerPeople muss WhatsApp verwalten können)

2. **WhatsApp Business Account auswählen:**
   - Wähle deinen WhatsApp Business Account aus
   - Oder erstelle einen neuen (falls nötig)

### **Schritt 4: Telefonnummer zuweisen**

1. **Neue Nummer hinzufügen:**
   - **Option 1:** Bestehende Nummer verwenden (falls verfügbar)
   - **Option 2:** Neue Nummer über MessengerPeople beantragen
   - **Option 3:** Eigene Nummer verifizieren (SMS oder Voice)

2. **Verifizierung:**
   - SMS-Code oder Voice-Call erhalten
   - Code eingeben
   - Nummer wird verifiziert

### **Schritt 5: Channel aktivieren**

1. **Channel-Name vergeben:**
   - z.B. "Teile-Service" oder "WhatsApp Teile"
   - Beschreibung: "WhatsApp für Teile-Handelsgeschäft"

2. **Channel aktivieren:**
   - Klicke auf **"Activate"** oder **"Save"**
   - Warte auf Bestätigung (kann 1-2 Tage dauern bei neuer WhatsApp-Genehmigung)

### **Schritt 6: Channel-ID finden**

1. **Channel-Details öffnen:**
   - Klicke auf den neu erstellten Channel
   - Oder: Settings → Channels → [Dein Teile-Channel]

2. **Channel-ID kopieren:**
   - **Option 1:** In Channel-Details angezeigt (z.B. "Channel ID: abc123...")
   - **Option 2:** In API-Settings (Settings → API → Channels)
   - **Option 3:** In Webhook-Konfiguration

3. **Format:**
   - Channel-ID ist meist eine UUID (z.B. `abc123-def456-ghi789`)
   - Oder eine alphanumerische ID

---

## 🔍 ALTERNATIVE: Channel-ID über API finden

Falls die Channel-ID nicht im Dashboard sichtbar ist:

### **API-Endpoint: Channels auflisten**

```bash
GET https://rest.messengerpeople.com/api/v17/channels
Authorization: Bearer DEIN_API_KEY
```

**Response:**
```json
{
  "channels": [
    {
      "id": "channel-id-kunden",
      "name": "Kunden-Service",
      "type": "whatsapp",
      "phone_number": "+49..."
    },
    {
      "id": "channel-id-teile",  // ← Das ist die neue Channel-ID!
      "name": "Teile-Service",
      "type": "whatsapp",
      "phone_number": "+49..."
    }
  ]
}
```

---

## 📝 KONFIGURATION IN DRIVE

Nachdem du die Channel-ID hast, füge sie in `.env` ein:

```bash
# Neue Konfiguration für Teile-Channel
MESSENGERPEOPLE_TEILE_CHANNEL_ID=DEINE_TEILE_CHANNEL_ID
MESSENGERPEOPLE_TEILE_WEBHOOK_TOKEN=teile_webhook_token_change_me
MESSENGERPEOPLE_TEILE_WEBHOOK_URL=https://auto-greiner.de/whatsapp/teile/webhook
```

---

## ⚠️ WICHTIGE HINWEISE

### **Genehmigungsprozess**

- **Neue WhatsApp-Nummer:** Kann 1-2 Werktage dauern (Meta-Genehmigung)
- **Bestehende Nummer:** Sofort verfügbar (nach Verifizierung)

### **Kosten**

- **Pro Channel:** MessengerPeople berechnet pro WhatsApp-Channel
- **Preise:** Je nach Plan (siehe MessengerPeople Pricing)
- **Nachrichten:** Gleiche Preise wie bestehender Channel (€0.001-0.003/Nachricht)

### **Berechtigungen**

- MessengerPeople benötigt **vollen Zugriff** auf WhatsApp Business Account
- Facebook Business Manager muss MessengerPeople als **Partner** hinzugefügt sein

---

## 🐛 TROUBLESHOOTING

### **Problem: "Channel kann nicht erstellt werden"**

**Lösung:**
1. Prüfe Facebook Business Manager Berechtigungen
2. Prüfe ob WhatsApp Business Account aktiv ist
3. Kontaktiere MessengerPeople Support

### **Problem: "Channel-ID nicht gefunden"**

**Lösung:**
1. Prüfe API-Endpoint: `GET /channels`
2. Prüfe Channel-Details im Dashboard
3. Kontaktiere MessengerPeople Support

### **Problem: "Nummer kann nicht verifiziert werden"**

**Lösung:**
1. Prüfe SMS/Voice-Code (kann 5-10 Minuten dauern)
2. Versuche Voice-Call statt SMS
3. Prüfe ob Nummer bereits für WhatsApp verwendet wird

---

## 📞 SUPPORT

Falls Probleme auftreten:

1. **MessengerPeople Support:**
   - Dashboard → Support
   - Oder: support@messengerpeople.dev

2. **Dokumentation:**
   - https://helpcenter.messengerpeople.com/
   - https://rest.messengerpeople.com/docs/

---

## ✅ CHECKLISTE

Nach Erstellung des Channels:

- [ ] Channel erstellt
- [ ] Telefonnummer verifiziert
- [ ] Channel aktiviert
- [ ] Channel-ID notiert
- [ ] In `.env` konfiguriert
- [ ] Webhook konfiguriert (nächster Schritt)

---

**Status:** 📋 Anleitung erstellt  
**Nächster Schritt:** Channel-ID in `.env` eintragen und Webhook konfigurieren
