# Kontenanalyse Ergebnisse - Variable Kosten Landau - TAG 184

**Datum:** 2026-01-13  
**Status:** ✅ Kontenanalyse durchgeführt

---

## 📊 ERGEBNISSE

### DRIVE Variable Kosten (Landau, Dez 2025):
- **Summe:** 6.173,95 € ✅ (passt perfekt zu DRIVE API)
- **Konten-Anzahl:** 16 Konten mit Werten

### Konten-Aufschlüsselung:

| Bereich | Summe | Beschreibung |
|---------|-------|--------------|
| 4151xx | 478,11 € | Provisionen Finanz-Vermittlung |
| 4355xx | 539,43 € | Trainingskosten |
| 455xx-456xx | 818,03 € | Fahrzeugkosten |
| 4870x | 120,00 € | Werbekosten |
| 491xx-497xx (6. Ziffer=2) | 4.218,38 € | Fertigmachen, Provisionen, Kulanz |
| **GESAMT** | **6.173,95 €** | |

### Top Konten:
1. 492022: 1.472,31 €
2. 492012: 1.157,90 €
3. 494012: 755,00 €
4. 494022: 755,00 €
5. 435532: 499,43 €

---

## ⚠️ PROBLEM: EXCEL vs. DRIVE

### Excel "Fertigmachen":
- **Wert:** 7.043,73 €
- **DRIVE Variable Kosten:** 6.173,95 €
- **Differenz:** -869,78 € (-12,35%)

### Analyse:

**DRIVE Filter (Landau):**
- 491xx-497xx mit **6. Ziffer='2'** = 4.218,38 €
- Plus andere Variable Kosten (4151xx, 4355xx, etc.) = 1.955,57 €
- **Gesamt:** 6.173,95 €

**Excel "Fertigmachen":**
- Vermutlich: 491xx-497xx mit **6. Ziffer='2'** + **bestimmte Konten mit 6. Ziffer='1'**
- Oder: Andere Filter-Logik

**Mögliche Konten mit 6. Ziffer='1' (nicht in DRIVE):**
- 492011: 8.334,06 €
- 494011: 7.693,60 €
- 492021: 5.762,17 €
- 491011: 5.640,00 €
- ... (Summe aller 6. Ziffer='1': 33.283,79 €)

**Problem:** Excel zeigt 7.043,73 €, aber die Summe aller 6. Ziffer='1' + '2' wäre 37.502,17 €.

**Erkenntnis:** Excel enthält **nicht alle** Konten mit 6. Ziffer='1', sondern nur bestimmte!

---

## 💡 MÖGLICHE URSACHEN

### 1. Excel verwendet andere Filter
- Möglicherweise nur bestimmte Konten-Bereiche (z.B. nur 492xx, 494xx)
- Oder bestimmte Konten-Typen
- Oder andere KST-Filter

### 2. Excel "Fertigmachen" ist nicht gleich 491xx-497xx
- Möglicherweise andere Konten-Bereiche
- Oder Mapping aus GlobalCube Struktur-Dateien

### 3. Excel summiert mehrere Positionen
- "Fertigmachen" könnte mehrere Excel-Positionen enthalten
- Nicht nur eine Zeile

---

## 🚀 NÄCHSTE SCHRITTE

### Option 1: GlobalCube Struktur-Dateien analysieren
- `Kontenrahmen.csv` prüfen
- Mapping zwischen Konten und Excel-Positionen finden
- Prüfen welche Konten zu "Fertigmachen" gehören

### Option 2: GlobalCube Portal Reports analysieren
- Auth-Problem beheben
- Portal-Reports für Landau scrapen
- Detaillierte Konten-Aufschlüsselung extrahieren

### Option 3: Excel-Struktur genauer analysieren
- Prüfen ob "Fertigmachen" mehrere Zeilen enthält
- Oder ob andere Positionen zu "Fertigmachen" gehören

### Option 4: DRIVE Filter anpassen (nur wenn nötig)
- Nur wenn Excel-Filter korrekter ist
- Oder wenn GlobalCube Filter-Logik anders ist

---

## ❓ FRAGEN

1. **Ist die -12,35% Differenz akzeptabel?**
   - Wenn ja → Keine Änderungen nötig
   - Wenn nein → Weitere Analyse nötig

2. **Sollen wir DRIVE Filter anpassen?**
   - Nur wenn Excel-Filter korrekter ist
   - Oder wenn GlobalCube Filter-Logik anders ist

3. **Wie sollen wir weiter vorgehen?**
   - GlobalCube Struktur-Dateien analysieren?
   - Portal-Reports scrapen?
   - Excel-Struktur genauer analysieren?

---

## 📁 GENERIERTE DATEIEN

- `/opt/greiner-portal/docs/globalcube_analysis/kontenanalyse_variable_kosten_landau_tag184.json`
- `/opt/greiner-portal/scripts/analyse_variable_kosten_landau.py`

---

## 💡 FAZIT

**Was wir wissen:**
- ✅ DRIVE Variable Kosten Query ist korrekt (6.173,95 €)
- ✅ Excel "Fertigmachen" enthält mehr (7.043,73 €)
- ✅ Excel enthält nicht alle Konten 491xx-497xx
- ✅ Excel enthält möglicherweise bestimmte Konten mit 6. Ziffer='1'

**Was wir nicht wissen:**
- ⏳ Welche Konten Excel genau enthält
- ⏳ Warum Excel mehr enthält
- ⏳ Ob Excel-Filter korrekter ist als DRIVE

**Empfehlung:**
- **Nächster Schritt:** GlobalCube Struktur-Dateien (`Kontenrahmen.csv`) analysieren
- **Oder:** GlobalCube Portal Reports scrapen (nach Auth-Fix)

---

*Erstellt: TAG 184 | Autor: Claude AI*
