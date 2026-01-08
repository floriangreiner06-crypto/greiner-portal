# /fix - Bug analysieren und beheben

Analysiere und behebe einen Bug im Greiner Portal.

## Anweisungen

1. **Bug-Beschreibung sammeln:**
   - Was ist das erwartete Verhalten?
   - Was passiert stattdessen?
   - Wann tritt es auf?
   - Gibt es Fehlermeldungen?

2. **Logs prüfen:**
   ```bash
   ssh ag-admin@10.80.80.20 "journalctl -u greiner-portal --since '1 hour ago' | grep -i 'error\|exception\|traceback'"
   ```

3. **Code-Analyse:**
   - Identifiziere betroffene Dateien
   - Suche nach der Fehlerquelle
   - Prüfe verwandte Funktionen

4. **Fix implementieren:**
   - Minimale Änderung bevorzugen
   - Keine unnötigen Refactorings
   - Kommentiere komplexe Fixes

5. **Testen:**
   - Sync auf Server
   - Neustart falls nötig
   - Verifiziere den Fix

6. **Dokumentieren:**
   - Was war das Problem?
   - Was war die Lösung?

## Output
Kurze Zusammenfassung: Problem → Ursache → Lösung
