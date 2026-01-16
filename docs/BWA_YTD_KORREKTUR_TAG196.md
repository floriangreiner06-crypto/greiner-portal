# BWA YTD Korrektur - TAG 196

**Datum:** 2026-01-16  
**Status:** ✅ Korrektur implementiert

---

## 🐛 PROBLEM

**YTD Betriebsergebnis bis Dezember 2025:**
- DRIVE: -405.863,59 €
- GlobalCube: -245.733,00 €
- **Differenz: -160.130,59 €** (DRIVE zu negativ)

**Ursache:** 498001 wurde nicht aus indirekten Kosten YTD ausgeschlossen!

---

## ✅ KORREKTUR

**Änderung:** 498001 wird jetzt aus indirekten Kosten ausgeschlossen (alle Stellen).

**Geändert in:**
- ✅ Monat indirekte Kosten (Zeile 597)
- ✅ YTD indirekte Kosten (Zeile 1150)
- ✅ v2 API indirekte Kosten (alle Varianten)
- ✅ Drill-Down indirekte Kosten

**SQL-Filter:**
```sql
OR (nominal_account_number BETWEEN 498000 AND 499999
    AND NOT (nominal_account_number = 498001))
```

---

## 📊 ERWARTETE AUSWIRKUNG

### YTD bis Dezember 2025

**Vor Korrektur:**
- Indirekte Kosten YTD: 838.937,55 €
- Betriebsergebnis YTD: -405.863,59 €
- Differenz zu GlobalCube: -160.130,59 €

**Nach Korrektur (erwartet):**
- Indirekte Kosten YTD: 638.937,55 € (838.937,55 - 200.000)
- Betriebsergebnis YTD: -205.863,59 € (-405.863,59 + 200.000)
- Differenz zu GlobalCube: +39.869,41 € (besser, aber noch nicht perfekt)

**Laut TAG 188 sollte BE YTD -191.157,71 € sein:**
- Das bedeutet: Es gibt noch weitere Probleme (z.B. Umsatz-Differenz)

---

## 🔧 TECHNISCHE DETAILS

### Geänderte Stellen

1. **Monat indirekte Kosten** (`_berechne_bwa_werte`)
   - Zeile 597: `OR nominal_account_number BETWEEN 498000 AND 499999`
   - → `OR (nominal_account_number BETWEEN 498000 AND 499999 AND NOT (nominal_account_number = 498001))`

2. **YTD indirekte Kosten** (`_berechne_bwa_ytd`)
   - Zeile 1150: `OR nominal_account_number BETWEEN 498000 AND 499999`
   - → `OR (nominal_account_number BETWEEN 498000 AND 499999 AND NOT (nominal_account_number = 498001))`

3. **v2 API indirekte Kosten** (`get_bwa_v2`)
   - Alle Varianten korrigiert

4. **Drill-Down indirekte Kosten** (`get_bwa_v2_drilldown`)
   - Korrigiert

---

## 📋 NÄCHSTE SCHRITTE

1. ✅ **Service neu starten** - Erledigt
2. ⏳ **YTD-Werte erneut prüfen**
3. ⏳ **Prüfen ob BE YTD jetzt -205.863,59 € ist**
4. ⏳ **Weitere Probleme identifizieren** (Umsatz-Differenz, etc.)

---

*Erstellt: TAG 196 | Autor: Claude AI*
