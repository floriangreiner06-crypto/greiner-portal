# TODO für Claude - Session Start TAG 213

**Erstellt:** 2026-01-26  
**Letzte Session:** TAG 212 (Garantieakte - Kilometerstand & Diagnose-Informationen)

---

## 📋 Offene Aufgaben

### Aus vorherigen Sessions
- Keine kritischen offenen Aufgaben

### Neue Aufgaben (optional, niedrige Priorität)
1. **Code-Refactoring: GraphQL-Query** (optional)
   - `query_dossier` in gemeinsame Funktion auslagern
   - Wird aktuell in `hole_arbeitskarte_daten()` und Fallback-Logik dupliziert

2. **Dokumentation: GraphQL-Query-Struktur** (optional)
   - GraphQL-Query-Struktur für GUDAT dokumentieren
   - `workshopTasks` vs `workshopTaskPackages` erklären

3. **Monitoring: Diagnose-Informationen** (optional)
   - Diagnose-Informationen über längere Zeit beobachten
   - Prüfen ob alle Fälle korrekt abgedeckt sind

---

## 🔍 Qualitätsprobleme die behoben werden sollten

**Keine kritischen Qualitätsprobleme**

Die Implementierung ist sauber und folgt SSOT-Prinzipien. Optional könnte die GraphQL-Query in eine gemeinsame Funktion ausgelagert werden.

---

## 📝 Wichtige Hinweise für die nächste Session

### Was wurde in TAG 212 gemacht
- ✅ Kilometerstand-Korrektur: Verwendung von `order_mileage` statt `vehicles.mileage_km`
- ✅ Diagnose-Informationen: GraphQL-Query erweitert um `workshopTaskPackages` und `where`-Clause
- ✅ Fallback-Logik: Nachträgliches Holen von Diagnose-Informationen wenn Dossier in Anhänge-Suche gefunden wird
- ✅ Session-Handling: Neue Session für Diagnose-Query (um 401-Fehler zu vermeiden)
- ✅ Error-Handling: Robuste JSON-Response-Fehlerbehandlung
- ✅ Syntax-Fehler behoben: Einrückung des `except`-Blocks korrigiert

### Wichtige Dateien
- `api/arbeitskarte_api.py` - Hauptänderungen für Kilometerstand und Diagnose-Informationen
- `api/arbeitskarte_pdf.py` - PDF-Anzeige für Diagnose-Informationen

### Bekannte Issues
- ✅ Alle gemeldeten Bugs behoben
- ✅ Kilometerstand korrekt
- ✅ Diagnose-Informationen werden angezeigt
- ✅ API gibt immer JSON zurück

### Technische Details

**Kilometerstand:**
- Verwendet `COALESCE(o.order_mileage, v.mileage_km)` mit JOIN zu `orders`
- `order_mileage` ist historischer Kilometerstand zum Zeitpunkt des Auftrags

**Diagnose-Informationen:**
- GraphQL-Query holt Tasks aus zwei Quellen:
  1. `workshopTasks` (ohne Package) - mit `where`-Clause
  2. `workshopTaskPackages.workshopTasks` (in Packages)
- Fallback-Logik: Wenn `hole_arbeitskarte_daten()` kein Dossier findet, aber `get_arbeitskarte_anhaenge()` findet es, dann nachträgliches Holen
- Neue Session für Diagnose-Query (um 401-Fehler zu vermeiden)

**Error-Handling:**
- Prüfung von `response.status_code` und `Content-Type` vor JSON-Parsing
- Fallback-Mechanismus: Falls `jsonify` fehlschlägt, wird einfache JSON-Response zurückgegeben

---

## 🎯 Nächste Prioritäten

1. **User-Requests** - Warte auf neue Anforderungen
2. **Code-Refactoring** - Optional: GraphQL-Query in gemeinsame Funktion auslagern
3. **Dokumentation** - Optional: GraphQL-Query-Struktur dokumentieren

---

## 📚 Relevante Dokumentation

- `docs/sessions/SESSION_WRAP_UP_TAG212.md` - Letzte Session-Dokumentation
- `api/arbeitskarte_api.py` - Hauptdatei mit allen Änderungen
- `api/arbeitskarte_pdf.py` - PDF-Generierung
- `docs/stellantis/STELLANTIS_GARANTIE_IMPLEMENTIERUNG_TAG189.md` - Garantieakte-Feature-Übersicht

---

**Status:** ✅ Bereit für nächste Session  
**Nächste TAG:** 213
