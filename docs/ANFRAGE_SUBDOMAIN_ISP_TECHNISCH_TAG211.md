# DNS-Anfrage: Technische Details für ISP

**An:** Florian Füeßl (Internet Service Provider)  
**Von:** [Dein Name]  
**Datum:** 2026-01-26  
**Betreff:** DNS-Eintrag - Technische Details & Sicherheit

---

## 📋 ANFRAGE (ERWEITERT)

**Hallo Florian Füeßl,**

vielen Dank für die Rückfrage. Hier sind die technischen Details:

---

## 🌐 NETZWERK-ARCHITEKTUR

### **Server:**
- **IP-Adresse:** `10.80.80.20`
- **Server-Name:** auto-greiner.de
- **Standort:** Internes Netzwerk

### **Port:**
- **Port 443 (HTTPS)** - Standard HTTPS-Port
- **Port 80 (HTTP)** - Nur für Redirect zu HTTPS

**Wichtig:**
- Nur HTTPS wird verwendet (Port 443)
- HTTP (Port 80) leitet automatisch zu HTTPS um

---

## 🔒 SICHERHEIT & DDOS-SCHUTZ

### **1. Was wird öffentlich erreichbar sein:**

**Nur ein einziger Endpoint:**
- `https://api.auto-greiner.de/whatsapp/webhook`
- **Nur POST-Requests** (Webhook-Empfang)
- **Alle anderen Endpoints blockiert** (403 Forbidden)

**Nginx-Konfiguration:**
```nginx
# Nur Webhook-Endpoint öffentlich
location /whatsapp/webhook {
    proxy_pass http://127.0.0.1:5000;
    # Nur POST erlauben
    limit_except POST {
        deny all;
    }
}

# Alle anderen Endpoints blockieren
location / {
    return 403;
}
```

---

### **2. DDoS-Schutz-Maßnahmen:**

**A) Rate Limiting (Nginx):**
```nginx
# Max. 10 Requests pro Sekunde pro IP
limit_req_zone $binary_remote_addr zone=webhook_limit:10m rate=10r/s;

location /whatsapp/webhook {
    limit_req zone=webhook_limit burst=5;
    proxy_pass http://127.0.0.1:5000;
}
```

**B) IP-Whitelist (optional):**
```nginx
# Nur Twilio-IPs erlauben (falls bekannt)
# allow 54.172.60.0/24;  # Twilio IP-Range
# deny all;
```

**C) Firewall-Regeln:**
```bash
# Nur Port 443 von außen erreichbar
sudo ufw allow 443/tcp
sudo ufw deny 80/tcp  # HTTP blockieren (nur HTTPS)
```

**D) Fail2Ban (optional):**
- Automatische IP-Sperre bei zu vielen Fehlversuchen
- Schutz vor Brute-Force-Angriffen

---

### **3. Was wird NICHT öffentlich erreichbar sein:**

**Blockiert:**
- ❌ Alle anderen Endpoints (`/`, `/admin`, etc.)
- ❌ GET-Requests (nur POST für Webhook)
- ❌ Port 5000 (nur intern über Nginx)
- ❌ SSH, Datenbank, etc. (bleiben im Intranet)

**Ergebnis:**
- Nur **ein einziger Endpoint** ist öffentlich
- Nur **POST-Requests** werden akzeptiert
- **Rate Limiting** verhindert DDoS

---

## 📊 ERWARTETER TRAFFIC

### **Normaler Traffic:**

**Twilio Webhook:**
- **Frequenz:** ~1-10 Requests/Minute (bei normalem Betrieb)
- **Peak:** ~50-100 Requests/Minute (bei vielen Nachrichten)
- **Request-Größe:** ~1-5 KB pro Request
- **Bandbreite:** ~10-50 KB/Minute (sehr gering)

**Vergleich:**
- **Normale Webseite:** ~100-1000 Requests/Minute
- **WhatsApp Webhook:** ~1-10 Requests/Minute
- **Sehr geringer Traffic!**

---

### **DDoS-Schutz:**

**Rate Limiting:**
- Max. 10 Requests/Sekunde pro IP
- Burst: 5 Requests
- **Schutz vor DDoS:** ✅ Ja

**Firewall:**
- Nur Port 443 erreichbar
- Port 5000 bleibt intern
- **Schutz vor Port-Scans:** ✅ Ja

---

## 🔧 TECHNISCHE IMPLEMENTIERUNG

### **Nginx Reverse Proxy:**

**Konfiguration:**
```nginx
server {
    listen 443 ssl http2;
    server_name api.auto-greiner.de;
    
    # SSL-Zertifikat (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.auto-greiner.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.auto-greiner.de/privkey.pem;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=webhook_limit:10m rate=10r/s;
    
    # Nur Webhook-Endpoint öffentlich
    location /whatsapp/webhook {
        limit_req zone=webhook_limit burst=5;
        limit_except POST {
            deny all;
        }
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Alle anderen Endpoints blockieren
    location / {
        return 403;
    }
}
```

**Sicherheit:**
- ✅ Rate Limiting (10 req/s)
- ✅ Nur POST erlaubt
- ✅ Nur Webhook-Endpoint öffentlich
- ✅ SSL-Verschlüsselung (HTTPS)

---

## 🛡️ ZUSÄTZLICHE SICHERHEITSMAßNAHMEN

### **1. Fail2Ban (optional):**

**Installation:**
```bash
sudo apt install fail2ban
```

**Konfiguration:**
- Automatische IP-Sperre bei zu vielen Fehlversuchen
- Schutz vor Brute-Force-Angriffen

---

### **2. Cloudflare (optional):**

**Falls zusätzlicher Schutz gewünscht:**
- Cloudflare vor Nginx schalten
- DDoS-Schutz von Cloudflare
- Rate Limiting von Cloudflare

**Nachteile:**
- ⚠️ Zusätzliche Kosten (kostenlose Version verfügbar)
- ⚠️ Zusätzliche Latenz

---

### **3. Monitoring:**

**Logs überwachen:**
```bash
# Nginx Access-Logs
tail -f /var/log/nginx/access.log

# Fail2Ban-Logs
tail -f /var/log/fail2ban.log
```

**Alerts:**
- Bei ungewöhnlich hohem Traffic
- Bei vielen Fehlversuchen
- Bei DDoS-Verdacht

---

## 📋 ZUSAMMENFASSUNG FÜR ISP

### **Was wird benötigt:**

1. **DNS-Eintrag:**
   - Subdomain: `api.auto-greiner.de`
   - Typ: A-Record
   - Ziel-IP: `10.80.80.20`

2. **Port:**
   - **Port 443 (HTTPS)** - Standard HTTPS-Port
   - Port 80 (HTTP) - Nur für Redirect

3. **Verwendung:**
   - **Nur ein Endpoint:** `/whatsapp/webhook`
   - **Nur POST-Requests**
   - **Sehr geringer Traffic** (~1-10 Requests/Minute)

---

### **Sicherheitsmaßnahmen:**

✅ **Rate Limiting** (10 Requests/Sekunde pro IP)  
✅ **Nur Webhook-Endpoint öffentlich** (alle anderen blockiert)  
✅ **Nur POST erlaubt** (GET blockiert)  
✅ **SSL-Verschlüsselung** (HTTPS)  
✅ **Firewall-Regeln** (nur Port 443)  
✅ **Optional: Fail2Ban** (automatische IP-Sperre)

---

### **DDoS-Schutz:**

✅ **Rate Limiting** verhindert DDoS  
✅ **Nur ein Endpoint** reduziert Angriffsfläche  
✅ **Firewall** blockiert unerwünschten Traffic  
✅ **Monitoring** erkennt Angriffe frühzeitig

---

## 💡 EMPFEHLUNG

**Für ISP:**

1. **DNS-Eintrag erstellen:**
   - `api.auto-greiner.de` → `10.80.80.20`

2. **Firewall-Regeln (falls ISP verwaltet):**
   - Port 443 (HTTPS) erlauben
   - Port 80 (HTTP) erlauben (für Redirect)
   - Alle anderen Ports blockieren

3. **Monitoring (optional):**
   - Traffic überwachen
   - Bei ungewöhnlichem Traffic melden

---

## 📞 RÜCKFRAGE

**Falls weitere Informationen benötigt:**

- **Server-Zugriff:** Wir konfigurieren Nginx selbst
- **Firewall:** Falls ISP verwaltet, bitte Port 443 freigeben
- **Monitoring:** Wir überwachen Traffic selbst

**Vielen Dank für die Unterstützung!**

---

**Mit freundlichen Grüßen**  
[Dein Name]  
Autohaus Greiner
