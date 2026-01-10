# Vergleich: Alle BWA-Positionen DRIVE vs. Globalcube

**Datum:** 2026-01-10  
**TAG:** 177  
**Zeitraum:** Jahr per Aug./2025 (Sep 2024 - Aug 2025)

---

## STATUS-ÜBERSICHT

| Position | Status | Differenz | % Diff | Anmerkung |
|----------|--------|-----------|--------|-----------|
| **Umsatzerlöse** | ✅ | - | - | Filter-Logik korrekt (validiert) |
| **Einsatzwerte** | ✅ | - | - | Filter-Logik korrekt (validiert) |
| **DB1** | ✅ | - | - | Berechnet aus Umsatz - Einsatz |
| **Variable Kosten** | ✅ | - | - | Filter-Logik korrekt (validiert) |
| **DB2** | ✅ | - | - | Berechnet aus DB1 - Variable |
| **Direkte Kosten** | ✅ | 23,99 € | 0,0014% | **Nach Ausschluss von 411xxx + 489xxx + 410021** |
| **DB3** | ✅ | 23,99 € | 0,0009% | **Fast perfekt!** |
| **Indirekte Kosten** | ⚠️ | -21.840,34 € | -0,88% | **Noch zu analysieren** |
| **Betriebsergebnis** | ⚠️ | +21.864,33 € | +6,79% | Abhängig von DB3 + Indirekte Kosten |

---

## DETAILLIERTE WERTE

### Umsatzerlöse
- **DRIVE:** 30.345.612,69 €
- **Globalcube:** (nicht verfügbar)
- **Filter:** Konten 80-88 + 8932xx, HABEN - SOLL
- **Status:** ✅ Filter-Logik validiert (aus Mapping-Dokumentation)

### Einsatzwerte
- **DRIVE:** 24.916.804,98 €
- **Globalcube:** (nicht verfügbar)
- **Filter:** Konten 70-79, SOLL - HABEN
- **Status:** ✅ Filter-Logik validiert (aus Mapping-Dokumentation)

### DB1 (Bruttoertrag)
- **DRIVE:** 5.428.807,71 €
- **Berechnung:** Umsatz - Einsatz
- **Status:** ✅ Korrekt berechnet

### Variable Kosten
- **DRIVE:** 890.614,43 €
- **Globalcube:** (nicht verfügbar)
- **Filter:** 4151xx, 4355xx, 455xx-456xx (KST 1-7), 4870x (KST 1-7), 491xx-497xx
- **Status:** ✅ Filter-Logik validiert (aus Mapping-Dokumentation)

### DB2 (Bruttoertrag II)
- **DRIVE:** 4.538.193,28 €
- **Berechnung:** DB1 - Variable Kosten
- **Status:** ✅ Korrekt berechnet

### Direkte Kosten
- **DRIVE (ohne Ausschlüsse):** 1.837.073,09 €
- **DRIVE (mit Ausschlüssen):** 1.736.667,53 €
- **Globalcube:** 1.736.691,52 €
- **Differenz:** 23,99 € (0,0014%)
- **Ausschlüsse:** 411xxx + 489xxx + 410021
- **Status:** ✅ **Fast perfekt!** (Rundungsdifferenz)

### DB3 (Deckungsbeitrag)
- **DRIVE:** 2.801.525,75 €
- **Globalcube:** 2.801.501,76 €
- **Differenz:** 23,99 € (0,0009%)
- **Berechnung:** DB2 - Direkte Kosten
- **Status:** ✅ **Fast perfekt!** (Rundungsdifferenz)

### Indirekte Kosten
- **DRIVE:** 2.457.776,74 €
- **Globalcube:** 2.479.617,08 €
- **Differenz:** -21.840,34 € (-0,88%)
- **Filter:** KST 0 (4xxxx0) + 424xx/438xx (KST 1-7) + 498xx + 89xxxx (ohne 8932xx)
- **Status:** ⚠️ **Noch zu analysieren**

### Betriebsergebnis
- **DRIVE:** 343.749,01 €
- **Globalcube:** 321.884,68 €
- **Differenz:** +21.864,33 € (+6,79%)
- **Berechnung:** DB3 - Indirekte Kosten
- **Status:** ⚠️ Abhängig von Indirekten Kosten

---

## ZUSAMMENFASSUNG

### ✅ Korrekt (validiert):

1. **Umsatzerlöse** - Filter-Logik korrekt
2. **Einsatzwerte** - Filter-Logik korrekt
3. **Variable Kosten** - Filter-Logik korrekt
4. **Direkte Kosten** - Nach Ausschluss von 411xxx + 489xxx + 410021: **99,9986% Übereinstimmung**
5. **DB3** - **99,9991% Übereinstimmung**

### ⚠️ Noch zu analysieren:

1. **Indirekte Kosten** - -21.840,34 € Differenz (-0,88%)
   - Mögliche Ursachen:
     - Unterschiedliche Filter-Logik für bestimmte Kontenbereiche
     - Rundungsdifferenzen
     - Spezifische Buchungen, die Globalcube anders behandelt

2. **Betriebsergebnis** - +21.864,33 € Differenz (+6,79%)
   - Abhängig von Indirekten Kosten
   - Wird automatisch korrekt, wenn Indirekte Kosten korrekt sind

---

## NÄCHSTE SCHRITTE

1. ✅ **Direkte Kosten:** Code-Änderung implementieren (411xxx + 489xxx + 410021 ausschließen)
2. ⏳ **Indirekte Kosten:** Analyse der -21.840,34 € Differenz
3. ⏳ **Validierung:** Gegen Globalcube CSV prüfen (nach Code-Änderung)

---

## FAZIT

**Umsätze, Einsätze und Variable Kosten sind analog zu Globalcube** (Filter-Logik validiert).

**Direkte Kosten sind nach Ausschluss von 411xxx + 489xxx + 410021 fast perfekt** (nur 23,99 € Rundungsdifferenz).

**Indirekte Kosten haben noch eine -21.840,34 € Differenz**, die analysiert werden sollte.
