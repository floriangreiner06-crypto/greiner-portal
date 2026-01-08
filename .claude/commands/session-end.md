# /session-end - Arbeitssession beenden

Beende die aktuelle Session mit Dokumentation.

## Anweisungen

1. **Frage nach der TAG-Nummer** falls nicht bekannt

2. **Erstelle SESSION_WRAP_UP_TAG[X].md:**
   - Was wurde in dieser Session erledigt
   - Welche Dateien wurden geändert
   - Gibt es bekannte Issues

3. **Erstelle TODO_FOR_CLAUDE_SESSION_START_TAG[X+1].md:**
   - Offene Aufgaben
   - Nächste Schritte
   - Wichtige Hinweise für die nächste Session

4. **Git Status prüfen:**
   - Zeige uncommittete Änderungen
   - Frage ob Commit gewünscht

5. **Server-Sync Reminder:**
   - Erinnere an eventuell nicht gesyncte Dateien

## Speicherort
docs/sessions/
