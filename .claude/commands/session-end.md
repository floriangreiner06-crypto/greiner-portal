# /session-end - Arbeitssession beenden

Beende die aktuelle Session mit Dokumentation und Qualitätscheck.

## Anweisungen

1. **Frage nach der TAG-Nummer** falls nicht bekannt

2. **Qualitätscheck für Neuentwicklungen durchführen:**
   - Prüfe auf Redundanzen (doppelte Dateien, doppelte Funktionen)
   - Prüfe SSOT-Konformität (verwendet zentrale Funktionen?)
   - Prüfe Code-Duplikate
   - Prüfe Konsistenz (DB-Verbindungen, Imports, Patterns)
   - Dokumentiere gefundene Probleme in SESSION_WRAP_UP

3. **Erstelle SESSION_WRAP_UP_TAG[X].md:**
   - Was wurde in dieser Session erledigt
   - Welche Dateien wurden geändert
   - Qualitätscheck-Ergebnisse (Redundanzen, SSOT-Verletzungen)
   - Gibt es bekannte Issues

4. **Erstelle TODO_FOR_CLAUDE_SESSION_START_TAG[X+1].md:**
   - Offene Aufgaben
   - Nächste Schritte
   - Qualitätsprobleme die behoben werden sollten
   - Wichtige Hinweise für die nächste Session

5. **Git Status prüfen:**
   - Zeige uncommittete Änderungen
   - Frage ob Commit gewünscht

6. **Server-Sync Reminder:**
   - Erinnere an eventuell nicht gesyncte Dateien

## Qualitätscheck-Checkliste

### Redundanzen
- [ ] Gibt es doppelte Dateien? (z.B. `standort_utils.py` in Root und `api/`)
- [ ] Gibt es doppelte Funktionen? (gleiche Logik an mehreren Stellen)
- [ ] Gibt es doppelte Mappings/Konstanten? (z.B. `STANDORTE`, `BETRIEB_NAMEN`)

### SSOT-Konformität
- [ ] Werden zentrale Funktionen verwendet? (`api/standort_utils.py`, `api/db_utils.py`)
- [ ] Gibt es lokale Implementierungen statt SSOT? (z.B. eigene `get_db()` Funktion)
- [ ] Werden zentrale Mappings verwendet? (Standort, Betrieb, etc.)

### Code-Duplikate
- [ ] Gibt es kopierte Code-Blöcke die in Funktionen ausgelagert werden sollten?
- [ ] Gibt es ähnliche Patterns die vereinheitlicht werden können?

### Konsistenz
- [ ] DB-Verbindungen: Werden `get_db()`, `get_locosoft_connection()` korrekt verwendet?
- [ ] Imports: Werden zentrale Utilities importiert?
- [ ] SQL-Syntax: PostgreSQL-kompatibel? (`%s` statt `?`, `true` statt `1`)
- [ ] Error-Handling: Konsistentes Pattern?

### Dokumentation
- [ ] Neue Features dokumentiert?
- [ ] API-Endpoints dokumentiert?
- [ ] Breaking Changes dokumentiert?

## Speicherort
docs/sessions/

## Qualitätscheck-Tools

```bash
# Doppelte Dateien finden
find . -name "*.py" -type f | sort | uniq -d

# Doppelte Funktionen finden (grep nach Funktionsnamen)
grep -r "^def " api/ | sort | uniq -d

# SSOT-Verletzungen finden (z.B. lokale get_db)
grep -r "def get_db" --exclude-dir=api/db_connection.py
```
