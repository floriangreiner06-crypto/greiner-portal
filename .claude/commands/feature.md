# /feature - Neues Feature planen

Plane die Implementierung eines neuen Features.

## Anweisungen

1. **Anforderungen sammeln:**
   - Was soll das Feature tun?
   - Wer sind die Nutzer?
   - Welche Daten werden benötigt?

2. **Technische Analyse:**
   - Welche bestehenden Module sind betroffen?
   - Welche APIs müssen erstellt/erweitert werden?
   - Welche Templates werden benötigt?
   - Datenbankänderungen nötig?

3. **Architektur-Check:**
   - Prüfe bestehende ähnliche Features
   - Identifiziere wiederverwendbare Komponenten
   - Beachte das Greiner Portal Pattern:
     - API in `api/[modul]_api.py`
     - Routes in `routes/[modul]_routes.py`
     - Templates in `templates/[bereich]/`

4. **Todo-Liste erstellen:**
   - Erstelle strukturierte Aufgabenliste mit TodoWrite
   - Priorisiere nach Abhängigkeiten

5. **Zeitschätzung:**
   - Grobe Einschätzung der Komplexität (klein/mittel/groß)

## Output
Strukturierter Implementierungsplan mit konkreten Schritten.
