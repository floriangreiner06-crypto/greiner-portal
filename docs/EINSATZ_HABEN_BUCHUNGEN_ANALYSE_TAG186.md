# Einsatz HABEN-Buchungen Analyse - Hersteller-Boni TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** 🔍 **ANALYSE**

---

## 🎯 PROBLEM

**Gesamtbetrieb Einsatz YTD:**
- DRIVE: 9.223.769,97 €
- GlobalCube: 9.191.864,00 €
- **Differenz:** +31.905,97 € (+0,35%)

**Hypothese:** HABEN-Buchungen (einsatzmindernd) könnten Hersteller-Boni sein, die ausgeschlossen werden sollten.

---

## 📊 ERGEBNISSE

### HABEN-Buchungen (einsatzmindernd)

**Gesamt:**
- Anzahl Buchungen: 12.027
- Anzahl Konten: 147
- **HABEN-Wert (einsatzmindernd):** 1.988.936,54 €
- **SOLL-Wert (einsatzerhöhend):** 11.212.706,51 €
- **NETTO-Wert (Einsatz):** 9.223.769,97 €

### Top 10 Konten mit HABEN-Buchungen

| Konto | Subsidiary | HABEN-Wert | SOLL-Wert | NETTO-Wert | Bezeichnung |
|-------|------------|------------|-----------|------------|-------------|
| 717001 | 1 (Stellantis) | 809.611,38 € | 811.306,73 € | 1.695,35 € | EW Sonstige Erlöse Neuwagen |
| 717001 | 2 (Hyundai) | 97.372,40 € | 102.567,75 € | 5.195,35 € | EW Sonstige Erlöse Neuwagen |
| 710631 | 2 (Hyundai) | 74.377,10 € | 327.444,86 € | 253.067,76 € | NW EW Tucson an Gewerbekd Leas |
| 727001 | 1 (Stellantis) | 70.807,96 € | 86.652,56 € | 15.844,60 € | Sonstige Einsatzwerte GW |
| 710611 | 2 (Hyundai) | 48.567,56 € | 149.764,20 € | 101.196,64 € | NW EW Tucson an Kunden Leas |
| 711951 | 1 (Stellantis) | 44.320,30 € | 232.397,21 € | 188.076,91 € | NW EW Grandland X Großkd leas |
| 710621 | 2 (Hyundai) | 36.489,54 € | 157.203,56 € | 120.714,02 € | NW EW Tucson an Gewerbekd Kauf |
| 710601 | 2 (Hyundai) | 35.134,49 € | 115.086,94 € | 79.952,45 € | NW EW Tucson an Kunden Kauf |
| 710941 | 1 (Stellantis) | 34.332,00 € | 114.858,13 € | 80.526,13 € | NW EW Mokka an Großkd Kauf |
| 710641 | 1 (Stellantis) | 32.632,06 € | 86.226,31 € | 53.594,25 € | NW EW Astra an Großkd Kauf |

**Summe Top 10:** 1.283.245,19 € HABEN-Wert

---

## 🔍 ANALYSE

### Konten-Identifikation

**Konten mit hohen HABEN-Buchungen:**
1. **717001** (EW Sonstige Erlöse Neuwagen): 906.983,78 € HABEN
   - Stellantis: 809.611,38 €
   - Hyundai: 97.372,40 €
   - **Vermutung:** Hersteller-Boni/Gutschriften für Neuwagen

2. **710631** (NW EW Tucson an Gewerbekd Leas): 74.377,10 € HABEN
   - **Vermutung:** Hersteller-Boni für Tucson Leasing

3. **727001** (Sonstige Einsatzwerte GW): 87.018,58 € HABEN
   - Stellantis: 70.807,96 €
   - Hyundai: 16.210,62 €
   - **Vermutung:** Gutschriften/Gutschriften für Gebrauchtwagen

4. **710611** (NW EW Tucson an Kunden Leas): 48.567,56 € HABEN
   - **Vermutung:** Hersteller-Boni für Tucson Leasing

5. **711951** (NW EW Grandland X Großkd leas): 44.320,30 € HABEN
   - **Vermutung:** Hersteller-Boni für Grandland X Leasing

### Mögliche Lösungen

#### Option 1: HABEN-Buchungen komplett ausschließen

**Ergebnis:**
- Einsatz OHNE HABEN-Buchungen (nur SOLL): 11.212.706,51 €
- GlobalCube: 9.191.864,00 €
- **Differenz:** +2.020.842,51 € ❌ (viel zu hoch!)

**Erkenntnis:** HABEN-Buchungen sind definitiv Teil des Einsatzes, aber möglicherweise werden bestimmte Konten von GlobalCube anders behandelt.

#### Option 2: Bestimmte Konten ausschließen

**Kandidaten:**
- **717001** (EW Sonstige Erlöse Neuwagen): 906.983,78 €
  - Wenn ausgeschlossen: 9.223.769,97 - 906.983,78 = 8.316.786,19 €
  - GlobalCube: 9.191.864,00 €
  - **Differenz:** -875.077,81 € ❌ (immer noch zu hoch)

- **727001** (Sonstige Einsatzwerte GW): 87.018,58 €
  - Wenn ausgeschlossen: 9.223.769,97 - 87.018,58 = 9.136.751,39 €
  - GlobalCube: 9.191.864,00 €
  - **Differenz:** -55.112,61 € ⚠️ (besser, aber noch nicht perfekt)

#### Option 3: Bestimmte Konten mit negativem NETTO-Wert ausschließen

**Konten mit negativem NETTO-Wert:**
- **727501** (GIVIT Garantien GW): -13.917,40 €
  - HABEN: 13.917,40 €, SOLL: 0,00 €
  - **Vermutung:** Garantie-Gutschriften, die ausgeschlossen werden sollten

**Ergebnis:**
- Wenn 727501 ausgeschlossen: 9.223.769,97 - (-13.917,40) = 9.237.687,37 €
- GlobalCube: 9.191.864,00 €
- **Differenz:** +45.823,37 € ⚠️ (schlechter!)

---

## 💡 HYPOTHESEN

### Hypothese 1: GlobalCube schließt bestimmte Konten aus

**Mögliche Kandidaten:**
- 717001 (EW Sonstige Erlöse Neuwagen) - 906.983,78 € HABEN
- 727001 (Sonstige Einsatzwerte GW) - 87.018,58 € HABEN
- 727501 (GIVIT Garantien GW) - 13.917,40 € HABEN (negativ)

### Hypothese 2: GlobalCube behandelt HABEN-Buchungen anders

**Mögliche Behandlung:**
- GlobalCube könnte HABEN-Buchungen nur für bestimmte Konten berücksichtigen
- Oder: GlobalCube könnte HABEN-Buchungen nur für bestimmte Buchungstypen berücksichtigen

### Hypothese 3: Buchungstext-Filter

**Mögliche Filter:**
- GlobalCube könnte Buchungen mit bestimmten Texten ausschließen
- Oder: GlobalCube könnte nur bestimmte Buchungstypen berücksichtigen

---

## 📋 BENÖTIGTE INFORMATIONEN

**Vom Benutzer:**
1. Welche Konten erfasst GlobalCube für Gesamtbetrieb Einsatz?
2. Werden HABEN-Buchungen (einsatzmindernd) von GlobalCube berücksichtigt?
3. Gibt es bestimmte Konten, die ausgeschlossen werden sollten?
4. Gibt es bestimmte Buchungstexte, die ausgeschlossen werden sollten?

**Konkrete Fragen:**
1. Ist **717001** (EW Sonstige Erlöse Neuwagen) in GlobalCube enthalten?
2. Ist **727001** (Sonstige Einsatzwerte GW) in GlobalCube enthalten?
3. Ist **727501** (GIVIT Garantien GW) in GlobalCube enthalten?
4. Wie behandelt GlobalCube HABEN-Buchungen (einsatzmindernd)?

---

## 📊 STATUS

- ✅ HABEN-Buchungen identifiziert (1.988.936,54 €)
- ✅ Top 30 Konten mit Kontobezeichnungen analysiert
- ⏳ Benötigt: GlobalCube-Konten-Liste für Vergleich
- ⏳ Benötigt: Bestätigung, welche Konten ausgeschlossen werden sollten

---

**Nächster Schritt:** GlobalCube-Konten-Liste besorgen und mit DRIVE vergleichen.
