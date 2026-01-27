# Twilio WhatsApp - Nächste Schritte

**TAG:** 211  
**Datum:** 2026-01-26  
**Status:** 🚀 **NÄCHSTE SCHRITTE**

---

## 🎯 WAS DU SIEHST

**Du siehst:**
- ✅ Account SID: `AC898fb7bdad556eb10bad3422bd79d430`
- ✅ Auth Token: `8beb1d33deabca8fcae5e30347f5f0f4` (sichtbar)
- ✅ From: `whatsapp:+14155238886` (Twilio Sandbox-Nummer)
- ✅ To: `whatsapp:+4917611199800` (Empfänger-Nummer)

---

## 📋 SCHRITT 1: CREDENTIALS NOTIEREN

### **1.1 Account SID**

**Du siehst im curl-Befehl:**
- Account SID: `AC898fb7bdad556eb10bad3422bd79d430`
- **Notiere diese!**

---

### **1.2 Auth Token**

**Du siehst im curl-Befehl:**
- Auth Token: `8beb1d33deabca8fcae5e30347f5f0f4`
- **Notiere diese!**

**Wichtig:**
- Token ist sichtbar, weil "Show auth token" angekreuzt ist
- Später: Token aus Sicherheitsgründen ausblenden

---

### **1.3 Sandbox-Nummer**

**Du siehst:**
- From: `whatsapp:+14155238886`
- **Notiere:** `whatsapp:+14155238886`

---

## ⚙️ SCHRITT 2: KONFIGURATION IN .ENV

### **2.1 .env Datei öffnen**

**Auf Server:**
```bash
nano /opt/greiner-portal/.env
```

**Oder via Windows-Sync:**
- Datei: `F:\Greiner Portal\Greiner_Portal_NEU\Server\.env`

---

### **2.2 Twilio-Variablen hinzufügen**

**Füge am Ende der Datei hinzu:**
```bash
# Twilio WhatsApp API (TAG 211)
TWILIO_ACCOUNT_SID=AC898fb7bdad556eb10bad3422bd79d430
TWILIO_AUTH_TOKEN=8beb1d33deabca8fcae5e30347f5f0f4
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
TWILIO_WEBHOOK_URL=https://auto-greiner.de/whatsapp/webhook
```

**Wichtig:**
- Ersetze die Werte mit deinen tatsächlichen Credentials
- Keine Leerzeichen um `=`
- Keine Anführungszeichen

---

## 🌐 SCHRITT 3: WEBHOOK KONFIGURIEREN

### **3.1 Webhook-URL in Twilio eintragen**

1. **Im Twilio Dashboard:**
   - Gehe zu: **Messaging** → **WhatsApp** → **Sandbox**
   - Tab: **"Sandbox settings"** (neben "Sandbox")

2. **Webhook-URL eintragen:**
   - **"When a message comes in":** `https://auto-greiner.de/whatsapp/webhook`
   - **"Status callback URL":** `https://auto-greiner.de/whatsapp/webhook`
   - **HTTP Method:** POST

3. **Speichern:**
   - Klicke auf **"Save"**

---

## 🐍 SCHRITT 4: PYTHON SDK INSTALLIEREN

### **4.1 Auf Server installieren**

**SSH zum Server:**
```bash
ssh ag-admin@10.80.80.20
```

**Dann:**
```bash
cd /opt/greiner-portal
source venv/bin/activate
pip install twilio --break-system-packages
```

**Prüfe Installation:**
```bash
python3 -c "import twilio; print(twilio.__version__)"
```

**Sollte zeigen:** `8.x.x` oder ähnlich

---

## 🔄 SCHRITT 5: SERVICE NEUSTARTEN

### **5.1 Service neustarten**

```bash
sudo systemctl restart greiner-portal
```

**Prüfe Status:**
```bash
sudo systemctl status greiner-portal
```

**Sollte zeigen:** `active (running)`

---

### **5.2 Logs prüfen**

```bash
journalctl -u greiner-portal -f
```

**Sollte zeigen:**
- Keine Fehler
- Service läuft

**Falls Fehler:**
- Prüfe ob `.env` korrekt ist
- Prüfe ob Twilio SDK installiert ist

---

## ✅ SCHRITT 6: TESTEN

### **6.1 Test-Nachricht senden**

**Via API (vom Server):**
```bash
curl -X POST http://localhost:5000/whatsapp/send \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{
    "to": "4917611199800",
    "message": "Test-Nachricht von DRIVE"
  }'
```

**Oder via UI:**
1. Gehe zu: `https://auto-greiner.de/whatsapp/contacts`
2. Klicke auf Kontakt
3. Sende Test-Nachricht

**Wichtig:**
- `to`: Nummer ohne `+` und ohne `whatsapp:` Prefix
- Format: `4917611199800` (nicht `+4917611199800`)

---

### **6.2 Eingehende Nachricht testen**

1. **Sende WhatsApp-Nachricht:**
   - Von deinem Handy an Sandbox-Nummer: `+1 415 523 8886`
   - Sende: "Hallo Test"

2. **Prüfe ob empfangen:**
   - Gehe zu: `https://auto-greiner.de/whatsapp/messages`
   - Sollte eingehende Nachricht zeigen

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
- Prüfe ob keine Leerzeichen um `=` sind

---

### **Problem 3: "Nachricht nicht gesendet"**

**Lösung:**
1. Prüfe Twilio Dashboard → **Monitor** → **Logs**
2. Prüfe Server-Logs: `journalctl -u greiner-portal -f`
3. Prüfe ob Empfänger-Nummer mit Sandbox verbunden ist

---

### **Problem 4: "Webhook nicht empfangen"**

**Lösung:**
1. Prüfe Webhook-URL in Twilio Dashboard
2. Prüfe ob URL öffentlich erreichbar ist (HTTPS!)
3. Prüfe Server-Logs: `journalctl -u greiner-portal -f`

---

## 📋 CHECKLISTE

### **Setup:**

- [ ] Account SID notiert (`AC898fb...`)
- [ ] Auth Token notiert (`8beb1d...`)
- [ ] Sandbox-Nummer notiert (`whatsapp:+14155238886`)
- [ ] Environment-Variablen in `.env` gesetzt
- [ ] Webhook-URL in Twilio konfiguriert
- [ ] Python SDK installiert (`pip install twilio`)
- [ ] Service neugestartet (`sudo systemctl restart greiner-portal`)

### **Testing:**

- [ ] Test-Nachricht gesendet
- [ ] Eingehende Nachricht getestet
- [ ] Nachrichten in UI sichtbar

---

## 🎯 NÄCHSTE SCHRITTE NACH SETUP

### **1. Sandbox testen:**

- ✅ Test-Nachrichten senden
- ✅ Eingehende Nachrichten empfangen
- ✅ UI testen

### **2. Für Produktion:**

- ⚠️ Eigene WhatsApp Business Nummer bei Twilio anfragen
- ⚠️ Nummer in `.env` aktualisieren
- ⚠️ Webhook-URL aktualisieren (falls nötig)

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

**Status:** 🚀 Nächste Schritte  
**Nächster Schritt:** Credentials in `.env` setzen und Service neustarten
