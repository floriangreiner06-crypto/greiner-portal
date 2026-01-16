# BWA Mechanik+Karo - Fehlende 10.814,14 € Analyse

**Datum:** 2026-01-16  
**TAG:** 196  
**Status:** ⏳ **IN ANALYSE**

---

## 🎯 PROBLEM

**GlobalCube zeigt:** "Mechanik+Karo" = 86.419,00 €  
**DRIVE zeigt:** Mechanik + Clean Park = 75.604,86 €  
**Fehlende Differenz:** -10.814,14 €

---

## ✅ IMPLEMENTIERT

### Clean Park als separate Rubrik:

- **Clean Park wird separat angezeigt** (wie gewünscht)
- **Mechanik enthält Clean Park NICHT mehr** (separate Berechnung)
- **Summe für Vergleich:** Mechanik + Clean Park = 75.604,86 €

### Aktuelle Werte (Dezember 2025):

- **Mechanik (ohne CP):** 58.096,43 €
- **Clean Park (separat):** 17.508,43 €
- **Summe:** 75.604,86 €
- **GlobalCube:** 86.419,00 €
- **Differenz:** -10.814,14 €

---

## 📊 ANALYSE

### Ausgeschlossene Bereiche:

1. **8405xx (Karosserie):** 0,00 € (keine Buchungen)
2. **8406xx (Lackierung):** 18.257,94 € (187 Buchungen) - **extern vergeben**
3. **847xxx (Clean Park):** 23.197,92 € (38 Buchungen) - **separat angezeigt**

### Clean Park Berechnung:

- **Erlös (847xxx):** 23.197,92 €
- **Einsatz (747xxx):** 5.689,49 €
- **Bruttoertrag:** 17.508,43 € ✅ **KORREKT**

### Standort-Verteilung (Mechanik ohne CP):

- **Branch 1, Subsidiary 1:** 71.336,59 €
- **Branch 2, Subsidiary 2:** 59.944,12 €
- **Branch 3, Subsidiary 1:** 21.059,00 €

---

## ⚠️ MÖGLICHE URSACHEN

1. **Andere Konten fehlen:**
   - Gibt es andere 84xxxx Konten, die zu Mechanik gehören sollten?
   - Gibt es andere 74xxxx Konten, die zu Mechanik gehören sollten?

2. **Filter-Unterschiede:**
   - Verwendet GlobalCube andere Filter-Logik?
   - Gibt es Standort-spezifische Unterschiede?

3. **Kostenstellen-Unterschiede:**
   - Verwendet GlobalCube andere Kostenstellen-Zuordnung?

4. **Zeitraum-Unterschiede:**
   - Gibt es Buchungsdatum-Unterschiede?

---

## 📝 NÄCHSTE SCHRITTE

1. ⏳ **Prüfe GlobalCube-Schema:** Welche Konten gehören zu "Mechanik+Karo"?
2. ⏳ **Prüfe Filter-Logik:** Gibt es Unterschiede in der Filter-Logik?
3. ⏳ **Prüfe Standort-Filter:** Gibt es Standort-spezifische Unterschiede?
4. ⏳ **Prüfe Kostenstellen:** Verwendet GlobalCube andere Kostenstellen-Zuordnung?

---

## ✅ STATUS

- ✅ Clean Park wird separat angezeigt
- ✅ Mechanik enthält Clean Park nicht mehr
- ⚠️ Fehlende Differenz: -10.814,14 €
- ⏳ Weitere Analyse erforderlich
