# WhatsApp – Weiterentwicklung ohne DMZ

**Datum:** 2026-01-26  
**Status:** ✅ **WEITERENTWICKLUNG MÖGLICH**

---

## Kurzantwort

**Ja, wir können weiter entwickeln.**  
Die DMZ wird nur für die **öffentliche Webhook-URL** gebraucht. Alles andere kann parallel entwickelt und lokal getestet werden.

---

## Was braucht die DMZ?

| Thema | Abhängigkeit von DMZ |
|--------|------------------------|
| **Webhook von Twilio empfangen** | ✅ Ja – Twilio braucht öffentliche HTTPS-URL |
| **Chat-UI, API, Berechtigungen** | ❌ Nein – alles lokal nutzbar |

---

## Was können wir jetzt bauen (ohne DMZ)?

### 1. Chat-Interface (Verkäufer)

- **Template:** `templates/whatsapp/verkauf_chat.html`
- **Inhalt:** Zwei Spalten (Kontakte links, Chat rechts), Nachrichtenliste, Eingabefeld
- **Test:** Lokal mit vorhandenen oder Mock-Daten
- **Aufwand:** ca. 4–6 h

### 2. API für Verkäufer

- **Routes:** z. B. `/whatsapp/verkauf/chats`, `/whatsapp/verkauf/messages/<contact_id>`, `/whatsapp/verkauf/send`, `/whatsapp/verkauf/updates`
- **Logik:** User-Filterung (nur eigene Chats), Channel „verkauf“
- **Test:** Lokal (z. B. mit Postman/curl oder Test-UI)
- **Aufwand:** ca. 2–3 h

### 3. Feature-Zugriff (Berechtigungen)

- **Datei:** `config/roles_config.py`
- **Inhalt:** z. B. `whatsapp_teile`, `whatsapp_verkauf` in `FEATURE_ACCESS`, Navigation anbinden
- **Test:** Lokal mit verschiedenen Rollen
- **Aufwand:** ca. 30 Min

### 4. Verkäufer-Dashboard

- **Template:** `templates/whatsapp/verkauf_dashboard.html`
- **Inhalt:** Karten (Ungelesen, aktive Chats), Chat-Liste, Schnellzugriff
- **Test:** Lokal mit Mock-/Test-Daten
- **Aufwand:** ca. 2–3 h

### 5. Lokales Webhook-Testing (optional)

- **Tool:** Ngrok oder Tunnelmole
- **Zweck:** Webhook testen, bevor DMZ steht
- **Abhängigkeit:** Keine DMZ nötig, nur Tunnel-URL in Twilio eintragen

---

## Was wartet auf die DMZ?

| Thema | Grund |
|--------|--------|
| **Twilio Webhook in Produktion** | Twilio braucht feste, öffentliche HTTPS-URL (z. B. `api.auto-greiner.de`) |
| **Nginx + SSL für Webhook** | Subdomain/DMZ muss vom ISP bereitgestellt sein |
| **Echte WhatsApp-Nachrichten von außen** | Erst wenn Webhook-URL erreichbar ist |

---

## Empfohlene Reihenfolge (ohne DMZ)

1. **Feature-Zugriff** (kurz, Basis für alles Weitere)
2. **API für Verkäufer** (Backend für Chat-UI)
3. **Chat-Interface** (Haupt-UI für Verkäufer)
4. **Verkäufer-Dashboard** (Übersicht, optional)

Wenn die DMZ-Angaben vom ISP da sind: Nginx + SSL + Twilio-Webhook-URL konfigurieren und testen.

---

## Zusammenfassung

- **Weiter entwickeln:** Ja, alles außer „Webhook von außen erreichbar machen“.
- **Warten auf DMZ:** Nur für öffentliche Webhook-URL und Produktionstest mit echten Twilio-Calls.
- **Lokal testen:** Chat, API, Berechtigungen und (mit Ngrok) auch den Webhook.

---

**Status:** Weiterentwicklung ohne DMZ möglich.  
**Nächster Schritt:** Z. B. Feature-Zugriff + API für Verkäufer, danach Chat-Interface.
