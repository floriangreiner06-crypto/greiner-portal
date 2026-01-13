# Landau BWA Problem - TAG 182

**Datum:** 2026-01-12  
**Status:** ⚠️ Noch Differenz vorhanden

---

## 🎯 PROBLEM

Landau BWA zeigt noch eine Differenz von **19.152,43 €** im Betriebsergebnis YTD.

**DRIVE:**
- BE YTD: -63.160,91 €
- UE YTD: -63.160,91 €

**GlobalCube:**
- BE YTD: -82.219,00 €
- UE YTD: -82.219,00 €

---

## ✅ KORREKTUREN DURCHGEFÜHRT

### 1. Kosten-Filter korrigiert

**Problem:** Für Landau wurden Variable Kosten mit `branch_number=3` gefiltert, aber Direkte und Indirekte Kosten mit `6. Ziffer='2'`.

**Lösung:** ALLE Kosten (Variable, Direkte, Indirekte) für Landau verwenden jetzt `6. Ziffer='2'`.

**Ergebnis:**
- Variable Kosten: 26.008,95 € (vorher: 13.455,61 €)
- Direkte Kosten: 140.761,54 € (vorher: 2.334,13 €)
- Indirekte Kosten: 148.628,95 € (vorher: 3.585,45 €)

---

## ⚠️ VERBLEIBENDE DIFFERENZ

**BE-Differenz:** 19.152,43 €

**Mögliche Ursachen:**
1. Neutrale Ergebnis: DRIVE zeigt 0,00 €, GlobalCube zeigt -127,00 €
   - Aber das erklärt nur 127 €, nicht 19.152 €
2. Fehlende Kosten: Analyse zeigt nur 94,34 € fehlende Kosten
3. Umsatz/Einsatz: Könnte falsch gefiltert sein
4. Andere Faktoren: Könnte an G&V-Filter oder anderen Exclusions liegen

---

## 📊 AKTUELLE WERTE

**Umsatz YTD:** 1.385.353,71 € (branch_number=3)  
**Einsatz YTD:** 1.133.115,18 € (branch_number=3)  
**DB1 YTD:** 252.238,53 €

**Variable Kosten:** 26.008,95 € (6. Ziffer='2')  
**Direkte Kosten:** 140.761,54 € (6. Ziffer='2')  
**Indirekte Kosten:** 148.628,95 € (6. Ziffer='2')  
**Summe Kosten:** 315.399,44 €

**DB2 YTD:** 226.229,58 €  
**DB3 YTD:** 85.562,38 €  
**BE YTD:** -63.160,91 €

**Neutrales Ergebnis:** 0,00 € (branch_number=3)  
**UE YTD:** -63.160,91 €

---

## 🔍 NÄCHSTE SCHRITTE

1. Prüfe ob Umsatz/Einsatz korrekt gefiltert sind
2. Prüfe ob Neutrale Ergebnis mit `6. Ziffer='2'` gefiltert werden muss
3. Prüfe ob G&V-Filter korrekt angewendet wird
4. Vergleiche mit HAR-Datei für Landau

---

## 📝 CODE-ÄNDERUNGEN

**Dateien:**
- `api/controlling_api.py`: Zeilen 462-503, 505-534, 536-568, 989-1030, 1032-1061, 1063-1095, 1917-1959, 1964-1996, 1997-2029, 2245-2287

**Änderungen:**
- Alle Kosten-Filter für Landau von `branch_number=3` zu `6. Ziffer='2'` geändert
- Kommentare aktualisiert: "Landau - ALLE Kosten mit 6. Ziffer='2' (nicht branch_number=3!)"
