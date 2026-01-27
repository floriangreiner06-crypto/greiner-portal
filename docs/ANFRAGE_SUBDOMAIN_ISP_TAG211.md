# DNS-Anfrage: Subdomain für WhatsApp Webhook

**An:** Florian Füeßl (Internet Service Provider)  
**Von:** [Dein Name]  
**Datum:** 2026-01-26  
**Betreff:** DNS-Eintrag für WhatsApp Webhook-Integration

---

## 📋 ANFRAGE

**Hallo Florian,**

wir benötigen einen **DNS-Eintrag** für eine neue Subdomain, um eine WhatsApp-Integration für unser Teile-Handelsgeschäft einzurichten.

---

## 🎯 WAS WIR BRAUCHEN

### **Subdomain:**
- **Name:** `api.auto-greiner.de`
- **Oder alternativ:** `webhook.auto-greiner.de`

### **DNS-Eintrag:**
- **Typ:** A-Record
- **Name:** `api` (oder `webhook`)
- **Ziel-IP:** `10.80.80.20`
- **TTL:** 3600 (Standard)

**Ergebnis:**
- `api.auto-greiner.de` → `10.80.80.20`

---

## 💡 ZWECK

**WhatsApp Webhook-Integration:**
- Wir integrieren WhatsApp für unser Teile-Handelsgeschäft
- Twilio (WhatsApp-Provider) benötigt eine **öffentlich erreichbare HTTPS-URL** für Webhooks
- Diese URL wird verwendet, um eingehende WhatsApp-Nachrichten zu empfangen

**Warum Subdomain:**
- `drive.auto-greiner.de` ist Intranet (nicht öffentlich erreichbar)
- `www.auto-greiner.de` wird von Agentur betreut (kein direkter Zugriff)
- Subdomain `api.auto-greiner.de` ermöglicht öffentlichen Zugriff nur auf Webhook-Endpoint

---

## 🔧 TECHNISCHE DETAILS

**Server:**
- **IP:** `10.80.80.20`
- **Port:** 5000 (intern, wird über Nginx Reverse Proxy erreichbar sein)
- **Service:** Greiner DRIVE Portal

**Webhook-Endpoint:**
- `https://api.auto-greiner.de/whatsapp/webhook`
- Nur dieser Endpoint wird öffentlich erreichbar sein
- Alle anderen Endpoints bleiben im Intranet

**SSL-Zertifikat:**
- Wir richten Let's Encrypt SSL-Zertifikat ein (nach DNS-Eintrag)
- HTTPS wird automatisch konfiguriert

---

## ⏰ ZEITRAHMEN

**Wann benötigt:**
- Sobald möglich (kein dringender Termin)
- Für Tests und Produktion

**DNS-Propagierung:**
- Normalerweise 1-24 Stunden nach Eintrag

---

## 📞 RÜCKFRAGE

**Falls Fragen:**
- Bitte melden, falls weitere Informationen benötigt werden
- Oder falls alternative Subdomain-Namen gewünscht sind

**Vielen Dank für die Unterstützung!**

---

**Mit freundlichen Grüßen**  
[Dein Name]  
Autohaus Greiner

---

## 📋 KURZVERSION (für E-Mail)

**Betreff:** DNS-Eintrag für WhatsApp Webhook-Integration

Hallo Florian,

wir benötigen einen DNS-Eintrag für eine neue Subdomain:

- **Subdomain:** `api.auto-greiner.de`
- **Typ:** A-Record
- **Ziel-IP:** `10.80.80.20`

**Zweck:** WhatsApp Webhook-Integration für unser Teile-Handelsgeschäft. Twilio benötigt eine öffentlich erreichbare HTTPS-URL für eingehende Nachrichten.

**Zeitraum:** Sobald möglich (kein dringender Termin)

Vielen Dank!

[Dein Name]
