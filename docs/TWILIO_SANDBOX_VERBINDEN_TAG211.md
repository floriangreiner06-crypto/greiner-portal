# Twilio WhatsApp Sandbox - Verbinden

**TAG:** 211  
**Datum:** 2026-01-26  
**Status:** 📱 **SANDBOX-VERBINDUNG**

---

## 🎯 AKTUELLE SITUATION

**Du siehst:**
- ✅ Twilio WhatsApp Sandbox Seite
- ✅ Sandbox-Nummer: `+1 415 523 8886`
- ✅ Code: `join post-frighten`
- ✅ QR-Code zum Scannen

---

## 📱 SCHRITT 1: SANDBOX VERBINDEN

### **Option A: WhatsApp-Nachricht senden** (Empfohlen)

1. **Öffne WhatsApp auf deinem Handy**

2. **Sende Nachricht an:**
   - Nummer: `+1 415 523 8886`
   - Nachricht: `join post-frighten`

3. **Warte auf Bestätigung:**
   - Twilio sendet Bestätigung
   - "You're all set!" oder ähnlich

4. **Prüfe im Dashboard:**
   - Status sollte auf "Connected" wechseln
   - Schritt 1 sollte abgeschlossen sein

---

### **Option B: QR-Code scannen**

1. **Öffne WhatsApp auf deinem Handy**

2. **Scanne QR-Code:**
   - WhatsApp → Einstellungen → Verknüpfte Geräte
   - QR-Code scannen

3. **Warte auf Bestätigung:**
   - Twilio sendet Bestätigung

---

## 🔑 SCHRITT 2: ACCOUNT SID UND AUTH TOKEN NOTIEREN

### **Account SID:**

1. **Im Dashboard (oben rechts):**
   - Klicke auf **"Account"** oder **"Account Info"**
   - Oder: https://console.twilio.com/us1/account/settings

2. **Account SID notieren:**
   - Format: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - Kopiere und speichere

---

### **Auth Token:**

1. **Auf derselben Seite:**
   - **"Auth Token"** → **"View"** klicken
   - **WICHTIG:** Token nur einmal sichtbar!
   - Kopiere und speichere

---

## 📞 SCHRITT 3: SANDBOX-NUMMER NOTIEREN

**Sandbox-Nummer:**
- Format: `whatsapp:+14155238886`
- (Mit `whatsapp:` Prefix!)

**Wichtig:**
- Diese Nummer wird in `.env` verwendet
- Format: `whatsapp:+14155238886` (nicht nur `+14155238886`)

---

## ⚙️ SCHRITT 4: KONFIGURATION IN .ENV

**Öffne:** `/opt/greiner-portal/.env`

**Füge hinzu:**
```bash
# Twilio WhatsApp API (TAG 211)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=dein_auth_token_hier
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
TWILIO_WEBHOOK_URL=https://auto-greiner.de/whatsapp/webhook
```

**Wichtig:**
- `TWILIO_ACCOUNT_SID`: Dein Account SID (Format: `AC...`)
- `TWILIO_AUTH_TOKEN`: Dein Auth Token
- `TWILIO_WHATSAPP_NUMBER`: Sandbox-Nummer mit `whatsapp:` Prefix
- `TWILIO_WEBHOOK_URL`: Öffentliche Webhook-URL

---

## 🌐 SCHRITT 5: WEBHOOK KONFIGURIEREN

### **5.1 Webhook-URL in Twilio eintragen**

1. **Auf Sandbox-Seite:**
   - Tab: **"Sandbox settings"** (neben "Sandbox")

2. **Webhook-URL eintragen:**
   - **"When a message comes in":** `https://auto-greiner.de/whatsapp/webhook`
   - **"Status callback URL":** `https://auto-greiner.de/whatsapp/webhook`
   - **HTTP Method:** POST

3. **Speichern:**
   - Klicke auf **"Save"**

---

## 🚀 SCHRITT 6: PYTHON SDK INSTALLIEREN

**Auf Server:**
```bash
cd /opt/greiner-portal
source venv/bin/activate
pip install twilio --break-system-packages
```

---

## 🔄 SCHRITT 7: SERVICE NEUSTARTEN

```bash
sudo systemctl restart greiner-portal
```

**Prüfe Status:**
```bash
sudo systemctl status greiner-portal
```

**Logs prüfen:**
```bash
journalctl -u greiner-portal -f
```

---

## ✅ SCHRITT 8: TESTEN

### **8.1 Test-Nachricht senden**

**Via API:**
```bash
curl -X POST https://auto-greiner.de/whatsapp/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "491234567890",
    "message": "Test-Nachricht von DRIVE"
  }'
```

**Wichtig:**
- `to`: Deine Handy-Nummer (die du mit Sandbox verbunden hast)
- Format: `491234567890` (ohne `+`, mit Ländercode)

---

### **8.2 Eingehende Nachricht testen**

1. **Sende WhatsApp-Nachricht:**
   - Von deinem Handy an Sandbox-Nummer: `+1 415 523 8886`
   - Sende: "Hallo Test"

2. **Prüfe ob empfangen:**
   - Gehe zu: `https://auto-greiner.de/whatsapp/messages`
   - Sollte eingehende Nachricht zeigen

---

## 📋 CHECKLISTE

### **Sandbox-Verbindung:**

- [ ] WhatsApp-Nachricht an `+1 415 523 8886` gesendet
- [ ] Code `join post-frighten` gesendet
- [ ] Bestätigung von Twilio erhalten
- [ ] Status im Dashboard: "Connected"

### **Credentials:**

- [ ] Account SID notiert (`AC...`)
- [ ] Auth Token notiert (nur einmal sichtbar!)
- [ ] Sandbox-Nummer notiert (`whatsapp:+14155238886`)

### **Konfiguration:**

- [ ] Environment-Variablen in `.env` gesetzt
- [ ] Webhook-URL in Twilio konfiguriert
- [ ] Python SDK installiert (`pip install twilio`)
- [ ] Service neugestartet

### **Testing:**

- [ ] Test-Nachricht gesendet
- [ ] Eingehende Nachricht getestet

---

## 🆘 TROUBLESHOOTING

### **Problem 1: "Sandbox nicht verbunden"**

**Lösung:**
- Prüfe ob Nachricht korrekt gesendet wurde
- Format: `join post-frighten` (exakt!)
- Warte 1-2 Minuten
- Prüfe Dashboard erneut

---

### **Problem 2: "Auth Token nicht sichtbar"**

**Lösung:**
- Token ist nur einmal sichtbar
- Falls nicht notiert: **"Reset"** klicken
- Neuen Token generieren
- Sofort notieren!

---

### **Problem 3: "Webhook nicht empfangen"**

**Lösung:**
1. Prüfe Webhook-URL in Twilio Dashboard
2. Prüfe ob URL öffentlich erreichbar ist (HTTPS!)
3. Prüfe Server-Logs: `journalctl -u greiner-portal -f`

---

## 💡 TIPP

**Sandbox-Limits:**
- Sandbox ist für **Tests** gedacht
- Nur **verbundene Nummern** können Nachrichten senden/empfangen
- Für Produktion: Eigene WhatsApp Business Nummer verifizieren

**Nächster Schritt nach Tests:**
- Eigene WhatsApp Business Nummer bei Twilio anfragen
- Keine direkte Facebook-Verbindung nötig!

---

**Status:** 📱 Sandbox-Verbindung  
**Nächster Schritt:** Sandbox verbinden (Code senden) und Credentials notieren
