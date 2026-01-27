# Twilio WhatsApp Integration - Setup-Anleitung

**TAG:** 211  
**Datum:** 2026-01-26  
**Status:** 🚀 **SETUP-ANLEITUNG**

---

## 🎯 ÜBERSICHT

**Twilio WhatsApp Integration für Teile-Handelsgeschäft**

**Vorteile:**
- ✅ **Keine direkte Facebook-Verbindung** - Twilio übernimmt das
- ✅ **Transparente Preise** - Pay-as-you-go (~€1-15/Monat)
- ✅ **Schneller Start** - Keine Wartezeiten
- ✅ **Sehr gute Dokumentation** - Python SDK verfügbar

---

## 📋 SCHRITT 1: TWILIO ACCOUNT ERSTELLEN

### **1.1 Account registrieren**

1. **Gehe zu:** https://www.twilio.com/
2. **Klicke:** "Sign Up" oder "Get Started"
3. **Fülle aus:**
   - E-Mail-Adresse
   - Passwort
   - Name
   - Telefonnummer (für Verifizierung)

4. **E-Mail verifizieren:**
   - Prüfe dein E-Mail-Postfach
   - Klicke auf Verifizierungs-Link

---

### **1.2 Account SID und Auth Token notieren**

**Nach Registrierung:**

1. **Dashboard öffnen:**
   - https://console.twilio.com/
   - Login mit deinem Account

2. **Account SID notieren:**
   - Im Dashboard sichtbar (Format: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
   - Oder: **Account Info** → **Account SID**

3. **Auth Token notieren:**
   - **Account Info** → **Auth Token**
   - Klicke auf "View" um Token anzuzeigen
   - **WICHTIG:** Token nur einmal sichtbar! Notieren!

---

## 📱 SCHRITT 2: WHATSAPP SANDBOX AKTIVIEREN

### **2.1 WhatsApp Sandbox öffnen**

1. **Im Twilio Dashboard:**
   - **Messaging** → **Try it out** → **Send a WhatsApp message**
   - Oder: **Messaging** → **WhatsApp** → **Sandbox**

2. **Sandbox aktivieren:**
   - Klicke auf **"Join Sandbox"** oder **"Get Started"**

---

### **2.2 WhatsApp-Nummer verbinden**

**Twilio Sandbox:**
- Twilio stellt eine **Test-WhatsApp-Nummer** bereit
- Format: `whatsapp:+14155238886` (Beispiel)

**Deine Nummer verbinden:**
1. **Sende WhatsApp-Nachricht an Sandbox-Nummer:**
   - Öffne WhatsApp auf deinem Handy
   - Sende Nachricht an: `+1 415 523 8886`
   - Code: `join <code>` (z.B. `join mountain-fly`)

2. **Bestätigung:**
   - Twilio sendet Bestätigung
   - Deine Nummer ist jetzt verbunden

---

### **2.3 WhatsApp-Nummer notieren**

**Sandbox-Nummer:**
- Format: `whatsapp:+14155238886`
- Im Dashboard sichtbar: **Messaging** → **WhatsApp** → **Sandbox**

**Für Produktion:**
- Später: Eigene WhatsApp Business Nummer verifizieren
- Jetzt: Sandbox-Nummer verwenden

---

## 🔧 SCHRITT 3: PYTHON SDK INSTALLIEREN

### **3.1 Twilio SDK installieren**

**Auf Server:**
```bash
cd /opt/greiner-portal
source venv/bin/activate
pip install twilio --break-system-packages
```

**Oder in requirements.txt:**
```bash
echo "twilio>=8.0.0" >> requirements.txt
pip install -r requirements.txt --break-system-packages
```

---

## ⚙️ SCHRITT 4: KONFIGURATION IN .ENV

### **4.1 Environment-Variablen hinzufügen**

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
- `TWILIO_WHATSAPP_NUMBER`: Sandbox-Nummer (Format: `whatsapp:+...`)
- `TWILIO_WEBHOOK_URL`: Öffentliche Webhook-URL

---

## 🌐 SCHRITT 5: WEBHOOK KONFIGURIEREN

### **5.1 Webhook-URL in Twilio eintragen**

1. **Twilio Dashboard:**
   - **Messaging** → **WhatsApp** → **Sandbox**
   - Oder: **Messaging** → **Settings** → **WhatsApp Sandbox Settings**

2. **Webhook-URL eintragen:**
   - **When a message comes in:** `https://auto-greiner.de/whatsapp/webhook`
   - **Status callback URL:** `https://auto-greiner.de/whatsapp/webhook`
   - **HTTP Method:** POST

3. **Speichern:**
   - Klicke auf **"Save"**

---

### **5.2 Webhook testen**

**Test-Nachricht senden:**
1. Sende WhatsApp-Nachricht an Sandbox-Nummer
2. Prüfe ob Webhook empfangen wird:
   - Server-Logs: `journalctl -u greiner-portal -f`
   - Sollte "Eingehende Twilio-Nachricht gespeichert" zeigen

---

## 🚀 SCHRITT 6: SERVICE NEUSTARTEN

### **6.1 Service neustarten**

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

## ✅ SCHRITT 7: TESTEN

### **7.1 Test-Nachricht senden**

**Via API:**
```bash
curl -X POST https://auto-greiner.de/whatsapp/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "491234567890",
    "message": "Test-Nachricht von DRIVE"
  }'
```

**Via UI:**
- Gehe zu: `https://auto-greiner.de/whatsapp/contacts`
- Klicke auf Kontakt
- Sende Test-Nachricht

---

### **7.2 Eingehende Nachricht testen**

1. **Sende WhatsApp-Nachricht:**
   - Von deinem Handy an Sandbox-Nummer
   - Format: `+1 415 523 8886`
   - Code: `join <code>`

2. **Prüfe ob empfangen:**
   - Gehe zu: `https://auto-greiner.de/whatsapp/messages`
   - Sollte eingehende Nachricht zeigen

---

## 📊 SCHRITT 8: PRODUKTION (SPÄTER)

### **8.1 Eigene WhatsApp Business Nummer**

**Für Produktion:**
1. **Twilio Dashboard:**
   - **Messaging** → **WhatsApp** → **Sender Phone Numbers**
   - **Request Phone Number**

2. **Telefonnummer verifizieren:**
   - Twilio führt durch Verifizierung
   - Keine direkte Facebook-Verbindung nötig!

3. **Nummer in .env aktualisieren:**
   - `TWILIO_WHATSAPP_NUMBER=whatsapp:+491234567890`

---

## 🆘 TROUBLESHOOTING

### **Problem 1: "Twilio Python SDK nicht installiert"**

**Lösung:**
```bash
cd /opt/greiner-portal
source venv/bin/activate
pip install twilio --break-system-packages
sudo systemctl restart greiner-portal
```

---

### **Problem 2: "Twilio-Konfiguration unvollständig"**

**Lösung:**
- Prüfe `.env` Datei
- Stelle sicher, dass alle Variablen gesetzt sind:
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_WHATSAPP_NUMBER`

---

### **Problem 3: "Webhook nicht empfangen"**

**Lösung:**
1. Prüfe Webhook-URL in Twilio Dashboard
2. Prüfe ob URL öffentlich erreichbar ist (HTTPS!)
3. Prüfe Server-Logs: `journalctl -u greiner-portal -f`

---

### **Problem 4: "Nachricht nicht gesendet"**

**Lösung:**
1. Prüfe Twilio Dashboard → **Monitor** → **Logs**
2. Prüfe Server-Logs
3. Prüfe ob Sandbox-Nummer korrekt ist
4. Prüfe ob Empfänger-Nummer verbunden ist (Sandbox)

---

## 📋 CHECKLISTE

### **Setup:**

- [ ] Twilio Account erstellt
- [ ] Account SID notiert
- [ ] Auth Token notiert
- [ ] WhatsApp Sandbox aktiviert
- [ ] Sandbox-Nummer verbunden
- [ ] Python SDK installiert (`pip install twilio`)
- [ ] Environment-Variablen in `.env` gesetzt
- [ ] Webhook-URL in Twilio konfiguriert
- [ ] Service neugestartet (`sudo systemctl restart greiner-portal`)
- [ ] Test-Nachricht gesendet
- [ ] Eingehende Nachricht getestet

---

## 🔗 WICHTIGE LINKS

- **Twilio Dashboard:** https://console.twilio.com/
- **Twilio WhatsApp Docs:** https://www.twilio.com/docs/whatsapp
- **Twilio Python SDK:** https://www.twilio.com/docs/libraries/python
- **Twilio Pricing:** https://www.twilio.com/en-us/whatsapp/pricing

---

## 💡 TIPP

**Sandbox vs. Produktion:**
- **Sandbox:** Für Tests, kostenlos, limitiert
- **Produktion:** Eigene Nummer, Pay-as-you-go

**Empfehlung:**
- Starte mit Sandbox für Tests
- Wechsle zu Produktion wenn alles funktioniert

---

**Status:** 🚀 Setup-Anleitung abgeschlossen  
**Nächster Schritt:** Twilio Account erstellen und WhatsApp Sandbox aktivieren
