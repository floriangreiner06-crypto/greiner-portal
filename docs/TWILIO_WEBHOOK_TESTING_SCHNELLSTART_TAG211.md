# Twilio Webhook Testing - Schnellstart

**TAG:** 211  
**Datum:** 2026-01-26  
**Status:** 🚀 **SCHNELLSTART-ANLEITUNG**

---

## 🎯 ZWECK

**Lokales Webhook-Testing ohne öffentliche URL:**
- Webhook-Endpoint lokal testen
- Twilio Sandbox mit lokaler URL verbinden
- Sicherheitsmaßnahmen testen

---

## ⚡ SCHNELLSTART (5 Minuten)

### **Schritt 1: Ngrok installieren**

```bash
cd /opt/greiner-portal
./scripts/setup_ngrok.sh
```

**Oder manuell:**
```bash
cd /tmp
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar -xzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/
ngrok version
```

---

### **Schritt 2: Ngrok Tunnel starten**

**In neuem Terminal:**
```bash
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

### **Schritt 3: Twilio Sandbox konfigurieren**

**1. Twilio Console öffnen:**
- https://console.twilio.com/
- **Messaging** → **Try it out** → **Send a WhatsApp message**

**2. Sandbox konfigurieren:**
- **Webhook URL:** `https://abc123.ngrok-free.app/whatsapp/webhook`
- **HTTP Method:** `POST`

**3. Sandbox-Nummer notieren:**
- Format: `whatsapp:+14155238886`
- Diese Nummer in `.env` setzen (falls noch nicht gesetzt)

---

### **Schritt 4: Handy mit Sandbox verbinden**

**1. Code in Twilio Console finden:**
- **Messaging** → **Try it out** → **Send a WhatsApp message**
- Code steht dort (z.B. `join abc-def-ghi`)

**2. WhatsApp-Nachricht senden:**
- Sende `join abc-def-ghi` an Twilio Sandbox-Nummer
- Format: `+1 415 523 8886`

**3. Bestätigung:**
- Twilio sendet Bestätigung: "You're all set!"

---

### **Schritt 5: Test-Nachricht senden**

**1. Von Handy an Sandbox-Nummer:**
- Sende: "Hallo, Test-Nachricht"

**2. Prüfe Flask-Logs:**
```bash
journalctl -u greiner-portal -f
```

**Erwartung:**
- ✅ Webhook-Request empfangen
- ✅ Signatur-Validierung erfolgreich
- ✅ Nachricht in DB gespeichert

**3. Prüfe Datenbank:**
```sql
SELECT * FROM whatsapp_messages ORDER BY created_at DESC LIMIT 5;
SELECT * FROM whatsapp_contacts ORDER BY created_at DESC LIMIT 5;
```

---

## 🔍 DEBUGGING

### **Problem 1: "Ngrok nicht gefunden"**

**Lösung:**
```bash
# Prüfe ob installiert
which ngrok

# Falls nicht: Installieren
./scripts/setup_ngrok.sh
```

---

### **Problem 2: "Webhook nicht empfangen"**

**Prüfe:**
1. ✅ Ngrok Tunnel läuft? (`ngrok http 5000`)
2. ✅ Flask-App läuft? (`systemctl status greiner-portal`)
3. ✅ Webhook-URL in Twilio korrekt? (HTTPS!)
4. ✅ Port 5000 erreichbar? (`curl http://localhost:5000`)

---

### **Problem 3: "401 Unauthorized"**

**Das ist korrekt!** 
- ✅ Signatur-Validierung funktioniert
- ✅ Gefälschte Requests werden abgelehnt
- ✅ Nur echte Twilio-Requests werden akzeptiert

**Prüfe:**
- ✅ Twilio sendet Request mit Signatur
- ✅ `TWILIO_AUTH_TOKEN` in `.env` gesetzt

---

### **Problem 4: "Nachricht nicht in DB"**

**Prüfe:**
1. ✅ Flask-Logs (Fehler?)
2. ✅ Datenbank-Verbindung
3. ✅ Signatur-Validierung erfolgreich?

```bash
# Logs prüfen
journalctl -u greiner-portal -f

# Datenbank prüfen
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -c "SELECT * FROM whatsapp_messages ORDER BY created_at DESC LIMIT 5;"
```

---

## 📋 CHECKLISTE

### **Setup:**

- [ ] Ngrok installiert (`ngrok version`)
- [ ] Flask-App läuft (`systemctl status greiner-portal`)
- [ ] Ngrok Tunnel gestartet (`ngrok http 5000`)
- [ ] HTTPS-URL notiert (z.B. `https://abc123.ngrok-free.app`)

### **Twilio:**

- [ ] Twilio Console geöffnet
- [ ] Webhook-URL in Sandbox konfiguriert
- [ ] HTTP Method: `POST`
- [ ] Handy mit Sandbox verbunden (`join <code>`)

### **Testing:**

- [ ] Test-Nachricht gesendet
- [ ] Webhook empfängt Request (200 OK in Twilio Console)
- [ ] Nachricht in DB gespeichert
- [ ] Flask-Logs zeigen erfolgreiche Verarbeitung

---

## 🎯 NÄCHSTE SCHRITTE

**Nach erfolgreichem Testing:**

1. ✅ **DMZ-URL verwenden:**
   - Webhook-URL in Twilio auf `https://api.auto-greiner.de/whatsapp/webhook` ändern
   - Ngrok kann gestoppt werden

2. ✅ **Produktions-Testing:**
   - Webhook mit DMZ-URL testen
   - Signatur-Validierung prüfen

---

**Status:** 🚀 Schnellstart-Anleitung  
**Nächster Schritt:** Ngrok installieren und Tunnel starten
