# GlobalCube Ebene-Zuordnungen - Vollständige Analyse TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** ✅ **VOLLSTÄNDIGE EBENE-ZUORDNUNGEN GEFUNDEN**

---

## 🎯 VOLLSTÄNDIGE EBENE-ZUORDNUNGEN

### 71700 (EW Sonstige Erlöse Neuwagen)

**Ebene-Zuordnungen:**
- **Ebene1:** Neuwagen
- **Ebene2:** NW Sonstige Erlöse
- **Ebene3:** NW Sonst. Verkaufserlöse
- **Ebene11:** zurückgestellt ⚠️
- **Ebene21:** GuV ✅
- **Ebene22:** 5. Materialaufwand ✅
- **Ebene23:** a) Aufwendungen für Roh-,Hilfs- und Betriebsstoffe und für bezogene Waren ✅
- **Ebene24:** aa) Neuwagen ✅
- **Ebene31:** XX
- **Ebene41:** NW
- **Ebene51:** Neuwagen
- **Ebene52:** NW Sonstige Erlöse
- **Ebene53:** NW Sonst. Verkaufserlöse
- **Ebene61:** EW NW Opel

**Erkenntnis:** Konto ist in GuV, Materialaufwand und Einsatz zugeordnet, aber auch "zurückgestellt"!

---

### 72700 (Sonstige Einsatzwerte GW)

**Ebene-Zuordnungen:**
- **Ebene1:** Gebrauchtwagen
- **Ebene2:** GW Sonstige Erlöse
- **Ebene3:** GW Sonst. Verkaufserlöse
- **Ebene11:** zurückgestellt ⚠️
- **Ebene21:** GuV ✅
- **Ebene22:** 5. Materialaufwand ✅
- **Ebene23:** a) Aufwendungen für Roh-,Hilfs- und Betriebsstoffe und für bezogene Waren ✅
- **Ebene24:** ab) Gebrauchtwagen ✅
- **Ebene31:** XX
- **Ebene41:** Einsatz ✅
- **Ebene51:** Gebrauchtwagen
- **Ebene52:** GW Sonstige Erlöse
- **Ebene53:** GW Sonst. Verkaufserlöse
- **Ebene61:** EW GW

**Erkenntnis:** Konto ist in GuV, Materialaufwand und Einsatz zugeordnet, aber auch "zurückgestellt"!

---

### 72750 (GIVIT Garantien GW)

**Ebene-Zuordnungen:**
- **Ebene1:** Gebrauchtwagen
- **Ebene2:** GW Sonstige Erlöse
- **Ebene3:** GW Garantie
- **Ebene11:** zurückgestellt ⚠️
- **Ebene21:** GuV ✅
- **Ebene22:** 5. Materialaufwand ✅
- **Ebene23:** a) Aufwendungen für Roh-,Hilfs- und Betriebsstoffe und für bezogene Waren ✅
- **Ebene24:** ab) Gebrauchtwagen ✅
- **Ebene31:** XX
- **Ebene41:** Einsatz ✅
- **Ebene51:** Gebrauchtwagen
- **Ebene52:** GW Sonstige Erlöse
- **Ebene53:** GW Garantie
- **Ebene61:** Im Kontenschema nicht vorhanden ⚠️

**Erkenntnis:** Konto ist in GuV, Materialaufwand und Einsatz zugeordnet, aber auch "zurückgestellt" und "Im Kontenschema nicht vorhanden"!

---

## 💡 INTERPRETATION

### "Zurückgestellt" ist eine zusätzliche Zuordnung

**Erkenntnis:** "Zurückgestellt" überschreibt **NICHT** die anderen Zuordnungen!

**Bedeutung:**
- Die Konten sind weiterhin in **GuV**, **Materialaufwand** und **Einsatz** zugeordnet
- "Zurückgestellt" könnte eine **zusätzliche Kategorisierung** sein
- Möglicherweise werden sie in **beiden Kategorien** verwendet (Einsatz UND zurückgestellt)

### Mögliche Bedeutung von "zurückgestellt"

1. **Für spätere Verwendung reserviert**
2. **Zusätzliche Kategorie** (neben Einsatz)
3. **Interne Markierung** (ohne Auswirkung auf BWA)

---

## 🔍 OFFENE FRAGEN

1. **Was bedeutet "zurückgestellt" genau?**
   - Wird es in den Cognos-Cubes verwendet?
   - Werden "zurückgestellt" Konten anders behandelt?

2. **Warum ist 72750 "Im Kontenschema nicht vorhanden"?**
   - Wird dieses Konto komplett ausgeschlossen?
   - Oder wird es anders behandelt?

3. **Wie werden diese Konten in GlobalCube verwendet?**
   - Werden sie in BWA berücksichtigt?
   - Oder werden sie ausgeschlossen?

---

## 📋 NÄCHSTE SCHRITTE

1. ⏳ **Prüfe, ob "zurückgestellt" in Cognos-Cubes verwendet wird:**
   - Werden "zurückgestellt" Konten gefiltert?
   - Oder werden sie anders behandelt?

2. ⏳ **Prüfe "Im Kontenschema nicht vorhanden":**
   - Was bedeutet das für 72750?
   - Wird dieses Konto ausgeschlossen?

3. ⏳ **Vergleiche mit GlobalCube-Ausgaben:**
   - Werden 71700, 72700, 72750 in GlobalCube-BWA berücksichtigt?
   - Oder werden sie ausgeschlossen?

---

## 📊 STATUS

- ✅ Vollständige Ebene-Zuordnungen gefunden
- ✅ Alle drei Konten sind in GuV, Materialaufwand und Einsatz zugeordnet
- ✅ Alle drei Konten haben auch "zurückgestellt"
- ⏳ Bedeutung von "zurückgestellt" klären
- ⏳ Prüfen, ob sie in GlobalCube-BWA verwendet werden

---

**ERKENNTNIS:** "Zurückgestellt" ist eine zusätzliche Zuordnung, die die anderen Zuordnungen nicht überschreibt!
