# TODO für Claude - Session Start TAG 215

**Erstellt:** 2026-01-27  
**Letzte Session:** TAG 214 (Kontenübersicht - Hypovereinsbank Eurokredit aus LocoSoft 070101)

---

## 📋 Offene Aufgaben

### Aus vorherigen Sessions
- Keine kritischen offenen Aufgaben

### Neue Aufgaben (optional, niedrige Priorität)
1. **Performance-Optimierung: LocoSoft Saldo** (optional)
   - LocoSoft Abfrage könnte gecacht werden, falls zu langsam
   - Aktuell wird bei jedem API-Call die LocoSoft DB abgefragt (für 071101 und 070101)

2. **Weitere LocoSoft Konten** (optional)
   - Falls weitere Sachkonten aus LocoSoft angezeigt werden sollen
   - Könnte ähnlich wie 071101 und 070101 implementiert werden

---

## 🔍 Qualitätsprobleme die behoben werden sollten

**Keine kritischen Qualitätsprobleme**

Die Implementierung ist sauber und folgt SSOT-Prinzipien. Optional könnte die LocoSoft Abfrage gecacht werden.

---

## 📝 Wichtige Hinweise für die nächste Session

### Was wurde in TAG 214 gemacht
- ✅ Hypovereinsbank Eurokredit (Konto 161401454) in Kontenübersicht integriert
- ✅ Saldo-Berechnung: HABEN - SOLL, dann negiert (-300.000,00 €)
- ✅ IBAN wird angezeigt: "Sachkonto Locosoft 070101"
- ✅ Frontend-Anpassungen: Blauer Hintergrund, IBAN angezeigt, kein Transaktionen-Button

### Wichtige Dateien
- `api/bankenspiegel_api.py` - Hauptänderungen für LocoSoft Saldo (070101)
- `static/js/bankenspiegel_konten.js` - Frontend-Anpassungen (IBAN-Anzeige)
- `app.py` - STATIC_VERSION erhöht

### Bekannte Issues
- ✅ Alle gemeldeten Bugs behoben
- ✅ Saldo korrekt (-300.000,00 €)
- ✅ IBAN wird angezeigt

### Technische Details

**LocoSoft Saldo:**
- Kontonummer: 70101 (5-stellig, Integer ohne führende Null)
- Berechnung: HABEN - SOLL, dann negiert (für Kredit/Schulden)
- Fehlerbehandlung: try/except mit Logging

**Frontend:**
- LocoSoft Konto: Blauer Hintergrund (`table-info`), IBAN wird angezeigt, kein Transaktionen-Button
- IBAN: Wird für alle Konten angezeigt (auch LocoSoft-Konten)

**Datenbank:**
- Neues Konto: ID 23, "Hypovereinsbank Eurokredit", Kontonummer: 161401454

---

## 🎯 Nächste Prioritäten

1. **User-Requests** - Warte auf neue Anforderungen
2. **Performance-Optimierung** - Optional: LocoSoft Abfrage cachen
3. **Weitere Features** - Optional: Weitere LocoSoft Konten integrieren

---

## 📚 Relevante Dokumentation

- `docs/sessions/SESSION_WRAP_UP_TAG214.md` - Letzte Session-Dokumentation
- `api/bankenspiegel_api.py` - Hauptdatei mit allen Änderungen
- `static/js/bankenspiegel_konten.js` - Frontend-Anpassungen

---

**Status:** ✅ Bereit für nächste Session  
**Nächste TAG:** 215
