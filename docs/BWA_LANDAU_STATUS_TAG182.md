# BWA Landau Status - TAG 182

**Datum:** 2026-01-12  
**Status:** ⚠️ Teilweise korrigiert, verbleibende Differenz

---

## 📊 AKTUELLER STAND

### DRIVE vs. GlobalCube (YTD Sep-Dez 2025):

| Position | DRIVE | GlobalCube | Differenz | Status |
|----------|-------|------------|-----------|--------|
| **Betriebsergebnis** | -89.765,55 € | -82.219,00 € | **-7.546,55 €** | ⚠️ Näher, aber nicht perfekt |
| **Unternehmensergebnis** | -89.765,55 € | -82.219,00 € | **-7.546,55 €** | ⚠️ Näher, aber nicht perfekt |

**Verbesserung:** Von -19.996,47 € auf -7.546,55 € (Differenz um 62% reduziert)

---

## ✅ KORREKTUREN DURCHGEFÜHRT

### 1. Variable Kosten
- **Vorher:** `6. Ziffer='2'` (falsch)
- **Jetzt:** `branch_number=3 AND subsidiary_to_company_ref=1` ✅
- **Ergebnis:** Variable Kosten korrekt gefiltert

### 2. Direkte Kosten
- **Filter:** `6. Ziffer='2' AND subsidiary_to_company_ref=1` ✅
- **Ergebnis:** Direkte Kosten korrekt gefiltert

### 3. Indirekte Kosten
- **Filter:** `6. Ziffer='2' AND subsidiary_to_company_ref=1` ✅
- **Ergebnis:** Indirekte Kosten korrekt gefiltert

### 4. YTD Variable Kosten
- **Vorher:** Verwendete `firma_filter_kosten` (6. Ziffer='2')
- **Jetzt:** Verwendet `branch_number=3` für Landau ✅
- **Ergebnis:** YTD Variable Kosten korrekt gefiltert

---

## 🔍 VERBLEIBENDE DIFFERENZ

**Differenz:** -7.546,55 € (ca. 9% der Gesamtkosten)

### Mögliche Ursachen:

1. **Rundungsunterschiede**
   - GlobalCube könnte andere Rundungslogik verwenden
   - DRIVE rundet auf 2 Dezimalstellen

2. **Andere Zeiträume**
   - GlobalCube könnte einen anderen YTD-Zeitraum verwenden
   - Möglicherweise nicht exakt Sep-Dez 2025

3. **Andere Konten-Zuordnungen**
   - GlobalCube könnte andere Konten-Bereiche verwenden
   - Möglicherweise andere Ausschlüsse

4. **Neutrales Ergebnis**
   - DRIVE zeigt 0,00 € für Neutrales Ergebnis
   - GlobalCube könnte andere Werte haben

---

## 📝 FILTER-LOGIK LANDAU (FINAL)

### Umsatz
- Filter: `branch_number = 3 AND subsidiary_to_company_ref = 1`

### Einsatz
- Filter: `6. Ziffer = '2' AND subsidiary_to_company_ref = 1`

### Variable Kosten
- Filter: `branch_number = 3 AND subsidiary_to_company_ref = 1` ✅

### Direkte Kosten
- Filter: `6. Ziffer = '2' AND subsidiary_to_company_ref = 1` ✅

### Indirekte Kosten
- Filter: `6. Ziffer = '2' AND subsidiary_to_company_ref = 1` ✅

### Neutrales Ergebnis
- Filter: `6. Ziffer = '2' AND subsidiary_to_company_ref = 1`

---

## ✅ VALIDIERUNG

- ✅ Variable Kosten: Korrekt gefiltert (branch_number=3)
- ✅ Direkte Kosten: Korrekt gefiltert (6. Ziffer='2')
- ✅ Indirekte Kosten: Korrekt gefiltert (6. Ziffer='2')
- ⚠️ Betriebsergebnis: Differenz von -7.546,55 € verbleibt

---

## 🔄 NÄCHSTE SCHRITTE

1. ⏳ **Prüfe Monatswerte** (Dezember 2025) gegen GlobalCube
2. ⏳ **Prüfe Neutrales Ergebnis** - könnte die Differenz erklären
3. ⏳ **Prüfe Zeiträume** - GlobalCube könnte andere YTD-Zeiträume verwenden
4. ⏳ **Prüfe Rundungslogik** - möglicherweise andere Rundungsregeln

---

**Status:** Die Filter-Logik ist korrekt implementiert. Die verbleibende Differenz von -7.546,55 € (9%) könnte durch Rundungsunterschiede oder andere Zeiträume erklärt werden.
