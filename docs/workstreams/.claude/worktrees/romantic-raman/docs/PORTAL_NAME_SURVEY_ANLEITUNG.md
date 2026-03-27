# Portal-Namen Umfrage - Anleitung zum Versenden

## 📧 E-Mail zur Validierung versenden

Die Umfrage-E-Mail kann auf dem Server versendet werden:

### Option 1: Auf dem Server ausführen (empfohlen)

```bash
# SSH zum Server
ssh ag-admin@10.80.80.20

# Zum Portal-Verzeichnis
cd /opt/greiner-portal

# Script ausführen (Empfänger ist bereits auf florian.greiner@auto-greiner.de gesetzt)
python3 scripts/send_portal_name_survey.py --send
```

### Option 2: Vorschau lokal ansehen

Die HTML-Vorschau wurde erstellt unter:
- `docs/portal_name_survey_preview.html`

Öffnen Sie diese Datei im Browser, um die E-Mail zu sehen.

### Option 3: Manuell versenden

1. Öffnen Sie `docs/portal_name_survey_preview.html` im Browser
2. Kopieren Sie den HTML-Inhalt
3. Versenden Sie als HTML-E-Mail über Outlook/Office 365

---

## 📝 Empfänger anpassen

Um die Umfrage an weitere Mitarbeiter zu senden, bearbeiten Sie:

**Datei:** `scripts/send_portal_name_survey.py`

**Zeile ~27:** Empfängerliste anpassen:
```python
SURVEY_RECIPIENTS = [
    'florian.greiner@auto-greiner.de',
    'geschaeftsfuehrung@auto-greiner.de',
    'werkstattleiter@auto-greiner.de',
    # ... weitere E-Mail-Adressen
]
```

---

## ✅ Nach der Validierung

Wenn die E-Mail validiert wurde:

1. Empfängerliste erweitern (siehe oben)
2. Deadline anpassen (standardmäßig 7 Tage)
3. Script auf dem Server ausführen: `python3 scripts/send_portal_name_survey.py --send`

---

## 📊 Antworten sammeln

Die Antworten kommen per E-Mail an `drive@auto-greiner.de` mit dem Betreff "Portal-Namen Umfrage".

**Format der Antworten:**
- "Meine Wahl: DRIVE"
- "Meine Wahl: PULSE"
- "Meine Wahl: CORE"
- "Meine Wahl: NEXUS"

