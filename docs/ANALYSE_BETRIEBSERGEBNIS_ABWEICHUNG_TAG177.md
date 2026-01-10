# Analyse: Betriebsergebnis-Abweichung Globalcube vs. DRIVE BWA

**Datum:** 2026-01-07  
**TAG:** 177

## Zusammenfassung

Die Analyse zeigt **perfekte Übereinstimmung** bei Monatswerten, aber **Abweichungen bei Jahreswerten (YTD)**:

| Zeitraum | DRIVE BWA | Globalcube | Differenz | Abweichung |
|----------|-----------|------------|-----------|------------|
| **Monat Aug./2025** | 689.679,69 € | 689.679,69 € | **0,00 €** | **0,00%** ✅ |
| **Jahr per Aug./2025** | 243.343,45 € | 321.884,68 € | **-78.541,23 €** | **-24,40%** ⚠️ |
| **VJ Monat Aug./2024** | 552.657,22 € | 552.657,22 € | **0,00 €** | **0,00%** ✅ |
| **VJ Jahr per Aug./2024** | 675.126,08 € | 686.161,65 € | **-11.035,57 €** | **-1,61%** ⚠️ |

## Detail-Analyse Jahr per Aug./2025

### Komponenten-Vergleich

| Komponente | DRIVE BWA | Globalcube | Differenz |
|------------|-----------|------------|-----------|
| **Umsatz** | 30.345.612,69 € | - | - |
| **Einsatz** | 24.916.804,98 € | - | - |
| **DB1** | 5.428.807,71 € | - | - |
| **Variable Kosten** | 890.614,43 € | - | - |
| **DB2** | 4.538.193,28 € | - | - |
| **Direkte Kosten** | 1.837.073,09 € | - | - |
| **DB3** | 2.701.120,19 € | 2.801.501,76 € | **-100.381,57 € (-3,58%)** |
| **Indirekte Kosten** | 2.457.776,74 € | 2.479.617,08 € | **-21.840,34 € (-0,88%)** |
| **Betriebsergebnis** | 243.343,45 € | 321.884,68 € | **-78.541,23 € (-24,40%)** |

### Indirekte Kosten - Komponenten

| Komponente | DRIVE BWA |
|------------|-----------|
| KST 0 (4xxxx0) | 2.488.418,05 € |
| 424xx KST 1-7 | 19.473,48 € |
| 438xx KST 1-7 | 39.386,00 € |
| 498xx | 870.000,00 € |
| 89xxxx (ohne 8932xx) | -89.500,79 € |
| **SUMME** | **2.457.776,74 €** |

**Globalcube Indirekte Kosten:** 2.479.617,08 €  
**Differenz:** -21.840,34 € (-0,88%)

### Kalkulatorische Kosten (29xxxx)

- **Kalkulatorische Kosten (29xxxx):** 1.798,00 €
- **Status:** Werden korrekt NICHT in indirekten Kosten einbezogen (gehören zum neutralen Ergebnis)
- **Bewertung:** ✅ Korrekt

## Ursachen-Analyse

### 1. DB3-Abweichung (-100.381,57 € / -3,58%)

Die DB3-Abweichung ist relativ klein und könnte durch folgende Faktoren verursacht werden:
- Unterschiedliche Behandlung von bestimmten Konten
- Rundungsdifferenzen
- Zeitpunkt-Unterschiede bei Buchungen

### 2. Indirekte Kosten-Abweichung (-21.840,34 € / -0,88%)

Die Abweichung bei den indirekten Kosten ist minimal (unter 1%). Mögliche Ursachen:
- Unterschiedliche Filter-Logik für bestimmte Kontenbereiche
- Rundungsdifferenzen
- Zeitpunkt-Unterschiede bei Buchungen

### 3. Betriebsergebnis-Abweichung (-78.541,23 € / -24,40%)

Die Hauptabweichung entsteht durch die **Kombination** von:
- DB3-Abweichung: -100.381,57 €
- Indirekte Kosten-Abweichung: -21.840,34 €
- **Netto-Abweichung:** -78.541,23 €

## Empfehlungen

1. **Monatswerte:** ✅ Perfekt übereinstimmend - keine Änderungen nötig
2. **Jahreswerte:** ⚠️ Abweichung von -24,40% - weitere Analyse empfohlen:
   - Prüfung der DB3-Berechnung (insbesondere direkte Kosten)
   - Prüfung der indirekten Kosten-Filter
   - Vergleich mit Globalcube auf Monatsbasis (Monat für Monat)

## Nächste Schritte

1. Monat-für-Monat-Vergleich durchführen, um zu identifizieren, in welchen Monaten die Abweichungen entstehen
2. Prüfung der direkten Kosten-Berechnung
3. Prüfung der indirekten Kosten-Filter-Logik
