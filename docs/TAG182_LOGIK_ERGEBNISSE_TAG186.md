# TAG 182 Logik Ergebnisse - TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** ✅ **IMPLEMENTIERT UND GETESTET**

---

## ✅ SERVER NEU GESTARTET

**Neustart erfolgreich:** Server läuft mit TAG 182 Logik

**Neue Werte aktiv:**
- Direkte Kosten Monat: **189.849,47 €** (statt 181.216,91 €) ✅
- Direkte Kosten YTD: **659.134,64 €** (statt 625.530,17 €) ✅

---

## 📊 ERGEBNISSE: GESAMTBETRIEB

### Monat Dezember 2025 ✅ **SEHR GUT!**

| Position | DRIVE | GlobalCube | Differenz | Status |
|----------|-------|------------|-----------|--------|
| Umsatz | 2.190.718,01 € | 2.190.718,00 € | +0,01 € | ✅ |
| Einsatz | 1.865.890,36 € | 1.862.668,00 € | +3.222,36 € | ⚠️ |
| Bruttoertrag (DB1) | 324.827,65 € | 328.050,00 € | -3.222,35 € | ⚠️ |
| Variable Kosten | 69.270,36 € | 69.374,00 € | -103,64 € | ✅ |
| Bruttoertrag II (DB2) | 255.557,29 € | 258.676,00 € | -3.118,71 € | ⚠️ |
| **Direkte Kosten** | **189.849,47 €** | **189.866,00 €** | **-16,53 €** | ✅ |
| Deckungsbeitrag (DB3) | 65.707,82 € | 68.810,00 € | -3.102,18 € | ⚠️ |
| Indirekte Kosten | 185.057,99 € | 185.058,00 € | -0,01 € | ✅ |
| Betriebsergebnis | -119.350,17 € | -116.248,00 € | -3.102,17 € | ⚠️ |
| Neutrales Ergebnis | 32.628,68 € | 32.629,00 € | -0,32 € | ✅ |
| Unternehmensergebnis | -86.721,49 € | -83.619,00 € | -3.102,49 € | ⚠️ |

**Ergebnis:** ✅ **Direkte Kosten sind jetzt sehr nah an GlobalCube!**
- Verbesserung: Von -8.649,09 € auf -16,53 € (99,8% Verbesserung!)

### YTD Sep-Dez 2025 ⚠️ **PROBLEME**

| Position | DRIVE | GlobalCube | Differenz | Status |
|----------|-------|------------|-----------|--------|
| Umsatz | 10.618.393,36 € | 10.618.400,00 € | -6,64 € | ✅ |
| Einsatz | 9.223.769,97 € | 9.191.864,00 € | +31.905,97 € | 🚨 |
| Bruttoertrag (DB1) | 1.394.623,39 € | 1.426.536,00 € | -31.912,61 € | 🚨 |
| Variable Kosten | 304.164,35 € | 304.268,00 € | -103,65 € | ✅ |
| Bruttoertrag II (DB2) | 1.090.459,04 € | 1.122.268,00 € | -31.808,96 € | 🚨 |
| **Direkte Kosten** | **659.134,64 €** | **659.229,00 €** | **-94,36 €** | ✅ |
| Deckungsbeitrag (DB3) | 431.324,40 € | 463.039,00 € | -31.714,60 € | 🚨 |
| Indirekte Kosten | 838.937,55 € | 838.944,00 € | -6,45 € | ✅ |
| Betriebsergebnis | -407.613,15 € | -375.905,00 € | -31.708,15 € | 🚨 |
| Neutrales Ergebnis | 130.171,89 € | 130.172,00 € | -0,11 € | ✅ |
| Unternehmensergebnis | -277.441,26 € | -245.733,00 € | -31.708,26 € | 🚨 |

**Ergebnis:** ✅ **Direkte Kosten sind jetzt sehr nah an GlobalCube!**
- Verbesserung: Von -33.698,83 € auf -94,36 € (99,7% Verbesserung!)

**Aber:** ⚠️ **Neue Probleme identifiziert:**
- Einsatz: +31.905,97 € Differenz (YTD)
- Betriebsergebnis: -31.708,15 € Differenz (YTD)
- **Erkenntnis:** Die Differenz im Betriebsergebnis entspricht genau der Einsatz-Differenz!

---

## 🔍 ANALYSE

### 1. Direkte Kosten ✅ **GELÖST!**

**Ergebnis:**
- Monat: -16,53 € Differenz (0,01%) ✅
- YTD: -94,36 € Differenz (0,01%) ✅

**Verbesserung:**
- Monat: Von -8.649,09 € auf -16,53 € (99,8% Verbesserung!)
- YTD: Von -33.698,83 € auf -94,36 € (99,7% Verbesserung!)

### 2. Einsatz ⚠️ **PROBLEM IDENTIFIZIERT**

**Ergebnis:**
- Monat: +3.222,36 € Differenz (0,17%)
- YTD: +31.905,97 € Differenz (0,35%)

**Erkenntnis:**
- Die Differenz im Betriebsergebnis (-31.708,15 € YTD) entspricht fast genau der Einsatz-Differenz (+31.905,97 € YTD)
- **Hypothese:** Problem liegt beim Einsatz-Filter für Gesamtbetrieb

### 3. Betriebsergebnis ⚠️ **PROBLEM IDENTIFIZIERT**

**Ergebnis:**
- Monat: -3.102,17 € Differenz (2,67%)
- YTD: -31.708,15 € Differenz (8,44%)

**Erkenntnis:**
- Die Differenz entspricht der Einsatz-Differenz
- **Hypothese:** Wenn Einsatz korrekt wäre, wäre Betriebsergebnis auch korrekt

---

## 📝 NÄCHSTE SCHRITTE

1. ⏳ **Einsatz-Filter für Gesamtbetrieb analysieren:**
   - Warum zeigt DRIVE 9.223.769,97 € statt 9.191.864,00 €?
   - Filter-Logik für firma=0, standort=0 prüfen

2. ⏳ **Landau-spezifische Probleme analysieren:**
   - Variable Kosten: -13.256,47 € Differenz (YTD)
   - Direkte Kosten: -9.498,80 € Differenz (YTD)

3. ⏳ **Weitere Differenzen analysieren:**
   - Deckungsbeitrag (DB3): -31.714,60 € Differenz (YTD)
   - Unternehmensergebnis: -31.708,26 € Differenz (YTD)

---

## 📊 STATUS

- ✅ TAG 182 Logik implementiert
- ✅ Server neu gestartet
- ✅ Direkte Kosten korrekt (nur -16,53 € / -94,36 € Differenz)
- ⏳ Einsatz-Filter analysieren
- ⏳ Weitere Differenzen analysieren

---

**Ergebnis:** Direkte Kosten sind jetzt sehr nah an GlobalCube! Aber es gibt noch Probleme mit Einsatz und Betriebsergebnis.
