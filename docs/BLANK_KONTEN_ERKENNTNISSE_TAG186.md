# "Blank" Konten Erkenntnisse TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** 🎯 **KRITISCHE ERKENNTNISSE**

---

## 🎯 ERKENNTNISSE

### 1. "Blank" Konten im Cube

**5-stellige Konten (71700, 72700, 72750):**
- ❌ Keine Buchungen (0 €)
- ❌ Nicht im Cube verwendet

**6-stellige Konten (717001, 727001, 727501):**
- ✅ Haben Buchungen!
- ✅ Im Cube vorhanden
- ✅ Haben "blank" Zuordnung im Cube

### 2. Werte der "blank" Konten (YTD Jan-Dez 2025)

- **717001:** 16.390,27 €
- **727001:** 71.729,12 €
- **727501:** -12.608,04 €
- **Summe:** 75.511,35 €

### 3. Vergleich mit bekannter Differenz

**Bekannte Differenz (GlobalCube vs DRIVE):**
- +31.905,97 € (DRIVE höher als GlobalCube)

**Summe "blank" Konten:**
- 75.511,35 €

**Ergebnis:**
- ❌ Summe ist **zu hoch** (43.605,38 € Abweichung)
- ❌ Passt **nicht** zur bekannten Differenz

---

## 💡 HYPOTHESEN

### Hypothese 1: Nur bestimmte Konten werden ausgeschlossen

**Möglichkeit:** Vielleicht werden nur **727001** oder eine Kombination ausgeschlossen, nicht alle drei.

**Test:** Prüfe verschiedene Kombinationen

### Hypothese 2: Nur HABEN-Buchungen werden ausgeschlossen

**Möglichkeit:** Vielleicht werden nur **HABEN-Buchungen** (einsatzmindernd) ausgeschlossen, nicht SOLL-Buchungen.

**Test:** Prüfe HABEN vs. SOLL für "blank" Konten

### Hypothese 3: Andere Filter

**Möglichkeit:** Es gibt **andere Filter** (z.B. nach Standort, Firma, oder anderen Kriterien), die die Differenz erklären.

**Test:** Prüfe Filter-Logik genauer

---

## 📊 NÄCHSTE SCHRITTE

1. ⏳ **HABEN vs. SOLL Buchungen analysieren**
2. ⏳ **Verschiedene Kombinationen prüfen**
3. ⏳ **Andere Filter-Logik prüfen**

---

## 📊 STATUS

- ✅ "Blank" Konten im Cube gefunden
- ✅ Werte der "blank" Konten berechnet
- ⏳ Vergleich mit bekannter Differenz läuft
- ⏳ HABEN vs. SOLL Analyse läuft

---

**KRITISCHE ERKENNTNIS:** "Blank" Konten haben Werte, aber die Summe passt nicht zur bekannten Differenz!
