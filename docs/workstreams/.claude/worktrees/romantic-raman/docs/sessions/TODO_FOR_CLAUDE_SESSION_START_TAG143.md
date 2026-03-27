# TODO für Session TAG 143

**Erstellt:** 2025-12-29 (TAG 142)
**Vorgänger:** SESSION_WRAP_UP_TAG142.md
**Fokus:** Service-Neustarts + Tests (Survey & Penner-Verkaufschancen)

---

## 🎯 HAUPTAUFGABE: Umfrage-System testen & funktionsfähig machen

Die interaktive Portal-Namen Umfrage wurde erstellt, aber es gibt einen 404-Fehler beim Klick auf die Buttons. Der Service muss neu gestartet werden.

---

## ✅ SCHRITT 1: Service-Neustart (KRITISCH!)

**Problem:** Endpoint `/api/survey/portal-name` gibt 404  
**Ursache:** Blueprint wurde noch nicht geladen (Service nicht neugestartet)

**Aktion:**
```bash
# Auf Server (10.80.80.20)
sudo systemctl restart greiner-portal

# Logs prüfen
journalctl -u greiner-portal -n 50 | grep -i survey
```

**Erwartetes Ergebnis:**
- Log zeigt: "✅ Portal-Namen Umfrage API geladen"
- Keine Import-Fehler

---

## ✅ SCHRITT 2: Endpoint testen

**URL testen:**
```
http://drive.auto-greiner.de/api/survey/portal-name?choice=PULSE&email=test@example.com
```

**Erwartetes Ergebnis:**
- ✅ Bestätigungsseite erscheint (kein 404)
- ✅ Zeigt gewählte Option (PULSE)
- ✅ Formular mit E-Mail-Feld und Begründung
- ✅ "Auswahl bestätigen" Button

---

## ✅ SCHRITT 3: E-Mail erneut versenden

**Nach Service-Neustart:**
```bash
cd /opt/greiner-portal
source venv/bin/activate
python3 scripts/send_portal_name_survey.py --send --force
```

**Prüfen:**
- E-Mail kommt an
- 4 Buttons sind sichtbar
- Buttons sind klickbar

---

## ✅ SCHRITT 4: Button-Klick testen

**Aktion:**
1. Auf einen Button in der E-Mail klicken (z.B. PULSE)
2. Prüfen ob Bestätigungsseite erscheint
3. E-Mail-Adresse eingeben
4. Optional: Begründung hinzufügen
5. "Auswahl bestätigen" klicken

**Erwartetes Ergebnis:**
- ✅ Weiterleitung zur Bestätigungsseite
- ✅ Erfolgsseite nach Submit
- ✅ Daten in Datenbank gespeichert

---

## ✅ SCHRITT 5: Datenbank prüfen

**SQL-Abfrage:**
```sql
-- PostgreSQL
SELECT * FROM portal_name_survey ORDER BY submitted_at DESC;
```

**Oder via Python:**
```python
from api.db_utils import db_session

with db_session() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM portal_name_survey ORDER BY submitted_at DESC")
    for row in cursor.fetchall():
        print(row)
```

**Erwartetes Ergebnis:**
- ✅ Einträge vorhanden
- ✅ Korrekte Daten (email, choice, reason, submitted_at)

---

## ✅ SCHRITT 6: Ergebnisse abrufen (optional)

**Nach Test-Abstimmungen:**
```bash
python3 scripts/send_survey_results.py
```

**Prüfen:**
- E-Mail mit Ergebnissen kommt an florian.greiner@auto-greiner.de
- Zeigt alle Optionen mit Stimmenanzahl
- Zeigt Liste der Abstimmenden

---

## 🐛 BEKANNTE PROBLEME & LÖSUNGEN

### Problem 1: 404-Fehler
**Symptom:** Button-Klick führt zu 404  
**Lösung:** Service neustarten (siehe Schritt 1)

### Problem 2: Blueprint nicht geladen
**Symptom:** Log zeigt keine "✅ Portal-Namen Umfrage API geladen"  
**Lösung:** 
- Prüfe ob `api/portal_name_survey_api.py` existiert
- Prüfe ob Import-Fehler in Logs
- Prüfe `app.py` Zeile ~455

### Problem 3: Tabelle existiert nicht
**Symptom:** SQL-Fehler "relation does not exist"  
**Lösung:** Tabelle wird automatisch erstellt beim ersten Blueprint-Load. Falls nicht:
```python
from api.portal_name_survey_api import init_survey_table
init_survey_table()
```

---

## 📋 CHECKLISTE

- [ ] Service neugestartet
- [ ] Logs zeigen "✅ Portal-Namen Umfrage API geladen"
- [ ] Endpoint `/api/survey/portal-name` erreichbar (kein 404)
- [ ] E-Mail mit Buttons versendet
- [ ] Button-Klick funktioniert
- [ ] Bestätigungsseite erscheint
- [ ] Formular-Submit funktioniert
- [ ] Daten in Datenbank gespeichert
- [ ] Ergebnis-E-Mail funktioniert (optional)

---

## 🚀 NACH DEM TEST

Wenn alles funktioniert:

1. **Empfänger-Liste erweitern:**
   - `scripts/send_portal_name_survey.py` Zeile ~27
   - Weitere E-Mail-Adressen hinzufügen

2. **Umfrage an alle versenden:**
   ```bash
   python3 scripts/send_portal_name_survey.py --send --force
   ```

3. **Deadline notieren:** 04.01.2026 (7 Tage ab Versand)

4. **Nach Deadline:** Ergebnisse abrufen mit `send_survey_results.py`

---

## 📝 WICHTIGE DATEIEN

- `api/portal_name_survey_api.py` - API-Endpoint
- `scripts/send_portal_name_survey.py` - E-Mail-Versand
- `scripts/send_survey_results.py` - Ergebnis-Zusammenfassung
- `app.py` - Blueprint-Registrierung (Zeile ~455)
- `docs/portal_name_survey_preview.html` - Vorschau

---

## 💡 HINWEISE

1. **Service-Neustart ist KRITISCH** - ohne Neustart funktioniert nichts!

2. **E-Mail-Client:** Manche E-Mail-Clients blockieren Links. Falls Buttons nicht klickbar:
   - HTML-Vorschau in Browser öffnen
   - Oder Link manuell kopieren

3. **Datenbank:** PostgreSQL (drive_portal). Tabelle wird automatisch erstellt.

4. **Ergebnisse:** Werden automatisch per E-Mail gesendet, wenn `send_survey_results.py` ausgeführt wird.

---

**Viel Erfolg beim Testen!**

---

# TEIL 2: PENNER-VERKAUFSCHANCEN

## Service-Neustarts für Celery

### Celery Worker & Beat neustarten
```bash
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat
```

### Prüfen ob Penner-Tasks registriert
```bash
celery -A celery_app inspect registered | grep -i penner
```

Erwartet:
- `celery_app.tasks.update_penner_marktpreise`
- `celery_app.tasks.email_penner_weekly`

---

## Penner-Verkaufschancen testen

### Dashboard prüfen
URL: `http://drive.auto-greiner.de/werkstatt/renner-penner`
- Tab "Verkaufschancen" klicken
- Prüfen ob Marktpreise angezeigt werden
- Prüfen ob Lagerkosten-Spalten sichtbar

### Wöchentlichen Report testen
```bash
python3 scripts/send_weekly_penner_report.py --test-email florian.greiner@auto-greiner.de
```

---

## E-Mail-Adressen

**WICHTIG: Immer AD-Adressen mit Umlauten verwenden!**

Siehe: `docs/EMAIL_ADRESSEN_AD.md`

| Person | E-Mail (aus AD) |
|--------|-----------------|
| Florian Greiner | florian.greiner@auto-greiner.de |
| Matthias König | matthias.könig@auto-greiner.de |
| Rolf Sterr | rolf.sterr@auto-greiner.de |

---

## Lagerkosten-Formel (Referenz)

```
Lagerkosten = EK * (Tage/365) * 10%
Mindestpreis = EK + Lagerkosten (Breakeven)
Marge = Empf. VK - Mindestpreis
```

---

## Celery Beat Schedule (Referenz)

| Task | Zeitplan | Beschreibung |
|------|----------|--------------|
| `update_penner_marktpreise` | Täglich 3:00 | Marktpreise von eBay/Daparto |
| `email_penner_weekly` | Montag 7:00 | Wöchentlicher Report |

---

## Neue Dateien aus TAG 142

| Datei | Beschreibung |
|-------|--------------|
| `api/preisvergleich_service.py` | eBay/Daparto Scraping |
| `scripts/send_weekly_penner_report.py` | Wöchentlicher E-Mail Report |
| `scripts/send_verkaufschancen_doku.py` | Feature-Ankündigung |
| `docs/EMAIL_ADRESSEN_AD.md` | AD E-Mail-Adressen |
| `docs/ANLEITUNG_VERKAUFSCHANCEN.md` | Benutzer-Anleitung |

---

*Aktualisiert: 2025-12-29 - TAG 142 Session-End*
