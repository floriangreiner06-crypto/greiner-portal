# WhatsApp: Alternative ohne Webhook (für IT-Sicherheit)

**Ziel:** Kein öffentlich erreichbarer Endpoint für eingehende Twilio-Requests. Stattdessen holt unser Server die Nachrichten aktiv per **Polling** von der Twilio-API ab (nur ausgehende HTTPS-Verbindungen).

---

## Warum der Webhook als Risiko gesehen wird

- **Öffentlicher Endpoint:** `/whatsapp/webhook` muss von außen (Twilio) erreichbar sein.
- **Inbound-Verkehr:** POST-Requests aus dem Internet zum eigenen Server.
- Auch mit Signaturprüfung (X-Twilio-Signature) bleibt ein Angriffsfläche (z. B. DDoS, Fehlkonfiguration, „Kein Inbound“-Richtlinie).

---

## Alternative: Polling (empfohlen)

**Prinzip:** Unser Server fragt in festen Abständen bei Twilio nach neuen Nachrichten (REST-API). Es gibt **keinen** Webhook, **keine** öffentliche URL für Twilio.

| Aspekt | Webhook | Polling |
|--------|--------|--------|
| Inbound vom Internet | Ja (POST auf /whatsapp/webhook) | **Nein** |
| Verbindungsrichtung | Twilio → unser Server | Unser Server → api.twilio.com |
| Latenz neue Nachricht | Sofort | Intervall (z. B. 1–2 Min) |
| Konfiguration Twilio | Webhook-URL eintragen | **Keine Webhook-URL nötig** |

### Ablauf

1. Celery Beat startet periodisch **alle 30 Sekunden** den Task `fetch_whatsapp_inbound_polling`.
2. Der Task ruft die Twilio REST-API auf: „Liste eingehende Nachrichten seit Zeitpunkt X“.
3. Neue Nachrichten werden in der gleichen Weise in die DB übernommen wie bisher im Webhook (Kontakt anlegen/aktualisieren, Nachricht in `whatsapp_messages`).
4. Der Verkauf-Chat und die Teile-UI lesen weiter aus der DB – es ändert sich nur die Art, wie Nachrichten **reinkommen**.

### Konfiguration (ohne Webhook)

1. **Umgebung (z. B. `.env`):**
   ```bash
   WHATSAPP_USE_POLLING_INSTEAD_OF_WEBHOOK=true
   ```
   (Fehlt die Variable oder ist sie `false`, läuft weiter der Webhook wie bisher.)

2. **Twilio Console:**  
   Webhook-URL für eingehende Nachrichten **leer lassen** oder auf einen Platzhalter setzen. Twilio speichert eingehende Nachrichten; unser Polling holt sie ab.

3. **Firewall/Reverse-Proxy:**  
   `/whatsapp/webhook` kann von außen **blockiert** oder gar nicht erst ausgeliefert werden (z. B. Route entfernen oder 404). Dann ist nur noch Polling aktiv.

4. **Celery:**  
   Worker und Beat müssen laufen; der Task `fetch_whatsapp_inbound_polling` ist im Beat-Schedule (z. B. alle 2 Minuten) eingetragen.

### Nachteile Polling (kurz)

- Neue Nachrichten erscheinen mit Verzögerung (bis zu 30 Sekunden).
- Status-Updates (z. B. „delivered“, „read“) für **ausgehende** Nachrichten kommen nicht mehr per Webhook; optional können wir sie ebenfalls per Polling nachziehen (separater Task oder gleicher Task).

---

## Empfehlung für den IT-Admin

- **Sicherheitsrichtlinie „Kein Inbound für App-X“:**  
  Polling nutzen: `WHATSAPP_USE_POLLING_INSTEAD_OF_WEBHOOK=true` setzen, Webhook-URL in Twilio leer lassen, `/whatsapp/webhook` von außen nicht erreichbar machen (oder in der App deaktivieren).

- **Wenn der Webhook erlaubt bleibt:**  
  `WHATSAPP_USE_POLLING_INSTEAD_OF_WEBHOOK` weglassen oder `false` lassen. Webhook wie bisher nutzen; Signaturprüfung und Limits bleiben aktiv.

Technische Details: siehe `api/whatsapp_api.py` (u. a. `fetch_inbound_messages`), Celery-Task `fetch_whatsapp_inbound_polling` in `celery_app/tasks.py`, Beat-Schedule in `celery_app/__init__.py`.
