# "Blank" Konten Zusammenfassung TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** 🎯 **KRITISCHE ERKENNTNISSE**

---

## 🎯 ERKENNTNISSE

### 1. "Blank" Konten im Cognos Cube

**Gefunden:**
- `QU;9;( blank )B$;14;( Leerstelle )A$;20;( Leerstelle )~71700`
- `QU;9;( blank )B$;14;( Leerstelle )A$;20;( Leerstelle )~72700`
- `QU;9;( blank )B$;14;( Leerstelle )A$;20;( Leerstelle )~72750`

**Erkenntnis:** Die 5-stelligen Konten (71700, 72700, 72750) haben "blank" Zuordnungen im Cube!

### 2. 6-stellige Varianten haben Werte

**5-stellige Konten:**
- ❌ Keine Buchungen (0 €)

**6-stellige Konten:**
- ✅ **717001:** 16.390,27 €
- ✅ **727001:** 71.729,12 €
- ✅ **727501:** -12.608,04 €
- ✅ **Summe:** 75.511,35 €

### 3. Differenz nach Standort/Firma

**Gesamtbetrieb:**
- Mit "blank": 25.866.837,48 €
- Ohne "blank": 25.791.326,13 €
- Differenz: 75.511,35 €

**Stellantis (alle Standorte):**
- Mit "blank": 16.908.301,97 €
- Ohne "blank": 16.886.217,35 €
- Differenz: 22.084,62 €

**Hyundai (alle Standorte):**
- Mit "blank": 8.958.535,51 €
- Ohne "blank": 8.905.108,78 €
- Differenz: 53.426,73 €

**Landau:**
- Mit "blank": 3.655.537,42 €
- Ohne "blank": 3.655.537,42 €
- Differenz: 0,00 € ⚠️

### 4. Bekannte Differenz

**Aus vorheriger Analyse:**
- DRIVE: 9.223.769,97 €
- GlobalCube: 9.191.864,00 €
- Differenz: +31.905,97 €

**Vermutung:** Diese Differenz gilt wahrscheinlich für **Stellantis (alle Standorte)**, nicht für Gesamtbetrieb!

---

## 💡 INTERPRETATION

### Hypothese 1: "Blank" Konten werden ausgeschlossen

**Möglichkeit:** GlobalCube schließt "blank" Konten (717001, 727001, 727501) aus.

**Test:**
- Stellantis ohne "blank": 16.886.217,35 €
- Bekannte DRIVE: 9.223.769,97 €
- ❌ Passt nicht (zu hoch)

### Hypothese 2: Nur bestimmte "blank" Konten werden ausgeschlossen

**Möglichkeit:** Vielleicht werden nur **727001** oder eine Kombination ausgeschlossen.

**Test:** Prüfe verschiedene Kombinationen

### Hypothese 3: Andere Filter

**Möglichkeit:** Es gibt **andere Filter** (z.B. nach Buchungstext, Buchungstyp, etc.), die die Differenz erklären.

**Test:** Prüfe Filter-Logik genauer

---

## 📊 NÄCHSTE SCHRITTE

1. ⏳ **Prüfe, ob bekannte Differenz für Stellantis gilt**
2. ⏳ **Vergleiche verschiedene Kombinationen von "blank" Konten**
3. ⏳ **Prüfe andere Filter-Logik**

---

## 📊 STATUS

- ✅ "Blank" Konten im Cube gefunden
- ✅ Werte der "blank" Konten berechnet
- ✅ Differenz nach Standort/Firma analysiert
- ⏳ Vergleich mit bekannter Differenz läuft

---

**KRITISCHE ERKENNTNIS:** "Blank" Konten haben Werte, aber die Summe passt nicht zur bekannten Differenz. Möglicherweise gibt es andere Filter oder die Differenz gilt für einen anderen Standort/Firma!
