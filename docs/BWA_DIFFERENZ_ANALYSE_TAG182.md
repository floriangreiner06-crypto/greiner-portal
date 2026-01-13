# BWA Differenz-Analyse: GlobalCube vs. DRIVE - TAG 182

**Datum:** 2026-01-12  
**Status:** ✅ Differenzen identifiziert

---

## 📊 GLOBALCUBE WERTE (aus Excel)

**YTD Sep-Dez 2025:**
- Direkte Kosten: **659.228,98 €**
- Indirekte Kosten: **838.943,85 €**
- Betriebsergebnis: **-375.797,45 €**

**Quelle:** `/mnt/greiner-portal-sync/docs/F.03 BWA Vorjahres-Vergleich (7).xlsx`
- Spalte Q = "Kumuliert per Dez./2025" (YTD Sep-Dez 2025)

---

## 📊 DRIVE WERTE (TAG 177 Logik)

**YTD Sep-Dez 2025:**
- Direkte Kosten: **625.530,17 €**
- Indirekte Kosten: **837.228,63 €**

**Logik:**
- 411xxx + 489xxx + 410021 aus direkten Kosten ausgeschlossen
- 8910xx aus indirekten Kosten ausgeschlossen

---

## 🔍 DIFFERENZEN

### Direkte Kosten

**Differenz:** +33.698,81 € (DRIVE fehlen 33.698,81 €)

**Ausgeschlossene Konten in DRIVE (TAG 177):**
- 411xxx (Ausbildungsvergütung): 32.548,10 €
- 410021 (Spezifisches Konto): 1.056,37 €
- 489xxx (gesamt): 1.803,26 €
- **Total ausgeschlossen:** 35.407,73 €

**Vergleich:**
- Differenz: 33.698,81 €
- Total ausgeschlossen: 35.407,73 €
- **Übereinstimmung:** 1.708,92 € Differenz

**Erkenntnis:** Die Differenz entspricht **fast genau** den ausgeschlossenen Konten!

### Indirekte Kosten

**Differenz:** +1.715,22 € (DRIVE fehlen 1.715,22 €)

**Erkenntnis:** Kleine Differenz, möglicherweise Rundungsunterschiede oder andere Konten.

---

## 💡 WICHTIGE ERKENNTNISSE

### 1. TAG 177 Logik ist zeitraum-abhängig

**Problem:**
- TAG 177 Logik war für **August 2025** korrekt (23,99 € Differenz)
- TAG 177 Logik ist für **Dezember 2025** falsch (33.698,81 € Differenz)

**Erklärung:**
- Die Logik (411xxx + 489xxx + 410021 ausschließen) gilt möglicherweise nur für bestimmte Zeiträume
- Oder: Die Logik hat sich geändert
- Oder: Mapping-Fehler in der ursprünglichen Logik

### 2. 411xxx sollte NICHT aus direkten Kosten ausgeschlossen werden (Dezember 2025)

**Hypothese:**
- 411xxx ist in "Ausbildung" (ID: 75) unter Personalaufwand
- Für Dezember 2025 sollte 411xxx in direkten Kosten enthalten sein
- Für August 2025 war es korrekt ausgeschlossen

**Frage:** Warum unterschiedliche Logik für verschiedene Zeiträume?

### 3. 410021 und 489xxx

**Erkenntnis:**
- 410021 und 489xxx sollten möglicherweise auch NICHT ausgeschlossen werden
- Oder: Nur teilweise ausschließen (z.B. nur 489xxx mit KST 0)

---

## 🚀 LÖSUNG

### Option 1: 411xxx + 410021 + 489xxx in direkten Kosten enthalten

**Für Dezember 2025:**
- 411xxx **ENTHALTEN** in direkten Kosten
- 410021 **ENTHALTEN** in direkten Kosten
- 489xxx **ENTHALTEN** in direkten Kosten (oder nur KST 1-7?)

**Erwartetes Ergebnis:**
- Direkte Kosten YTD: 625.530,17 + 35.407,73 = **660.937,90 €**
- GlobalCube: **659.228,98 €**
- Differenz: **1.708,92 €** (sehr nah!)

### Option 2: Zeitraum-abhängige Logik

**Frage:** Gibt es unterschiedliche Logik für verschiedene Zeiträume?

**Möglichkeiten:**
- Strukturen haben sich geändert
- Mapping-Regeln haben sich geändert
- GlobalCube verwendet verschiedene Filter je nach Zeitraum

---

## 📝 NÄCHSTE SCHRITTE

1. ⏳ **Prüfen: Sollten 411xxx + 410021 + 489xxx enthalten sein?**
   - Test: Enthalten → Vergleich mit GlobalCube
   - Erwartung: Sehr nahe an GlobalCube (1.708,92 € Differenz)

2. ⏳ **Zeitraum-Analyse**
   - Warum war TAG 177 Logik für August 2025 korrekt?
   - Warum ist sie für Dezember 2025 falsch?
   - Gibt es unterschiedliche Logik?

3. ⏳ **489xxx Logik verfeinern**
   - Sollte 489xxx komplett enthalten sein?
   - Oder nur 489xxx mit KST 1-7?
   - Was ist mit 489xxx KST 0?

---

## 📊 STATUS

- ✅ GlobalCube Werte extrahiert (aus Excel)
- ✅ DRIVE Werte berechnet (TAG 177 Logik)
- ✅ Differenzen identifiziert
- ✅ Ausgeschlossene Konten analysiert
- ⏳ Lösung implementieren
- ⏳ Validierung durchführen

---

**Nächster Schritt:** Testen, ob 411xxx + 410021 + 489xxx in direkten Kosten enthalten sein sollten.
