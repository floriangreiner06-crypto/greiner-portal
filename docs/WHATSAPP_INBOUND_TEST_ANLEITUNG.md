# WhatsApp Inbound testen

**TAG 211** – Eingehende Nachrichten (Twilio → DRIVE) prüfen.

---

## Option 1: Simulierter Inbound (ohne Twilio von außen)

Funktioniert, wenn der Webhook von außen noch nicht erreichbar ist (z. B. vor DMZ/ngrok).

1. **Test-Seite im Browser öffnen**
   - URL: `https://<dein-drive-host>/whatsapp/webhook/test`  
     (z. B. `https://drive.auto-greiner.de/whatsapp/webhook/test` oder mit `/drive`-Prefix, falls verwendet)

2. **Formular ausfüllen**
   - **From:** deine WhatsApp-Nummer im Twilio-Format, z. B. `whatsapp:+4917611199800`
   - **Body:** z. B. `Test eingehend aus Anleitung`
   - MessageSid/To können Standard bleiben.

3. **„Test Webhook“ klicken**
   - Der Server ruft den echten Webhook intern auf und speichert die Nachricht in der DB.

4. **Chat prüfen**
   - **Verkauf → WhatsApp Chat** öffnen.
   - Den Kontakt mit der eingetragenen From-Nummer auswählen.
   - Die simulierte eingehende Nachricht sollte im Verlauf erscheinen.

---

## Option 2: Echter Inbound (Twilio ruft unseren Server auf)

Voraussetzung: Webhook-URL ist von außen erreichbar (DMZ `api.auto-greiner.de` oder ngrok).

### A) Webhook-URL in Twilio eintragen

1. **Twilio Console:** https://console.twilio.com/
2. **Messaging** → **Try it out** → **Send a WhatsApp message**
3. **„When a message comes in“**
   - URL: `https://api.auto-greiner.de/whatsapp/webhook` (oder deine ngrok-URL + `/whatsapp/webhook`)
   - HTTP: **POST**
4. Speichern.

### B) Von Handy an Sandbox senden

1. **Sandbox verbinden** (falls noch nicht):  
   An die Twilio-Sandbox-Nummer (`+1 415 523 8886`) eine Nachricht senden:  
   `join <dein-code>` (Code aus der Twilio Sandbox-Seite).

2. **Echte Nachricht senden**  
   Von deinem Handy eine beliebige Nachricht **an** die Sandbox-Nummer senden (z. B. „Hallo DRIVE“).

3. **Im Portal prüfen**  
   - **Verkauf → WhatsApp Chat** öffnen.
   - Dein Kontakt (Handynummer) sollte erscheinen.
   - Die soeben gesendete Nachricht erscheint als eingehende Nachricht.

---

## Hinweise

- **Signatur:** Der echte Webhook prüft die Twilio-Signatur (`TWILIO_AUTH_TOKEN`). Bei Option 1 entfällt das (interner Aufruf).
- **Ngrok:** Für Tests ohne DMZ z. B. `ngrok http 5000` und in Twilio die ngrok-URL + `/whatsapp/webhook` eintragen (siehe `docs/TWILIO_WEBHOOK_TESTING_SCHNELLSTART_TAG211.md`).
