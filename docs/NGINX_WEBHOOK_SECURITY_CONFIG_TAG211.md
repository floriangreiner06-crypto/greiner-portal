# Nginx Webhook Security Configuration

**TAG:** 211  
**Datum:** 2026-01-26  
**Status:** 🔒 **SICHERHEITS-KONFIGURATION**

---

## 🎯 ZWECK

**Sichere Nginx-Konfiguration für WhatsApp Webhook:**
- Nur Webhook-Endpoint öffentlich
- DDoS-Schutz (Rate Limiting)
- Nur POST erlaubt
- Alle anderen Endpoints blockiert

---

## 📋 NGINX-KONFIGURATION

### **Datei:** `/etc/nginx/sites-available/api-auto-greiner`

```nginx
# HTTP → HTTPS Redirect
server {
    listen 80;
    server_name api.auto-greiner.de;
    
    # Redirect HTTP → HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name api.auto-greiner.de;
    
    # SSL-Zertifikat (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.auto-greiner.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.auto-greiner.de/privkey.pem;
    
    # SSL-Konfiguration (Sicherheit)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Rate Limiting Zone (DDoS-Schutz)
    limit_req_zone $binary_remote_addr zone=webhook_limit:10m rate=10r/s;
    
    # Nur Webhook-Endpoint öffentlich
    location /whatsapp/webhook {
        # Rate Limiting (10 req/s, Burst: 5)
        limit_req zone=webhook_limit burst=5 nodelay;
        
        # Nur POST erlauben
        limit_except POST {
            deny all;
        }
        
        # Content-Type prüfen (nur JSON)
        if ($request_method != POST) {
            return 405;
        }
        
        # Proxy zu Flask-App
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 10s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
        
        # Body-Size-Limit (max. 1MB)
        client_max_body_size 1M;
    }
    
    # Alle anderen Endpoints blockieren (Sicherheit)
    location / {
        return 403;
    }
    
    # Logging
    access_log /var/log/nginx/api-auto-greiner-access.log;
    error_log /var/log/nginx/api-auto-greiner-error.log;
}
```

---

## 🔒 SICHERHEITS-FEATURES

### **1. Rate Limiting:**

**Konfiguration:**
- **Zone:** `webhook_limit`
- **Rate:** 10 Requests/Sekunde pro IP
- **Burst:** 5 Requests (kurze Spitzen erlaubt)
- **Schutz:** Verhindert DDoS-Angriffe

**Ergebnis:**
- Max. 10 Requests/Sekunde pro IP
- Bei Überschreitung: 503 Service Unavailable
- Schutz vor DDoS ✅

---

### **2. Nur POST erlaubt:**

**Konfiguration:**
```nginx
limit_except POST {
    deny all;
}
```

**Ergebnis:**
- GET, PUT, DELETE, etc. → 403 Forbidden
- Nur POST erlaubt ✅

---

### **3. Nur Webhook-Endpoint öffentlich:**

**Konfiguration:**
```nginx
location / {
    return 403;
}
```

**Ergebnis:**
- `/whatsapp/webhook` → ✅ Erlaubt
- `/`, `/admin`, etc. → ❌ 403 Forbidden
- Minimale Angriffsfläche ✅

---

### **4. Body-Size-Limit:**

**Konfiguration:**
```nginx
client_max_body_size 1M;
```

**Ergebnis:**
- Max. 1MB pro Request
- Schutz vor großen Payloads ✅

---

### **5. Timeouts:**

**Konfiguration:**
```nginx
proxy_connect_timeout 10s;
proxy_send_timeout 10s;
proxy_read_timeout 10s;
```

**Ergebnis:**
- Verbindungen werden nach 10s abgebrochen
- Schutz vor Slowloris-Angriffen ✅

---

## 🛡️ ZUSÄTZLICHE SICHERHEITSMASSNAHMEN

### **1. Fail2Ban (optional):**

**Installation:**
```bash
sudo apt install fail2ban
```

**Konfiguration:** `/etc/fail2ban/jail.local`
```ini
[nginx-webhook]
enabled = true
port = 443
filter = nginx-webhook
logpath = /var/log/nginx/api-auto-greiner-access.log
maxretry = 10
bantime = 3600
```

**Ergebnis:**
- Automatische IP-Sperre bei zu vielen Fehlversuchen
- Schutz vor Brute-Force-Angriffen ✅

---

### **2. Firewall-Regeln:**

**UFW (Uncomplicated Firewall):**
```bash
# Nur Port 443 erlauben
sudo ufw allow 443/tcp

# Port 80 erlauben (für Redirect)
sudo ufw allow 80/tcp

# Alle anderen Ports blockieren
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Firewall aktivieren
sudo ufw enable
```

**Ergebnis:**
- Nur Port 443 und 80 erreichbar
- Alle anderen Ports blockiert ✅

---

### **3. IP-Whitelist (optional, falls Twilio-IPs bekannt):**

**Nginx-Konfiguration:**
```nginx
# Twilio IP-Ranges (Beispiel - muss geprüft werden)
# allow 54.172.60.0/24;
# allow 54.244.51.0/24;
# deny all;
```

**Wichtig:**
- Twilio-IPs können sich ändern
- Nicht empfohlen (Rate Limiting reicht)

---

## 📊 MONITORING

### **1. Access-Logs überwachen:**

```bash
# Live-Logs
tail -f /var/log/nginx/api-auto-greiner-access.log

# Fehlerhafte Requests
grep " 403 " /var/log/nginx/api-auto-greiner-access.log

# Rate-Limit-Überschreitungen
grep "503" /var/log/nginx/api-auto-greiner-access.log
```

---

### **2. Traffic-Statistiken:**

```bash
# Requests pro Stunde
awk '{print $4}' /var/log/nginx/api-auto-greiner-access.log | cut -d: -f1-2 | sort | uniq -c

# Top IPs
awk '{print $1}' /var/log/nginx/api-auto-greiner-access.log | sort | uniq -c | sort -rn | head -10
```

---

## ✅ INSTALLATION

### **Schritt 1: Nginx-Konfiguration erstellen**

```bash
sudo nano /etc/nginx/sites-available/api-auto-greiner
```

**Inhalt:** (siehe oben)

---

### **Schritt 2: Konfiguration aktivieren**

```bash
sudo ln -s /etc/nginx/sites-available/api-auto-greiner /etc/nginx/sites-enabled/
sudo nginx -t  # Prüfe Konfiguration
sudo systemctl reload nginx
```

---

### **Schritt 3: SSL-Zertifikat (nach DNS-Eintrag)**

```bash
sudo certbot --nginx -d api.auto-greiner.de
```

---

### **Schritt 4: Firewall konfigurieren**

```bash
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp
sudo ufw reload
```

---

## 🧪 TESTING

### **1. Webhook-Endpoint testen:**

```bash
# POST-Request (sollte funktionieren)
curl -X POST https://api.auto-greiner.de/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# GET-Request (sollte 403 geben)
curl https://api.auto-greiner.de/whatsapp/webhook
```

---

### **2. Rate Limiting testen:**

```bash
# 20 Requests schnell senden (sollte Rate Limit auslösen)
for i in {1..20}; do
  curl -X POST https://api.auto-greiner.de/whatsapp/webhook \
    -H "Content-Type: application/json" \
    -d '{"test": "data"}'
done
```

**Erwartung:**
- Erste 10-15 Requests: 200 OK
- Weitere Requests: 503 Service Unavailable (Rate Limit)

---

### **3. Andere Endpoints testen:**

```bash
# Sollte 403 geben
curl https://api.auto-greiner.de/
curl https://api.auto-greiner.de/admin
```

---

## 📋 CHECKLISTE

### **Konfiguration:**

- [ ] Nginx-Konfiguration erstellt
- [ ] Rate Limiting konfiguriert
- [ ] Nur POST erlaubt
- [ ] Andere Endpoints blockiert
- [ ] SSL-Zertifikat installiert
- [ ] Firewall-Regeln gesetzt

### **Testing:**

- [ ] Webhook-Endpoint funktioniert (POST)
- [ ] GET-Request blockiert (403)
- [ ] Rate Limiting funktioniert
- [ ] Andere Endpoints blockiert (403)

---

**Status:** 🔒 Sicherheits-Konfiguration  
**Nächster Schritt:** Nach DNS-Eintrag: Nginx konfigurieren und SSL-Zertifikat installieren
