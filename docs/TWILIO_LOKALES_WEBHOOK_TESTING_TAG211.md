# Twilio - Lokales Webhook-Testing (Ngrok/Tunnelmole)

**TAG:** 211  
**Datum:** 2026-01-26  
**Status:** 🧪 **TESTING-ANLEITUNG**

---

## 🎯 ZWECK

**Lokales Webhook-Testing ohne öffentliche URL:**
- Webhook-Endpoint lokal testen
- Twilio Sandbox mit lokaler URL verbinden
- Sicherheitsmaßnahmen testen (Signatur-Validierung)
- Eingehende Nachrichten testen

**Vorteil:**
- ✅ Funktioniert, bevor DMZ steht
- ✅ Keine öffentliche URL nötig
- ✅ Schnelles Testing

---

## 📋 VORBEREITUNG

### **1. Twilio Credentials prüfen**

**In `.env` Datei müssen gesetzt sein:**
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
TWILIO_WEBHOOK_URL=https://api.auto-greiner.de/whatsapp/webhook
```

**Wichtig:**
- `TWILIO_WEBHOOK_URL` wird später durch Ngrok-URL ersetzt
- `TWILIO_WHATSAPP_NUMBER` ist die Sandbox-Nummer (Format: `whatsapp:+14155238886`)

---

## 🔧 OPTION 1: NGROK (Empfohlen)

### **1.1 Ngrok installieren**

**Linux:**
```bash
# Download
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz

# Entpacken
tar -xzf ngrok-v3-stable-linux-amd64.tgz

# In PATH verschieben (optional)
sudo mv ngrok /usr/local/bin/
```

**Oder via Snap:**
```bash
sudo snap install ngrok
```

---

### **1.2 Ngrok Account erstellen (optional, aber empfohlen)**

**Warum:**
- ✅ Feste URL (nicht bei jedem Start neu)
- ✅ Mehr Features
- ✅ Bessere Performance

**Vorgehen:**
1. **Gehe zu:** https://dashboard.ngrok.com/signup
2. **Registriere dich** (kostenlos)
3. **Authtoken kopieren** (aus Dashboard)
4. **Token setzen:**
   ```bash
   ngrok config add-authtoken DEIN_AUTH_TOKEN
   ```

---

### **1.3 Ngrok Tunnel starten**

**Flask-App muss laufen:**
```bash
cd /opt/greiner-portal
source venv/bin/activate
python app.py
# Oder: gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

**In neuem Terminal:**
```bash
# Ngrok Tunnel starten (Port 5000)
ngrok http 5000
```

**Ausgabe:**
```
Forwarding   https://abc123.ngrok-free.app -> http://localhost:5000
```

**Wichtig:**
- ✅ **HTTPS-URL kopieren** (z.B. `https://abc123.ngrok-free.app`)
- ✅ **Webhook-URL:** `https://abc123.ngrok-free.app/whatsapp/webhook`

---

### **1.4 Twilio Sandbox konfigurieren**

**1. Twilio Console öffnen:**
- https://console.twilio.com/
- **Messaging** → **Try it out** → **Send a WhatsApp message**

**2. Sandbox konfigurieren:**
- **Webhook URL:** `https://abc123.ngrok-free.app/whatsapp/webhook`
- **HTTP Method:** `POST`

**3. Sandbox-Nummer notieren:**
- Format: `whatsapp:+14155238886`
- Diese Nummer in `.env` setzen: `TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886`

---

### **1.5 Testen**

**1. Handy mit Sandbox verbinden:**
- Sende `join <code>` an Twilio Sandbox-Nummer
- Code steht in Twilio Console

**2. Test-Nachricht senden:**
- Sende WhatsApp-Nachricht an Sandbox-Nummer
- Prüfe Flask-Logs: `tail -f /var/log/greiner-portal/app.log`

**3. Webhook prüfen:**
- Twilio Console → **Monitor** → **Logs** → **Messaging**
- Prüfe ob Webhook erfolgreich war (200 OK)

---

## 🔧 OPTION 2: TUNNELMOLE (Einfacher, aber weniger Features)

### **2.1 Tunnelmole installieren**

```bash
# Via npm (falls Node.js installiert)
npm install -g tunnelmole

# Oder: Download Binary
# https://github.com/robbie-cahill/tunnelmole-client/releases
```

---

### **2.2 Tunnelmole starten**

**Flask-App muss laufen:**
```bash
cd /opt/greiner-portal
source venv/bin/activate
python app.py
```

**In neuem Terminal:**
```bash
# Tunnelmole starten (Port 5000)
tunnelmole 5000
```

**Ausgabe:**
```
https://abc123.tunnelmole.net is forwarding to localhost:5000
```

**Wichtig:**
- ✅ **HTTPS-URL kopieren** (z.B. `https://abc123.tunnelmole.net`)
- ✅ **Webhook-URL:** `https://abc123.tunnelmole.net/whatsapp/webhook`

---

### **2.3 Twilio Sandbox konfigurieren**

**Gleiche Schritte wie bei Ngrok:**
1. Twilio Console öffnen
2. Webhook-URL setzen: `https://abc123.tunnelmole.net/whatsapp/webhook`
3. HTTP Method: `POST`

---

## 🧪 TESTING

### **1. Webhook-Endpoint testen**

**Manueller Test (ohne Twilio):**
```bash
# POST-Request an Webhook (sollte 401 geben ohne Signatur)
curl -X POST http://localhost:5000/whatsapp/webhook \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "MessageSid=SM123&From=whatsapp:+491234567890&Body=Test"
```

**Erwartung:**
- ✅ **401 Unauthorized** (keine gültige Signatur)
- ✅ Log zeigt: "Ungültige Twilio-Signatur"

---

### **2. Twilio Sandbox testen**

**1. Handy verbinden:**
- Sende `join <code>` an Twilio Sandbox-Nummer
- Code in Twilio Console

**2. Test-Nachricht senden:**
- Sende WhatsApp-Nachricht an Sandbox-Nummer
- Prüfe Flask-Logs

**3. Prüfe Datenbank:**
```sql
SELECT * FROM whatsapp_messages ORDER BY created_at DESC LIMIT 5;
SELECT * FROM whatsapp_contacts ORDER BY created_at DESC LIMIT 5;
```

---

### **3. Signatur-Validierung testen**

**Erfolgreicher Request (von Twilio):**
- ✅ **200 OK** (XML Response)
- ✅ Nachricht in DB gespeichert
- ✅ Log zeigt: "Twilio-Request erfolgreich validiert"

**Gefälschter Request (ohne Signatur):**
- ✅ **401 Unauthorized**
- ✅ Keine Nachricht in DB
- ✅ Log zeigt: "Ungültige Twilio-Signatur"

---

## 🔍 DEBUGGING

### **1. Flask-Logs prüfen**

```bash
# Live-Logs
tail -f /var/log/greiner-portal/app.log

# Oder: Journalctl (falls systemd)
journalctl -u greiner-portal -f
```

**Was prüfen:**
- ✅ Webhook-Requests werden empfangen
- ✅ Signatur-Validierung funktioniert
- ✅ Nachrichten werden gespeichert

---

### **2. Twilio Console prüfen**

**Monitor → Logs → Messaging:**
- ✅ Webhook-Status (200 OK = erfolgreich)
- ✅ Request-Details
- ✅ Response-Zeit

---

### **3. Datenbank prüfen**

```sql
-- Nachrichten prüfen
SELECT * FROM whatsapp_messages ORDER BY created_at DESC LIMIT 10;

-- Kontakte prüfen
SELECT * FROM whatsapp_contacts ORDER BY created_at DESC LIMIT 10;

-- Conversations prüfen (falls Verkäufer-Support aktiv)
SELECT * FROM whatsapp_conversations ORDER BY last_message_at DESC LIMIT 10;
```

---

## ⚠️ WICHTIGE HINWEISE

### **1. Ngrok-URL ändert sich**

**Problem:**
- Bei kostenlosem Ngrok ändert sich URL bei jedem Start
- Twilio-Webhook muss neu konfiguriert werden

**Lösung:**
- ✅ Ngrok Account erstellen (feste URL möglich)
- ✅ Oder: URL nach jedem Start neu in Twilio setzen

---

### **2. Rate Limiting**

**Ngrok:**
- Kostenlos: 40 Requests/Minute
- Für Testing ausreichend

**Tunnelmole:**
- Keine Limits bekannt
- Für Testing ausreichend

---

### **3. HTTPS erforderlich**

**Twilio erfordert HTTPS:**
- ✅ Ngrok: HTTPS automatisch
- ✅ Tunnelmole: HTTPS automatisch
- ❌ HTTP funktioniert nicht!

---

## 📋 CHECKLISTE

### **Vorbereitung:**

- [ ] Twilio Credentials in `.env` gesetzt
- [ ] Flask-App läuft (Port 5000)
- [ ] Ngrok/Tunnelmole installiert

### **Setup:**

- [ ] Ngrok/Tunnelmole Tunnel gestartet
- [ ] HTTPS-URL notiert
- [ ] Twilio Sandbox mit Webhook-URL konfiguriert
- [ ] Handy mit Sandbox verbunden

### **Testing:**

- [ ] Test-Nachricht gesendet
- [ ] Webhook empfängt Request (200 OK)
- [ ] Nachricht in DB gespeichert
- [ ] Signatur-Validierung funktioniert (401 bei gefälschten Requests)

---

## 🎯 NÄCHSTE SCHRITTE

**Nach erfolgreichem Testing:**

1. ✅ **DMZ-URL verwenden:**
   - Webhook-URL in Twilio auf `https://api.auto-greiner.de/whatsapp/webhook` ändern
   - Ngrok/Tunnelmole kann gestoppt werden

2. ✅ **Produktions-Testing:**
   - Webhook mit DMZ-URL testen
   - Signatur-Validierung prüfen

3. ✅ **Monitoring:**
   - Logs überwachen
   - Fehler prüfen

---

**Status:** 🧪 Testing-Anleitung erstellt  
**Nächster Schritt:** Ngrok/Tunnelmole installieren und Testing starten
