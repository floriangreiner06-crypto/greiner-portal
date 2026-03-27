# TODO für Claude - Session Start TAG 171

**Erstellt:** 2026-01-08  
**Letzte Session:** TAG 170 (Analyse - Werkstatt-KPIs)

## 📋 Kontext aus letzter Session

In TAG 170 wurde eine Analyse-Frage beantwortet:
- **Frage:** Was passiert mit Sascha's KPIs wenn er einen Hyundai-Auftrag stempelt?
- **Antwort:** Die Zeit wird in Sascha's Landau-KPIs gezählt (korrekt, da Aufträge zum Mechaniker gehören)
- **Code-Analyse:** `api/werkstatt_data.py::get_mechaniker_leistung()`
- **Ergebnis:** Verhalten ist korrekt und gewollt

## 🎯 Prioritäten für TAG 171

### 1. Uncommittete Änderungen prüfen (HOCH)
- **Status:** Es gibt uncommittete Änderungen aus vorherigen Sessions
- **Dateien:**
  - `api/parts_api.py`
  - `api/werkstatt_live_api.py`
  - `app.py`
  - `celery_app/tasks.py`
  - `routes/app.py`
  - `templates/base.html`
  - `templates/sb/mein_bereich.html`
- **Aktion:** Prüfen ob diese committed werden sollen
- **Befehl:** `git diff` um Änderungen zu sehen

### 2. Offene Punkte aus TAG 170 (MITTEL)
- **Test-Modus entfernen** (optional)
  - Task sendet aktuell immer Test-Mail an Florian
  - Kann entfernt werden wenn alles stabil läuft
- **Celery Beat prüfen**
  - Prüfen ob Beat-Service läuft
  - `sudo systemctl status celery-beat`
- **Monitoring & Logs**
  - Logs prüfen ob E-Mails korrekt versendet werden
  - `journalctl -u celery-worker -f | grep ueberschreitung`

### 3. Modal-Verhalten optimieren (NIEDRIG)
- **Option:** Mehrere Aufträge gleichzeitig anzeigen?
- **Option:** Liste mit "Weitere X Aufträge" Button?
- **Aktuell:** Zeigt nur ersten betroffenen Auftrag

## 🔍 Wichtige Dateien

### Geänderte Dateien (aus vorherigen Sessions):
- `api/werkstatt_live_api.py` - Serviceberater-Benachrichtigungen (TAG 169)
- `celery_app/tasks.py` - Serviceberater-Benachrichtigungen Task (TAG 169)
- `templates/base.html` - Globales Modal (TAG 169)
- `api/parts_api.py` - Unbekannte Änderungen
- `app.py` - Unbekannte Änderungen
- `routes/app.py` - Unbekannte Änderungen
- `templates/sb/mein_bereich.html` - Unbekannte Änderungen

### Wichtige Endpoints:
- `/api/werkstatt/live/meine-ueberschreitungen` - Prüft User-Überschreitungen
- `/api/werkstatt/live/auftrag/<nr>` - Auftrag-Details

## ⚠️ Bekannte Issues

1. **Uncommittete Änderungen**
   - Mehrere Dateien haben uncommittete Änderungen
   - Sollten diese committed werden?

2. **Test-Modus aktiv** (aus TAG 170)
   - Task sendet aktuell immer Test-Mail an Florian
   - Kann entfernt werden wenn alles stabil läuft

3. **Modal zeigt nur ersten Auftrag** (aus TAG 170)
   - Wenn mehrere Überschreitungen, wird nur erste angezeigt
   - Eventuell Liste oder "Weitere X" Button?

## 📝 Nächste Schritte

1. **Session-Start:**
   - User fragen: Was ist die Priorität heute?
   - Uncommittete Änderungen prüfen?
   - Test-Modus entfernen oder behalten?
   - Monitoring prüfen?

2. **Entwicklung:**
   - Je nach Priorität des Users
   - Falls keine klare Priorität: Uncommittete Änderungen prüfen

3. **Session-Ende:**
   - `/session-end` verwenden
   - Dokumentation erstellen
   - Git-Commit falls nötig

## 🔗 Referenzen

- Letzte Session: `docs/sessions/SESSION_WRAP_UP_TAG170.md`
- Projekt-Kontext: `CLAUDE.md`
- Celery-Config: `celery_app/__init__.py`
- Werkstatt-Data: `api/werkstatt_data.py` (Zeile 88-264)

## 💡 Tipps

- **Git Status:** `git status` zeigt uncommittete Änderungen
- **Git Diff:** `git diff` zeigt Änderungen in Dateien
- **Celery Beat prüfen:** `sudo systemctl status celery-beat`
- **Logs prüfen:** `journalctl -u celery-worker -f | grep ueberschreitung`
- **Test-Modus:** Aktuell in `celery_app/tasks.py` (Test-Mail an Florian)
- **Modal:** Erscheint automatisch alle 30 Sekunden wenn Überschreitungen vorhanden

## 📌 Wichtige Erkenntnisse aus TAG 170

- **KPIs werden nach Mechaniker aggregiert**, nicht nach Betrieb des Auftrags
- Wenn ein Mechaniker aus Landau einen Hyundai-Auftrag stempelt, zählt das in seine Landau-KPIs
- Das ist das gewünschte Verhalten
- Code-Stelle: `api/werkstatt_data.py::get_mechaniker_leistung()` (Zeile 88-264)
