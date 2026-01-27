# Twilio WhatsApp Webhook - URL-Lösung

**TAG:** 211  
**Datum:** 2026-01-26  
**Status:** 🔧 **URL-PROBLEM LÖSUNG**

---

## 🎯 PROBLEM

**Situation:**
- ❌ `drive.auto-greiner.de` - Intranet (nicht öffentlich erreichbar)
- ❌ `www.auto-greiner.de` - Wird von Agentur betreut (kein Zugriff)
- ✅ **Webhooks brauchen öffentliche HTTPS-URL**

**Was brauchen wir:**
- ✅ Öffentlich erreichbare URL (HTTPS)
- ✅ Zugriff auf DNS/Server-Konfiguration
- ✅ Stabile URL (nicht nur für Tests)

---

## 💡 LÖSUNGSOPTIONEN

### **Option 1: Subdomain erstellen** ⭐⭐⭐⭐ **EMPFOHLEN**

**Vorgehen:**
- Neue Subdomain: `api.auto-greiner.de` oder `webhook.auto-greiner.de`
- DNS-Eintrag bei Domain-Provider erstellen
- Nginx Reverse Proxy konfigurieren

**Vorteile:**
- ✅ Professionell
- ✅ Stabile URL
- ✅ Eigene Kontrolle
- ✅ Keine Abhängigkeit von Agentur

**Nachteile:**
- ⚠️ Braucht DNS-Zugriff
- ⚠️ Braucht Server-Zugriff (Nginx-Konfiguration)

**Aufwand:** ~1-2 Stunden

---

### **Option 2: Ngrok/Tunnelmole (für Tests)** ⭐⭐⭐

**Vorgehen:**
- Tunnel-Service installieren (Ngrok, Tunnelmole, etc.)
- Lokaler Tunnel zu Server
- Öffentliche URL generieren

**Vorteile:**
- ✅ Schnell eingerichtet
- ✅ Keine DNS-Änderungen nötig
- ✅ Gut für Tests

**Nachteile:**
- ❌ URL ändert sich bei jedem Start (außer bezahlte Version)
- ❌ Nicht für Produktion geeignet
- ❌ Abhängigkeit von externem Service

**Aufwand:** ~15-30 Minuten

---

### **Option 3: Eigene Domain** ⭐⭐

**Vorgehen:**
- Eigene Domain registrieren (z.B. `greiner-drive.de`)
- DNS konfigurieren
- Nginx Reverse Proxy

**Vorteile:**
- ✅ Vollständige Kontrolle
- ✅ Keine Abhängigkeit

**Nachteile:**
- ⚠️ Zusätzliche Kosten (~10-15€/Jahr)
- ⚠️ DNS-Konfiguration nötig

**Aufwand:** ~2-3 Stunden

---

### **Option 4: Port-Forwarding + DynDNS** ⭐⭐

**Vorgehen:**
- Port-Forwarding in Firewall
- DynDNS-Service (z.B. No-IP, DuckDNS)
- Öffentliche IP verwenden

**Vorteile:**
- ✅ Keine Domain nötig
- ✅ Kostenlos (DynDNS)

**Nachteile:**
- ⚠️ Braucht Firewall-Zugriff
- ⚠️ Sicherheitsrisiko (Port öffnen)
- ⚠️ Nicht empfohlen für Produktion

**Aufwand:** ~1-2 Stunden

---

## 🎯 EMPFEHLUNG: SUBDOMAIN ERSTELLEN

### **Warum Subdomain?**

1. ✅ **Professionell** - Eigene Subdomain für API
2. ✅ **Stabil** - URL ändert sich nicht
3. ✅ **Kontrolle** - Eigene Verwaltung
4. ✅ **Sicherheit** - Nur Webhook-Endpoints öffentlich

---

## 📋 SCHRITT-FÜR-SCHRITT: SUBDOMAIN ERSTELLEN

### **Schritt 1: DNS-Eintrag erstellen**

**Bei Domain-Provider (z.B. Strato, 1&1, etc.):**

1. **DNS-Verwaltung öffnen**
2. **Neuen A-Record erstellen:**
   - **Name:** `api` (oder `webhook`)
   - **Typ:** A
   - **Wert:** `10.80.80.20` (Server-IP)
   - **TTL:** 3600 (1 Stunde)

3. **Ergebnis:**
   - `api.auto-greiner.de` → `10.80.80.20`
   - Oder: `webhook.auto-greiner.de` → `10.80.80.20`

**Wichtig:**
- DNS-Propagierung kann 1-24 Stunden dauern
- Prüfe mit: `nslookup api.auto-greiner.de`

---

### **Schritt 2: SSL-Zertifikat (Let's Encrypt)**

**Auf Server:**

```bash
# Certbot installieren
sudo apt install certbot python3-certbot-nginx -y

# SSL-Zertifikat erstellen
sudo certbot --nginx -d api.auto-greiner.de
```

**Oder manuell:**
```bash
sudo certbot certonly --standalone -d api.auto-greiner.de
```

---

### **Schritt 3: Nginx Reverse Proxy konfigurieren**

**Auf Server:**

```bash
sudo nano /etc/nginx/sites-available/api-auto-greiner
```

**Inhalt:**
```nginx
server {
    listen 80;
    server_name api.auto-greiner.de;
    
    # Redirect HTTP → HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.auto-greiner.de;
    
    # SSL-Zertifikat
    ssl_certificate /etc/letsencrypt/live/api.auto-greiner.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.auto-greiner.de/privkey.pem;
    
    # Nur Webhook-Endpoint öffentlich
    location /whatsapp/webhook {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Alle anderen Endpoints blockieren (Sicherheit)
    location / {
        return 403;
    }
}
```

**Aktivieren:**
```bash
sudo ln -s /etc/nginx/sites-available/api-auto-greiner /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### **Schritt 4: Firewall-Regeln**

**Port 80 und 443 öffnen (falls nicht bereits offen):**

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload
```

---

### **Schritt 5: Konfiguration aktualisieren**

**In `.env`:**
```bash
TWILIO_WEBHOOK_URL=https://api.auto-greiner.de/whatsapp/webhook
```

**In Twilio Dashboard:**
- Webhook-URL: `https://api.auto-greiner.de/whatsapp/webhook`

---

## 🔧 ALTERNATIVE: NGROK FÜR TESTS

### **Falls Subdomain nicht möglich:**

**Ngrok installieren:**
```bash
# Download
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar -xzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# Account erstellen (kostenlos)
# https://dashboard.ngrok.com/signup

# Auth Token setzen
ngrok config add-authtoken DEIN_TOKEN
```

**Tunnel starten:**
```bash
ngrok http 5000
```

**Ergebnis:**
- Öffentliche URL: `https://abc123.ngrok.io`
- Webhook-URL: `https://abc123.ngrok.io/whatsapp/webhook`

**Wichtig:**
- URL ändert sich bei jedem Start (außer bezahlte Version)
- Nur für Tests, nicht für Produktion!

---

## 🔧 ALTERNATIVE: TUNNELMOLE (Open Source)

**Installation:**
```bash
npm install -g tunnelmole
```

**Tunnel starten:**
```bash
tunnelmole 5000
```

**Ergebnis:**
- Öffentliche URL: `https://random-subdomain.tunnelmole.net`
- Webhook-URL: `https://random-subdomain.tunnelmole.net/whatsapp/webhook`

**Vorteile:**
- ✅ Kostenlos
- ✅ Open Source
- ✅ Keine Registrierung nötig

**Nachteile:**
- ❌ URL ändert sich bei jedem Start
- ❌ Nur für Tests

---

## 📊 VERGLEICH

| Lösung | Aufwand | Stabilität | Kosten | Empfehlung |
|--------|---------|------------|--------|------------|
| **Subdomain** | 1-2h | ✅ Sehr stabil | ✅ Kostenlos | ⭐⭐⭐⭐ |
| **Ngrok (kostenlos)** | 15 Min | ❌ URL ändert sich | ✅ Kostenlos | ⭐⭐⭐ (Tests) |
| **Ngrok (bezahlt)** | 15 Min | ✅ Stabil | ⚠️ ~$8/Monat | ⭐⭐⭐ |
| **Tunnelmole** | 15 Min | ❌ URL ändert sich | ✅ Kostenlos | ⭐⭐⭐ (Tests) |
| **Eigene Domain** | 2-3h | ✅ Sehr stabil | ⚠️ ~10-15€/Jahr | ⭐⭐ |

---

## 🎯 EMPFEHLUNG

### **Für Produktion:**

**Option 1: Subdomain erstellen** ⭐⭐⭐⭐
- `api.auto-greiner.de` oder `webhook.auto-greiner.de`
- Professionell, stabil, kostenlos

**Falls DNS-Zugriff nicht möglich:**
- Agentur kontaktieren
- Bitte um Subdomain-Eintrag

---

### **Für Tests (sofort):**

**Option 2: Ngrok/Tunnelmole** ⭐⭐⭐
- Schnell eingerichtet
- Für Tests ausreichend
- Später auf Subdomain wechseln

---

## 📋 CHECKLISTE

### **Subdomain-Lösung:**

- [ ] DNS-Zugriff vorhanden?
- [ ] A-Record erstellt (`api.auto-greiner.de` → `10.80.80.20`)
- [ ] DNS-Propagierung geprüft (`nslookup api.auto-greiner.de`)
- [ ] SSL-Zertifikat erstellt (Let's Encrypt)
- [ ] Nginx konfiguriert
- [ ] Firewall-Regeln gesetzt
- [ ] Webhook-URL in `.env` aktualisiert
- [ ] Webhook-URL in Twilio aktualisiert

### **Ngrok-Lösung (Tests):**

- [ ] Ngrok installiert
- [ ] Account erstellt
- [ ] Auth Token gesetzt
- [ ] Tunnel gestartet
- [ ] Webhook-URL in Twilio aktualisiert

---

## 🆘 FALLS DNS-ZUGRIFF NICHT MÖGLICH

### **Option A: Agentur kontaktieren**

**Frage an Agentur:**
- "Können Sie einen DNS-Eintrag für `api.auto-greiner.de` erstellen?"
- "Ziel-IP: `10.80.80.20`"
- "Für WhatsApp Webhook-Integration"

---

### **Option B: Ngrok für Tests, später Subdomain**

**Vorgehen:**
1. **Jetzt:** Ngrok für Tests verwenden
2. **Später:** Subdomain erstellen (wenn DNS-Zugriff vorhanden)
3. **Webhook-URL ändern:** In Twilio Dashboard

---

## 💡 TIPP

**Sicherheit:**
- Nur `/whatsapp/webhook` Endpoint öffentlich machen
- Alle anderen Endpoints blockieren (403)
- SSL-Zertifikat verwenden (HTTPS)

**Nginx-Konfiguration:**
```nginx
# Nur Webhook öffentlich
location /whatsapp/webhook {
    proxy_pass http://127.0.0.1:5000;
}

# Rest blockieren
location / {
    return 403;
}
```

---

**Status:** 🔧 URL-Problem Lösung  
**Empfehlung:** Subdomain erstellen (`api.auto-greiner.de`)  
**Alternative:** Ngrok für Tests (später auf Subdomain wechseln)
