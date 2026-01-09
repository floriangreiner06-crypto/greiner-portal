# /session-start - Neue Arbeitssession starten

Starte eine neue Arbeitssession mit Kontext aus der letzten Session und Standards für neue Features.

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
   - Gibt es Qualitätsprobleme die behoben werden sollten

4. **Bestimme den aktuellen TAG:**
   - Basierend auf den Session-Dateien
   - Informiere den User über die aktuelle TAG-Nummer

5. **Frage den User:**
   - Womit sollen wir heute starten?
   - Gibt es neue Prioritäten?

6. **Erinnere an Standards für neue Features/Änderungen:**
   - SSOT-Prinzip beachten
   - Redundanzen vermeiden
   - Zentrale Funktionen verwenden

## Standards für neue Features/Änderungen

### SSOT-Prinzip (Single Source of Truth)
**⚠️ WICHTIG:** Immer zentrale Funktionen verwenden!

**Standort-Logik:**
- ✅ Verwende: `api/standort_utils.py`
- ❌ NICHT: Eigene Standort-Mappings erstellen

**DB-Verbindungen:**
- ✅ Verwende: `api/db_connection.py` → `get_db()`
- ✅ Verwende: `api/db_utils.py` → `get_locosoft_connection()`
- ❌ NICHT: Lokale `get_db()` Funktionen erstellen

**Lagerbestand:**
- ✅ Verwende: `api/teile_stock_utils.py` (TAG 176)
- ❌ NICHT: Eigene Lagerbestand-Queries schreiben

**Betriebs-Mappings:**
- ✅ Verwende: `api/standort_utils.py` → `BETRIEB_NAMEN`
- ❌ NICHT: Eigene Mappings in verschiedenen Dateien

### Redundanzen vermeiden
- [ ] Prüfe ob Funktion bereits existiert (z.B. in `api/db_utils.py`)
- [ ] Prüfe ob Mapping bereits existiert (z.B. in `api/standort_utils.py`)
- [ ] Prüfe ob ähnliche Logik bereits vorhanden ist

### Code-Duplikate vermeiden
- [ ] Ähnliche Code-Blöcke in Funktionen auslagern
- [ ] Gemeinsame Patterns in Utilities verschieben
- [ ] DRY-Prinzip beachten (Don't Repeat Yourself)

### Konsistenz
- [ ] SQL-Syntax: PostgreSQL-kompatibel (`%s`, `true`, `CURRENT_DATE`)
- [ ] Error-Handling: Konsistentes Pattern (try/except/finally)
- [ ] Imports: Zentrale Utilities importieren
- [ ] Logging: `logger = logging.getLogger(__name__)`

### Dokumentation
- [ ] Neue Features dokumentieren
- [ ] API-Endpoints dokumentieren
- [ ] Breaking Changes dokumentieren
- [ ] Beispiele in Code-Kommentaren

### Testing
- [ ] Service startet ohne Fehler
- [ ] Keine Warnings in Logs
- [ ] API-Endpoints funktionieren
- [ ] Frontend lädt ohne Fehler

## Checkliste vor Implementierung

**Vor dem Schreiben von Code:**
1. [ ] Prüfe ob ähnliche Funktionalität bereits existiert
2. [ ] Prüfe welche zentralen Funktionen verwendet werden sollten
3. [ ] Prüfe ob Mapping/Konstanten bereits existieren
4. [ ] Prüfe ob Pattern bereits etabliert ist

**Während der Implementierung:**
1. [ ] Verwende zentrale Funktionen (SSOT)
2. [ ] Vermeide Code-Duplikate
3. [ ] Verwende konsistente Patterns
4. [ ] Dokumentiere wichtige Entscheidungen

**Nach der Implementierung:**
1. [ ] Qualitätscheck durchführen (Redundanzen, SSOT)
2. [ ] Service testen
3. [ ] Logs prüfen
4. [ ] Dokumentation aktualisieren

## Output
Kurze Zusammenfassung der letzten Session, offenen Punkte und Erinnerung an Standards.

## Relevante Dokumentation
- `docs/QUALITAETSKONTROLLE_TAG176.md` - Qualitätskontrolle-Beispiel
- `docs/STANDORT_LOGIK_SSOT.md` - SSOT-Dokumentation
- `api/standort_utils.py` - SSOT für Standort-Logik
- `api/db_utils.py` - SSOT für DB-Verbindungen
- `api/teile_stock_utils.py` - SSOT für Lagerbestand (TAG 176)
