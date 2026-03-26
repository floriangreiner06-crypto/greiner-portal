# n8n-Mockup: DRIVE Urlaubsplaner

**Dateien:**
- `n8n_mockup_urlaubsplaner.json` – Workflow zum **Import in n8n**
- `n8n_mockup_urlaubsplaner_README.md` – diese Anleitung
- `n8n_mockup_urlaubsplaner_preview.html` – **visuelle Vorschau** (ohne n8n im Browser öffnen)

---

## Import in n8n

1. n8n öffnen (lokal oder Self-Hosted).
2. **Workflows** → **Import from File** (oder Menü **…** → **Import from File**).
3. Datei `n8n_mockup_urlaubsplaner.json` auswählen.
4. Nach dem Import:
   - **Webhook-URL** prüfen (z. B. `https://<n8n>/webhook/drive-urlaubsplaner` oder Test-URL).
   - **E-Mail-Nodes:** Credentials anlegen (SMTP oder Microsoft 365), in den Knoten zuweisen.
   - **„Outlook: drive@ + MA-Kalender“:** Optional durch Microsoft-Graph-Kalender-Node ersetzen oder per HTTP-Request an Graph-API anpassen.
   - **Respond to Webhook:** Bleibt am Ende jeder Verzweigung, damit DRIVE eine Antwort erhält.

---

## Ablauf im Mockup

| Event (von DRIVE) | Ablauf in n8n |
|-------------------|----------------|
| **book** | Webhook → **5 Sek warten** → E-Mail an Genehmiger → Antwort |
| **approval** | Webhook → E-Mail an HR → E-Mail an MA → (optional) Outlook-Kalender → Antwort |
| **reject** | Webhook → E-Mail an MA (Ablehnung) → Antwort |
| **cancel** | Webhook → E-Mail an Genehmiger (Storno) → **Wenn was_approved:** E-Mail an HR → Antwort |
| **sickness** | Webhook → E-Mail an HR + Teamleitung + GL → Antwort |

DRIVE sendet pro Aufruf ein **event** und ein **payload** mit allen nötigen Daten (Empfänger, HTML-Texte, Buchungsdetails), damit n8n keine weiteren API-Calls zu DRIVE braucht.

---

## Payload-Beispiel (von DRIVE an n8n)

```json
{
  "body": {
    "event": "approval",
    "payload": {
      "employee_name": "Max Mustermann",
      "employee_email": "max@auto-greiner.de",
      "hr_emails": ["hr@auto-greiner.de"],
      "approver_emails": ["chef@auto-greiner.de"],
      "approver_name": "Lisa Vorgesetzte",
      "hr_mail_html": "<p>...</p>",
      "employee_mail_html": "<p>...</p>",
      "calendar_subject": "Urlaub Max Mustermann",
      "calendar_start": "2026-04-01T00:00:00",
      "calendar_end": "2026-04-02T00:00:00"
    }
  }
}
```

Die genaue Struktur würde die DRIVE-API beim Aufruf des Webhooks mitschicken (SSOT bleibt DRIVE).

---

## Hinweise

- **Credentials:** Im Mockup sind keine Credentials gespeichert; nach Import in n8n E-Mail- und ggf. Microsoft-Graph-Credentials anlegen und den Knoten zuweisen.
- **Node-Versionen:** Bei Inkompatibilität (ältere n8n-Version) Knotentypen ggf. anpassen (z. B. `emailSend` → aktueller Typ).
- **Kalender:** Der Knoten „Outlook: drive@ + MA-Kalender“ ist als HTTP-Request skizziert; in der Praxis evtl. zwei Microsoft-Graph-Kalender-Nodes (drive@ + User) oder ein eigener DRIVE-Endpoint, den n8n aufruft.

---

*Siehe auch: `URLAUBSPLANER_WORKFLOW_N8N_EINSCHAETZUNG.md` (Abschnitt 1 + 2).*
