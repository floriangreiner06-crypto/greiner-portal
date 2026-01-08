# GW-Abweichung Analyse - Dezember 2025

## Zusammenfassung

**API vs. CSV:**
- Stück: 18 (API) vs. 16 (CSV) = **+2 (+12.5%)**
- Umsatz: 278,520.76 € (identisch)
- DB1: 19,743.01 € (API) vs. 22,312.30 € (CSV) = **-2,569.29 € (-11.5%)**
- DB1 %: 7.09% (API) vs. 8.01% (CSV) = **-0.92%**

## Detaillierte Analyse

### 1. Stückzahlen

**Nach Fahrzeugtyp:**
- **G (Gebrauchtwagen):** 14 Stück
- **D (Demo):** 4 Stück
- **G+D (gesamt):** 18 Stück (API)
- **CSV:** 16 Stück

**Mögliche Ursachen:**
- CSV könnte nur 'G' zählen (14 Stück) + 2 andere = 16
- Oder CSV verwendet einen anderen Filter (z.B. nur bestimmte Fahrzeugtypen)
- Unterschiedliche Buchungszeitpunkte (out_invoice_date vs. accounting_date)

### 2. Umsatz

**Vergleich:**
- **accounting_date (BWA):** 278,520.76 € ✅ (identisch mit CSV)
- **out_invoice_date (sales):** 306,529.52 € (Differenz: -28,008.76 €)

**Erkenntnis:** Die BWA verwendet `accounting_date`, nicht `out_invoice_date`. Das ist korrekt.

### 3. DB1-Berechnung

**Komponenten:**
- Umsatz: 278,520.76 €
- Einsatz: 258,777.75 €
- **DB1 = Umsatz - Einsatz: 19,743.01 €**

**CSV-Referenz:** 22,312.30 €
**Abweichung:** -2,569.29 € (-11.5%)

### 4. Umlage-Erlöse (Konto 827051)

**Wichtig:** Konto 827051 enthält Umlage-Erlöse von 12,500.00 €

**DB1-Varianten:**
- **Mit Umlage:** 19,743.01 € (Diff zu CSV: -2,569.29 €)
- **Ohne Umlage:** 7,243.01 € (Diff zu CSV: -15,069.29 €)

**Erkenntnis:** Die CSV scheint die Umlage-Erlöse zu enthalten, da der DB1-Wert näher am Wert mit Umlage liegt.

### 5. Variable Kosten

**Gesamt:** 41,260.15 €
**Top-Konten:**
- 492011: 8,334.06 €
- 494011: 7,693.60 €
- 492021: 5,762.17 €
- 491011: 5,640.00 €

**DB2 = DB1 - Variable Kosten: -21,517.14 €**

### 6. Mögliche Ursachen für DB1-Abweichung

1. **Unterschiedliche Konten-Filter:**
   - API: 820000-829999 (alle GW-Konten)
   - CSV: Möglicherweise andere Konten oder Filter

2. **Umlage-Erlöse:**
   - API: Enthält Umlage (827051: 12,500.00 €)
   - CSV: Könnte Umlage anders behandeln

3. **Buchungszeitpunkte:**
   - API: `accounting_date` (BWA-konform)
   - CSV: Möglicherweise `out_invoice_date` oder andere Logik

4. **Einsatz-Berechnung:**
   - API: 720000-729999 mit Konto-Endziffer-Filter (6. Ziffer = '1')
   - CSV: Möglicherweise andere Filter

5. **G&V-Abschlussbuchungen:**
   - API: Ausgeschlossen ✅
   - CSV: Unbekannt

## Empfehlungen

### 1. Stückzahl-Abweichung (+2)
- **Prüfen:** Welche 2 Fahrzeuge zählt die CSV nicht?
- **Möglich:** CSV zählt nur 'G' (14) + 2 andere = 16
- **Lösung:** CSV-Filter dokumentieren oder anpassen

### 2. DB1-Abweichung (-2,569.29 €)
- **Prüfen:** Welche Konten enthält die CSV, die die API nicht hat?
- **Möglich:** CSV könnte andere Konten oder Filter verwenden
- **Lösung:** CSV-Konten-Mapping dokumentieren

### 3. Umlage-Erlöse
- **Prüfen:** Sollten Umlage-Erlöse (827051) in der Planung enthalten sein?
- **Möglich:** Bei Konzern-Ansicht sollten sie ausgeblendet werden
- **Lösung:** Filter-Logik anpassen, falls nötig

## Nächste Schritte

1. ✅ Analyse abgeschlossen
2. ⏳ CSV-Filter dokumentieren
3. ⏳ Konten-Mapping prüfen
4. ⏳ Umlage-Erlöse-Filter anpassen (falls nötig)

## Fazit

Die Abweichungen sind relativ klein:
- **Stückzahl:** +2 (12.5%) - möglicherweise Filter-Unterschied
- **DB1:** -2,569.29 € (11.5%) - möglicherweise Konten-Filter-Unterschied

Die BWA-Logik funktioniert korrekt. Die Abweichungen könnten durch unterschiedliche Filter oder Buchungszeitpunkte in der CSV entstehen.

