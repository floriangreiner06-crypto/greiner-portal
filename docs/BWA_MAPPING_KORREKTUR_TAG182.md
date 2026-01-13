# BWA Mapping Korrektur - TAG 182

**Datum:** 2026-01-12  
**TAG:** 182  
**Status:** ⚠️ **IN ARBEIT**

---

## 🐛 PROBLEM

Die BWA-Werte für Dezember 2025 weichen von GlobalCube ab:
- **Unternehmensergebnis YTD:** Drive -260.135,91 € vs. GlobalCube -245.524,00 €
- **Differenz:** -14.611,91 €

**Ursache:** Die ursprüngliche Logik von TAG 177 (für August 2025 validiert) wurde geändert, aber die Logik für Dezember 2025 ist anders.

---

## 📋 URSPRÜNGLICHE LOGIK (TAG 177 - August 2025)

Laut `docs/LOESUNG_DIREKTE_KOSTEN_411XXX_489XXX_410021_TAG177.md`:

**Direkte Kosten:** 411xxx + 489xxx + 410021 sollten **AUS direkten Kosten AUSGESCHLOSSEN** werden.

**Validierung für August 2025:**
- DRIVE: 1.736.667,53 €
- GlobalCube: 1.736.691,52 €
- **Differenz:** 23,99 € ✅ (Rundungsdifferenz)

---

## 🔍 AKTUELLE SITUATION (Dezember 2025)

**Problem:** Die TAG 177 Logik führt zu falschen Werten für Dezember 2025:
- Direkte Kosten YTD: 625.530,17 € (TAG 177 Logik)
- GlobalCube Referenz: 659.229,00 €
- **Differenz:** -33.698,83 € ❌

**Analyse:**
- 411xxx YTD: 32.548,10 €
- 410021 YTD: 1.056,37 €
- 489xxx YTD: 1.803,26 € (gesamt), davon KST 1-7: 94,34 €, KST 0: 1.708,92 €

**Test:**
- Wenn 411xxx + 410021 enthalten wären: 659.134,64 € (Diff: -94,36 €) ✅
- Wenn nur 411xxx enthalten wäre: 658.078,27 € (Diff: -1.150,73 €)

---

## ✅ AKTUELLE KORREKTUR

**Implementiert:**
- ✅ 411xxx **IN direkten Kosten enthalten**
- ✅ 410021 **IN direkten Kosten enthalten**
- ✅ 489xxx **AUS direkten Kosten ausgeschlossen** (komplett)
- ✅ 489xxx (KST 0) **IN indirekten Kosten enthalten**
- ✅ 8910xx **AUS indirekten Kosten ausgeschlossen** (wie TAG 177)

**Ergebnis:**
- Direkte Kosten YTD: 659.134,64 € (GlobalCube: 659.229,00 €, Diff: -94,36 €) ✅
- Indirekte Kosten YTD: 838.937,55 € (GlobalCube: 838.944,00 €, Diff: -6,45 €) ✅
- Betriebsergebnis YTD: -390.408,99 € (GlobalCube: -375.797,00 €, Diff: -14.611,99 €) ⚠️

---

## ⚠️ VERBLEIBENDES PROBLEM

**Betriebsergebnis-Differenz:** -14.611,99 €

**Ursache:** DB2 ist falsch (-14.711,80 € Differenz), verursacht durch Umsatz (-14.711,89 € Differenz).

**Mögliche Ursachen:**
1. GlobalCube enthält andere Umsatz-Konten, die wir nicht haben
2. Filter-Logik für "Alle Standorte" ist falsch
3. Rundungsunterschiede zwischen PostgreSQL und Cognos
4. Unterschiedliche Zeiträume (GlobalCube könnte andere Monate enthalten)

---

## 🔄 LOGIK-UNTERSCHIEDE

### TAG 177 (August 2025):
- **Direkte Kosten:** 411xxx + 489xxx + 410021 **AUSGESCHLOSSEN**
- **Ergebnis:** 23,99 € Differenz ✅

### TAG 182 (Dezember 2025):
- **Direkte Kosten:** 411xxx + 410021 **ENTHALTEN**, 489xxx **AUSGESCHLOSSEN**
- **Ergebnis:** 94,36 € Differenz bei direkten Kosten ✅
- **Problem:** Betriebsergebnis-Differenz durch Umsatz-Differenz

---

## 📝 NÄCHSTE SCHRITTE

1. ⏳ **Umsatz-Differenz analysieren:**
   - Prüfen, welche Umsatz-Konten GlobalCube enthält, die wir nicht haben
   - Filter-Logik für "Alle Standorte" prüfen
   - Zeitraum-Vergleich (GlobalCube könnte andere Monate enthalten)

2. ⏳ **Validierung:**
   - Prüfen, ob die Logik für Dezember 2025 wirklich anders sein sollte
   - Oder ob die ursprüngliche TAG 177 Logik korrekt war und sich nur der Zeitraum geändert hat

3. ⏳ **Dokumentation aktualisieren:**
   - Logik-Unterschiede zwischen Zeiträumen dokumentieren
   - Oder Mapping-Fehler korrigieren

---

## 💡 HYPOTHESE

**Mögliche Erklärung:**
- Die TAG 177 Logik war für August 2025 (Sep 2024 - Aug 2025) korrekt
- Für Dezember 2025 (Sep-Dez 2025) könnte die Logik anders sein
- Oder: Die ursprüngliche Logik war falsch, und wir haben sie heute "korrigiert", aber das war ein Fehler

**Empfehlung:**
- Zur ursprünglichen TAG 177 Logik zurückkehren (411xxx + 489xxx + 410021 ausgeschlossen)
- Umsatz-Differenz separat analysieren
- Prüfen, ob die 23,99 € Differenz für Dezember 2025 auch gilt
