# Fertigmachen Lösung - Variable Kosten Landau - TAG 184

**Datum:** 2026-01-13  
**Status:** ✅ Lösung gefunden!

---

## 🎯 PROBLEM

- **Excel "Fertigmachen" (Landau):** 7.043,73 €
- **DRIVE Variable Kosten (Landau):** 6.173,95 €
- **Differenz:** -869,78 € (-12,35%)

---

## ✅ LÖSUNG

**Excel "Fertigmachen" enthält:**
1. **DRIVE Variable Kosten (6. Ziffer='2'):** 4.218,38 €
2. **Plus bestimmte Konten mit 6. Ziffer='1':**
   - 494021: 2.458,40 €
   - 497061: 132,50 €
   - 497221: 239,61 €
   - **Summe:** 2.830,51 €

**Gesamt:** 4.218,38 € + 2.830,51 € = **7.048,89 €**

**Vergleich mit Excel:** 7.043,73 €  
**Differenz:** 5,16 € (0,07%) ✅ **PERFEKT!**

---

## 📊 KONTEN-AUFSCHLÜSSELUNG

### DRIVE Variable Kosten (6. Ziffer='2'):
- 492022: 1.472,31 €
- 492012: 1.157,90 €
- 494012: 755,00 €
- 494022: 755,00 €
- 491012: 150,00 €
- 497312: -71,83 €
- **Summe:** 4.218,38 €

### Excel zusätzliche Konten (6. Ziffer='1'):
- 494021: 2.458,40 €
- 497061: 132,50 €
- 497221: 239,61 €
- **Summe:** 2.830,51 €

---

## 💡 ERKENNTNIS

**Excel "Fertigmachen" Filter:**
- 491xx-497xx mit **6. Ziffer='2'** (wie DRIVE)
- **Plus** bestimmte Konten mit **6. Ziffer='1'**: 494021, 497061, 497221

**Warum diese 3 Konten?**
- Möglicherweise spezielle Konten-Typen
- Oder bestimmte Konten-Bereiche (494xx, 497xx)
- Oder GlobalCube Mapping-Logik

---

## 🔍 NÄCHSTE SCHRITTE

### Option 1: DRIVE Filter anpassen
**Frage:** Sollen wir DRIVE Variable Kosten Filter anpassen, um diese 3 Konten einzuschließen?

**Vorteile:**
- ✅ Perfekte Übereinstimmung mit Excel/GlobalCube
- ✅ Konsistente Werte

**Nachteile:**
- ⚠️ Müssen prüfen ob diese Konten auch in anderen Standorten enthalten sind
- ⚠️ Müssen prüfen ob diese Logik für alle Monate gilt

### Option 2: Weitere Analyse
**Frage:** Warum enthält Excel nur diese 3 Konten mit 6. Ziffer='1'?

**Mögliche Ursachen:**
- GlobalCube Mapping-Logik
- Konten-Typen oder Konten-Bereiche
- Spezielle Filter in GlobalCube

---

## 📋 EMPFEHLUNG

### Schritt 1: Prüfe andere Standorte
- Enthalten DEG und HYU auch diese 3 Konten in "Fertigmachen"?
- Oder ist das Landau-spezifisch?

### Schritt 2: Prüfe andere Monate
- Gilt diese Logik auch für andere Monate?
- Oder nur für Dezember 2025?

### Schritt 3: Entscheidung
- **Wenn konsistent:** DRIVE Filter anpassen
- **Wenn nicht konsistent:** Weitere Analyse nötig

---

## 📁 GENERIERTE DATEIEN

- `/opt/greiner-portal/docs/globalcube_analysis/fertigmachen_differenz_analyse_tag184.json`
- `/opt/greiner-portal/scripts/analyse_fertigmachen_differenz.py`

---

## 💡 FAZIT

**Was wir gefunden haben:**
- ✅ Excel "Fertigmachen" = DRIVE (6. Ziffer='2') + 3 Konten (494021, 497061, 497221)
- ✅ Differenz nur noch 5,16 € (0,07%) - praktisch perfekt!

**Was wir noch prüfen müssen:**
- ⏳ Gilt diese Logik auch für andere Standorte?
- ⏳ Gilt diese Logik auch für andere Monate?
- ⏳ Warum genau diese 3 Konten?

**Empfehlung:**
- **Nächster Schritt:** Prüfe andere Standorte und Monate
- **Dann:** Entscheidung ob DRIVE Filter angepasst werden soll

---

*Erstellt: TAG 184 | Autor: Claude AI*
