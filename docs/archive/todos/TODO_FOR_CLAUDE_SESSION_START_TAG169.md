# TODO für Claude - Session Start TAG 169

**Erstellt:** 2026-01-08  
**Letzte Session:** TAG 168 (Cursor-Konfiguration wiederhergestellt)

## 📋 Kontext aus letzter Session

In TAG 168 wurde die Cursor-Konfiguration nach einem Absturz wiederhergestellt:
- `.cursorrules` mit erweiterten Regeln
- Code-Snippets für häufige Aufgaben
- 10 Custom Commands (session-start, session-end, commit, deploy, etc.)

## 🎯 Prioritäten für TAG 169

### 1. Git-Status aufräumen (HOCH)
- **Problem:** 19 geänderte Dateien + 100+ untracked Dateien
- **Aktion:** 
  - Entscheiden welche untracked Dateien behalten werden sollen
  - Geänderte Dateien committen oder stashen
  - Git-Status bereinigen

### 2. Geänderte Dateien reviewen (HOCH)
- **Werkstatt-API Änderungen:**
  - `api/werkstatt_live_api.py` - +1672 Zeilen
  - `api/werkstatt_api.py` - 1651 Zeilen geändert
  - `api/werkstatt_data.py` - 242 Zeilen geändert
- **Planungsformulare:**
  - `templates/planung/fragen_werkstatt.html` - 345 Zeilen geändert
  - `templates/planung/abteilungsleiter_formular.html` - 154 Zeilen geändert
- **Celery-Tasks:**
  - `celery_app/tasks.py` - 731 Zeilen geändert

### 3. Commands testen (MITTEL)
- `/session-start` in neuer Session testen
- Andere Commands testen (commit, deploy, status, etc.)
- Feedback sammeln ob Commands wie erwartet funktionieren

### 4. Dokumentation aktualisieren (NIEDRIG)
- Session-Dokumentation prüfen
- README aktualisieren falls nötig
- Code-Kommentare bei größeren Änderungen ergänzen

## 🔍 Wichtige Dateien zu prüfen

### Geänderte API-Dateien:
- `api/werkstatt_live_api.py` - Größte Änderung, sollte reviewt werden
- `api/werkstatt_api.py` - Viele Änderungen
- `api/abteilungsleiter_planung_data.py` - 604 Zeilen geändert
- `api/controlling_api.py` - 30 Zeilen geändert
- `api/db_connection.py` - 9 Zeilen geändert
- `api/standort_utils.py` - 165 Zeilen geändert

### Geänderte Templates:
- `templates/aftersales/werkstatt_cockpit.html` - 293 Zeilen geändert
- `templates/aftersales/werkstatt_uebersicht.html` - 50 Zeilen geändert
- `templates/planung/fragen_werkstatt.html` - 345 Zeilen geändert
- `templates/planung/abteilungsleiter_formular.html` - 154 Zeilen geändert

### Geänderte Routes:
- `routes/planung_routes.py` - 113 Zeilen geändert
- `routes/werkstatt_routes.py` - 7 Zeilen geändert

### Andere:
- `app.py` - 16 Zeilen geändert
- `celery_app/tasks.py` - 731 Zeilen geändert

## ⚠️ Bekannte Issues

1. **Viele untracked Dateien**
   - Viele Scripts und Analyse-Dateien
   - Entscheidung nötig: behalten oder löschen?

2. **Geänderte Dateien nicht committed**
   - Seit TAG 167 keine Commits
   - Änderungen sollten reviewt und committed werden

3. **Commands noch nicht getestet**
   - Commands wurden wiederhergestellt, aber noch nicht in Cursor getestet

## 📝 Nächste Schritte

1. **Session-Start:**
   - Git-Status prüfen
   - User fragen: Was ist die Priorität heute?
   - Geänderte Dateien reviewen oder committen?

2. **Entwicklung:**
   - Je nach Priorität des Users
   - Falls keine klare Priorität: Git-Status aufräumen

3. **Session-Ende:**
   - `/session-end` verwenden
   - Dokumentation erstellen
   - Git-Commit falls nötig

## 🔗 Referenzen

- Letzte Session: `docs/sessions/SESSION_WRAP_UP_TAG168.md`
- Projekt-Kontext: `CLAUDE.md`
- Cursor-Rules: `.cursorrules`
- Commands: `.claude/commands/`

## 💡 Tipps

- **Commands verwenden:** Die wiederhergestellten Commands können mit `@` verwendet werden
- **Code-Snippets:** Vorgefertigte Snippets für häufige Aufgaben nutzen
- **Git-Status:** Erst aufräumen, dann neue Features entwickeln
