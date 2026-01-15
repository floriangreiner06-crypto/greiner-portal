# "Zurückgestellt" Erkenntnis - Kritische Entdeckung TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** 🎯 **KRITISCHE ERKENNTNIS!**

---

## 🎯 KRITISCHE ERKENNTNIS

### Gefundene Konten in GCStruct/Kontenrahmen/Kontenrahmen.csv:

1. **71700** (EW Sonstige Erlöse Neuwagen)
   - **Ebene-Zuordnung:** "zurückgestellt" ⚠️

2. **72700** (Sonstige Einsatzwerte GW)
   - **Ebene-Zuordnung:** "zurückgestellt" ⚠️

3. **72750** (GIVIT Garantien GW)
   - **Ebene-Zuordnung:** "zurückgestellt" ⚠️

**Alle drei Konten haben die Ebene-Zuordnung "zurückgestellt"!**

---

## 💡 HYPOTHESE

### "Zurückgestellt" = Ausgeschlossen?

**Möglichkeit:** Konten mit der Ebene-Zuordnung "zurückgestellt" werden von GlobalCube **ausgeschlossen** oder in eine **andere Kategorie** verschoben.

**Bedeutung:**
- **71700** (EW Sonstige Erlöse Neuwagen) → 906.983,78 € HABEN
- **72700** (Sonstige Einsatzwerte GW) → 87.018,58 € HABEN
- **72750** (GIVIT Garantien GW) → 13.917,40 € HABEN

**Wenn diese Konten ausgeschlossen werden:**
- Einsatz würde um 906.983,78 + 87.018,58 + 13.917,40 = **1.007.919,76 €** sinken
- Das ist viel zu viel! (Differenz ist nur 31.905,97 €)

**Alternative:**
- Vielleicht werden nur bestimmte Buchungen ausgeschlossen?
- Oder: "Zurückgestellt" bedeutet etwas anderes?

---

## 🔍 NÄCHSTE SCHRITTE

1. ⏳ **Prüfe, was "zurückgestellt" bedeutet:**
   - Wie viele Konten haben "zurückgestellt"?
   - Welche anderen Ebene-Zuordnungen gibt es?
   - Gibt es Dokumentation zu "zurückgestellt"?

2. ⏳ **Prüfe Struktur_GuV.csv:**
   - Sind 71700, 72700, 72750 in Struktur_GuV.csv enthalten?
   - Oder werden sie ausgeschlossen?

3. ⏳ **Prüfe, ob "zurückgestellt" Konten in BWA verwendet werden:**
   - Werden sie in "Neutrales Ergebnis" verschoben?
   - Oder werden sie komplett ausgeschlossen?

---

## 📊 STATUS

- ✅ 71700, 72700, 72750 in GCStruct gefunden
- ✅ Alle haben "zurückgestellt" als Ebene-Zuordnung
- ⏳ Bedeutung von "zurückgestellt" klären
- ⏳ Prüfen, ob sie in BWA verwendet werden

---

**KRITISCHE FRAGE:** Was bedeutet "zurückgestellt" in GlobalCube? Werden diese Konten ausgeschlossen?
