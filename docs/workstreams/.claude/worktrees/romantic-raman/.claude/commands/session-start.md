# /session-start - Neue Arbeitssession starten

Starte eine neue Arbeitssession mit Kontext aus der letzten Session.

## Anweisungen

1. **Lies die Projekt-Dokumentation:**
   - CLAUDE.md (Hauptkontext)
   - Server/CLAUDE.md (technische Details)

2. **Finde die letzte Session:**
   - Suche in `docs/sessions/` nach dem neuesten `SESSION_WRAP_UP_TAG*.md`
   - Suche nach `TODO_FOR_CLAUDE_SESSION_START_TAG*.md`

3. **Lies beide Dateien** und fasse zusammen:
   - Was wurde zuletzt gemacht
   - Was sind die offenen Aufgaben
   - Gibt es bekannte Probleme

4. **Bestimme den aktuellen TAG:**
   - Basierend auf den Session-Dateien
   - Informiere den User über die aktuelle TAG-Nummer

5. **Frage den User:**
   - Womit sollen wir heute starten?
   - Gibt es neue Prioritäten?

## Output
Kurze Zusammenfassung der letzten Session und offenen Punkte.
