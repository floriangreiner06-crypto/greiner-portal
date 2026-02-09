# WhatsApp Verkäufer – Umgesetzt (ohne DMZ)

**Datum:** 2026-01-26  
**Status:** ✅ **WEITERENTWICKLUNG ABGESCHLOSSEN**

---

## ✅ Umgesetzt

### 1. Feature-Zugriff (`config/roles_config.py`)

- **`whatsapp_teile`:** admin, lager, werkstatt_leitung, service_leitung, serviceberater  
- **`whatsapp_verkauf`:** admin, verkauf_leitung, verkauf  

### 2. Navigation (`templates/base.html`)

- **Verkauf:** Menüpunkt „WhatsApp Chat“ (nur bei `whatsapp_verkauf`)
- **After Sales:** Menüpunkt „WhatsApp Teile“ (nur bei `whatsapp_teile`)

### 3. API für Verkäufer (`routes/whatsapp_routes.py`)

| Route | Methode | Beschreibung |
|-------|---------|--------------|
| `/whatsapp/verkauf/chat` | GET | Seite: Chat-UI |
| `/whatsapp/verkauf/chats` | GET | API: Liste Chats (Kontakte mit Nachrichten) |
| `/whatsapp/verkauf/messages/<contact_id>` | GET | API: Nachrichten eines Kontakts |
| `/whatsapp/verkauf/send` | POST | API: Nachricht senden (JSON: `to`, `message`) |
| `/whatsapp/verkauf/updates` | GET | API: Neue Nachrichten (Polling: `contact_id`, `last_message_id`) |

Zugriff auf alle Verkäufer-Routes nur mit Feature **`whatsapp_verkauf`** (sonst 403).

### 4. Chat-Interface (`templates/whatsapp/verkauf_chat.html`)

- Zwei Spalten: Kontakte links, Chat rechts
- Kontaktliste aus API `/whatsapp/verkauf/chats`
- Nachrichten pro Kontakt aus `/whatsapp/verkauf/messages/<id>`
- Senden über `/whatsapp/verkauf/send` (JSON: `to`, `message`)
- Polling alle 5 s für neue Nachrichten (`/whatsapp/verkauf/updates`)
- Suche in der Kontaktliste
- Anzeige: letzte Nachricht, Zeit, Ungelesen-Badge (falls vorhanden)

---

## Abhängigkeiten

- **Datenbank:** Tabellen/Views aus Migration (bereits ausgeführt)
- **Twilio:** Nur zum **Senden** nötig (Credentials in `.env`)
- **DMZ/Webhook:** Nur für **eingehende** Nachrichten von Twilio nötig

Lokal/ohne DMZ: Verkäufer können die Chat-UI nutzen, Chats anzeigen und senden, sobald Twilio konfiguriert ist. Eingehende Nachrichten erscheinen erst, wenn der Webhook öffentlich erreichbar ist (z. B. nach DMZ-Einrichtung).

---

## Nächste Schritte (optional)

- Service neu starten: `sudo systemctl restart greiner-portal`
- Nach DMZ: Nginx + SSL + Webhook-URL in Twilio
- Optional: Verkäufer-Dashboard (Übersicht Ungelesen, aktive Chats)
- Optional: Bild-Upload im Chat

---

**Status:** Weiterentwicklung ohne DMZ umgesetzt.  
**Nächster Schritt:** Service neu starten, dann Verkauf → „WhatsApp Chat“ testen.
