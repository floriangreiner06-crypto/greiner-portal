# TODO für Claude - Session Start TAG 214

**Erstellt:** 2026-01-27  
**Letzte Session:** TAG 213 (Kontenübersicht - Sachkonto 071101 + Darlehen Peter Greiner)

---

## 📋 Offene Aufgaben

### Aus vorherigen Sessions
- Keine kritischen offenen Aufgaben

### Neue Aufgaben (optional, niedrige Priorität)
1. **Performance-Optimierung: Loco-Soft Saldo** (optional)
   - Loco-Soft Abfrage könnte gecacht werden, falls zu langsam
   - Aktuell wird bei jedem API-Call die Loco-Soft DB abgefragt

2. **Weitere Loco-Soft Konten** (optional)
   - Falls weitere Sachkonten aus Loco-Soft angezeigt werden sollen
   - Könnte ähnlich wie 071101 implementiert werden

---

## 🔍 Qualitätsprobleme die behoben werden sollten

**Keine kritischen Qualitätsprobleme**

Die Implementierung ist sauber und folgt SSOT-Prinzipien. Optional könnte die Loco-Soft Abfrage gecacht werden.

---

## 📝 Wichtige Hinweise für die nächste Session

### Was wurde in TAG 213 gemacht
- ✅ Sachkonto 071101 aus Loco-Soft in Kontenübersicht integriert
- ✅ Saldo-Berechnung korrigiert: HABEN - SOLL (41.000,00 €)
- ✅ Darlehen Peter Greiner: Bank-Name "Intern / Gesellschafter" ausgeblendet
- ✅ Kontoname geändert: "Darlehen Peter Greiner"
- ✅ Frontend-Anpassungen für Loco-Soft Konto (blauer Hintergrund, keine IBAN)

### Wichtige Dateien
- `api/bankenspiegel_api.py` - Hauptänderungen für Loco-Soft Saldo und Bank-Name Ausblendung
- `static/js/bankenspiegel_konten.js` - Frontend-Anpassungen
- `app.py` - STATIC_VERSION erhöht

### Bekannte Issues
- ✅ Alle gemeldeten Bugs behoben
- ✅ Saldo korrekt (41.000,00 €)
- ✅ Bank-Name ausgeblendet
- ✅ Kontoname korrekt

### Technische Details

**Loco-Soft Saldo:**
- Kontonummer: 71101 (5-stellig, Integer ohne führende Null)
- Berechnung: HABEN - SOLL (für Passivkonto/Darlehen)
- Fehlerbehandlung: try/except mit Logging

**Bank-Name Ausblendung:**
- SQL CASE WHEN: "Intern / Gesellschafter" → NULL
- Frontend zeigt keinen Bank-Namen, wenn NULL

**Frontend:**
- Loco-Soft Konto: Blauer Hintergrund (`table-info`), kein IBAN, kein Transaktionen-Button
- Bank-Name: Wird nur angezeigt, wenn vorhanden

---

## 🎯 Nächste Prioritäten

1. **User-Requests** - Warte auf neue Anforderungen
2. **Performance-Optimierung** - Optional: Loco-Soft Abfrage cachen
3. **Weitere Features** - Optional: Weitere Loco-Soft Konten integrieren

---

## 📚 Relevante Dokumentation

- `docs/sessions/SESSION_WRAP_UP_TAG213.md` - Letzte Session-Dokumentation
- `api/bankenspiegel_api.py` - Hauptdatei mit allen Änderungen
- `static/js/bankenspiegel_konten.js` - Frontend-Anpassungen

---

**Status:** ✅ Bereit für nächste Session  
**Nächste TAG:** 214
