# "Zurückgestellt" Analyse - Vollständige Erkenntnisse TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** 🎯 **KRITISCHE ERKENNTNIS!**

---

## 🎯 KRITISCHE ERKENNTNISSE

### 1. Konten mit "zurückgestellt"

**Gefundene Konten:**
- **71700** (EW Sonstige Erlöse Neuwagen) → "zurückgestellt"
- **72700** (Sonstige Einsatzwerte GW) → "zurückgestellt"
- **72750** (GIVIT Garantien GW) → "zurückgestellt"

**Gesamt:** 554 Konten mit "zurückgestellt" (7xxx-Bereich)

### 2. Struktur_GuV.csv

**Ergebnis:**
- ❌ 71700, 72700, 72750 sind **NICHT** in Struktur_GuV.csv enthalten!
- ❌ "Zurückgestellt" kommt **NICHT** in Struktur_GuV.csv vor!

**Erkenntnis:** Konten mit "zurückgestellt" werden möglicherweise **nicht in der G&V-Struktur** verwendet!

### 3. Bedeutung von "zurückgestellt"

**Mögliche Interpretationen:**
1. **Ausgeschlossen:** Konten werden komplett aus der BWA ausgeschlossen
2. **Verschoben:** Konten werden in eine andere Kategorie verschoben (z.B. "Neutrales Ergebnis")
3. **Reserviert:** Konten sind für spätere Verwendung "zurückgestellt"

---

## 💡 HYPOTHESEN

### Hypothese 1: "Zurückgestellt" = Ausgeschlossen aus BWA

**Möglichkeit:** Konten mit "zurückgestellt" werden von GlobalCube **nicht in der BWA** berücksichtigt.

**Test:**
- Prüfe, ob 71700, 72700, 72750 in anderen Strukturen enthalten sind
- Prüfe, ob sie in "Neutrales Ergebnis" verschoben werden

### Hypothese 2: "Zurückgestellt" = Verschoben zu "Neutrales Ergebnis"

**Möglichkeit:** Konten mit "zurückgestellt" werden in "Neutrales Ergebnis" verschoben, nicht in "Einsatz".

**Test:**
- Prüfe Struktur_Controlling.csv
- Prüfe, ob "zurückgestellt" Konten in "Neutrales Ergebnis" kategorisiert sind

### Hypothese 3: "Zurückgestellt" = Nur bestimmte Buchungen ausgeschlossen

**Möglichkeit:** Nicht alle Buchungen werden ausgeschlossen, sondern nur bestimmte (z.B. HABEN-Buchungen).

**Test:**
- Prüfe, ob nur HABEN-Buchungen von 71700, 72700, 72750 ausgeschlossen werden
- Prüfe, ob SOLL-Buchungen weiterhin berücksichtigt werden

---

## 📊 AUSWIRKUNG

### Wenn 71700, 72700, 72750 ausgeschlossen werden:

**HABEN-Buchungen (einsatzmindernd):**
- 71700: 906.983,78 €
- 72700: 87.018,58 €
- 72750: 13.917,40 €
- **Summe:** 1.007.919,76 €

**Aber:** Die Differenz ist nur 31.905,97 €!

**Erkenntnis:** Wenn alle "zurückgestellt" Konten ausgeschlossen würden, wäre die Differenz viel größer!

**Alternative:** Vielleicht werden nur bestimmte Buchungen ausgeschlossen, oder "zurückgestellt" bedeutet etwas anderes.

---

## 📋 NÄCHSTE SCHRITTE

1. ⏳ **Vollständige Ebene-Zuordnungen prüfen:**
   - Welche anderen Ebene-Zuordnungen haben 71700, 72700, 72750?
   - Wohin werden sie verschoben?

2. ⏳ **Struktur_Controlling.csv prüfen:**
   - Sind 71700, 72700, 72750 in Struktur_Controlling.csv enthalten?
   - Werden sie in "Neutrales Ergebnis" verschoben?

3. ⏳ **Bedeutung von "zurückgestellt" klären:**
   - Gibt es Dokumentation?
   - Was bedeutet es in der Praxis?

---

## 📊 STATUS

- ✅ 71700, 72700, 72750 gefunden
- ✅ Alle haben "zurückgestellt" als Ebene-Zuordnung
- ✅ Nicht in Struktur_GuV.csv enthalten
- ⏳ Vollständige Ebene-Zuordnungen prüfen
- ⏳ Struktur_Controlling.csv prüfen
- ⏳ Bedeutung von "zurückgestellt" klären

---

**KRITISCHE FRAGE:** Was bedeutet "zurückgestellt" genau? Werden diese Konten ausgeschlossen oder verschoben?
