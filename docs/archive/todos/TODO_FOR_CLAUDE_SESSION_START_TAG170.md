# TODO für Claude - Session Start TAG 170

**Erstellt:** 2026-01-08  
**Letzte Session:** TAG 169 (Serviceberater-Benachrichtigungen bei Zeitüberschreitungen)

## 📋 Kontext aus letzter Session

In TAG 169 wurde das System für Serviceberater-Benachrichtigungen bei Zeitüberschreitungen implementiert:
- Celery-Task für E-Mail-Versand (alle 15 Min, Mo-Fr, 7-18 Uhr)
- Globales Modal im Base-Template (erscheint auf allen Seiten)
- API-Endpoint `/api/werkstatt/live/meine-ueberschreitungen`
- Bug-Fix: Abgeschlossene Aufträge werden jetzt auch erkannt

## 🎯 Prioritäten für TAG 170

### 1. Test-Modus entfernen (NIEDRIG)
- **Aktuell:** Task sendet immer Test-Mail an Florian
- **Aktion:** Test-Modus aus `celery_app/tasks.py` entfernen
- **Wann:** Nach erfolgreichem Test in Produktion

### 2. Celery Beat prüfen (MITTEL)
- **Aktion:** Prüfen ob Beat-Service läuft und Schedule aktiv ist
- **Befehl:** `sudo systemctl status celery-beat`
- **Falls nicht aktiv:** `sudo systemctl restart celery-beat`

### 3. Monitoring & Logs (MITTEL)
- **Aktion:** Logs prüfen ob E-Mails korrekt versendet werden
- **Befehl:** `journalctl -u celery-worker -f | grep ueberschreitung`
- **Prüfen:** Werden E-Mails wirklich gesendet? Gibt es Fehler?

### 4. Modal-Verhalten optimieren (NIEDRIG)
- **Option:** Mehrere Aufträge gleichzeitig anzeigen?
- **Option:** Liste mit "Weitere X Aufträge" Button?
- **Aktuell:** Zeigt nur ersten betroffenen Auftrag

## 🔍 Wichtige Dateien

### Geänderte Dateien (TAG 169):
- `api/werkstatt_live_api.py` - Neuer Endpoint + Logik für abgeschlossene Aufträge
- `celery_app/tasks.py` - Serviceberater-Benachrichtigungen Task
- `celery_app/__init__.py` - Task im Beat-Schedule
- `templates/base.html` - Globales Modal + Script

### Wichtige Endpoints:
- `/api/werkstatt/live/meine-ueberschreitungen` - Prüft User-Überschreitungen
- `/api/werkstatt/live/auftrag/<nr>` - Auftrag-Details

## ⚠️ Bekannte Issues

1. **Test-Modus aktiv**
   - Task sendet aktuell immer Test-Mail an Florian
   - Kann entfernt werden wenn alles stabil läuft

2. **Modal zeigt nur ersten Auftrag**
   - Wenn mehrere Überschreitungen, wird nur erste angezeigt
   - Eventuell Liste oder "Weitere X" Button?

## 📝 Nächste Schritte

1. **Session-Start:**
   - User fragen: Was ist die Priorität heute?
   - Test-Modus entfernen oder behalten?
   - Monitoring prüfen?

2. **Entwicklung:**
   - Je nach Priorität des Users
   - Falls keine klare Priorität: Monitoring & Logs prüfen

3. **Session-Ende:**
   - `/session-end` verwenden
   - Dokumentation erstellen
   - Git-Commit falls nötig

## 🔗 Referenzen

- Letzte Session: `docs/sessions/SESSION_WRAP_UP_TAG169.md`
- Projekt-Kontext: `CLAUDE.md`
- Celery-Config: `celery_app/__init__.py`
- API-Endpoint: `api/werkstatt_live_api.py` (Zeile 3957)

## 💡 Tipps

- **Celery Beat prüfen:** `sudo systemctl status celery-beat`
- **Logs prüfen:** `journalctl -u celery-worker -f | grep ueberschreitung`
- **Test-Modus:** Aktuell in `celery_app/tasks.py` Zeile ~257 (Test-Mail an Florian)
- **Modal:** Erscheint automatisch alle 30 Sekunden wenn Überschreitungen vorhanden
