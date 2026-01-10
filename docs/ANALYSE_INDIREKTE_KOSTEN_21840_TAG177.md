# Analyse: Indirekte Kosten -21.840,34 € Differenz

**Datum:** 2026-01-10  
**TAG:** 177  
**Status:** ⚠️ **Noch nicht vollständig gelöst**

---

## ZUSAMMENFASSUNG

**Indirekte Kosten Differenz:**
- **DRIVE:** 2.457.776,74 €
- **Globalcube:** 2.479.617,08 €
- **Differenz:** -21.840,34 € (-0,88%)

**Bewertung:** Die Abweichung von 0,88% ist relativ gering, aber sollte analysiert werden.

---

## KOMPONENTEN-ANALYSE

### Aktuelle Komponenten (DRIVE):

| Komponente | Wert (€) | % von Gesamt |
|------------|----------|--------------|
| KST 0 (4xxxx0) | 2.488.418,05 | 101,2% |
| 424xx KST 1-7 | 19.473,48 | 0,8% |
| 438xx KST 1-7 | 39.386,00 | 1,6% |
| 498xx | 870.000,00 | 35,4% |
| 89xxxx (ohne 8932xx) | -89.500,79 | -3,6% |
| **GESAMT** | **2.457.776,74** | **100,0%** |

**Hinweis:** Die Summe der Komponenten ergibt 3.327.776,74 €, aber das ist falsch (doppelte Zählung). Die tatsächliche Summe ist 2.457.776,74 €.

---

## KONTENBEREICHE-ANALYSE

### Größte Kontenbereiche:

| Kontenbereich | Anzahl | Wert (€) | % von Gesamt |
|---------------|--------|----------|--------------|
| 498xxx | 19 | 870.000,00 | 35,4% |
| 450xxx | 195 | 378.586,41 | 15,4% |
| 487xxx | 380 | 206.150,55 | 8,4% |
| 452xxx | 518 | 160.351,91 | 6,5% |
| 458xxx | 174 | 130.666,35 | 5,3% |
| 440xxx | 95 | 109.332,00 | 4,5% |
| 473xxx | 30 | 105.734,88 | 4,3% |
| 474xxx | 101 | 83.836,68 | 3,4% |
| ... | ... | ... | ... |

---

## GETESTETE VARIANTEN

### 1. skr51_cost_center statt 5. Stelle
- **Ergebnis:** 5.184.654,12 € (viel zu viel)
- **Status:** ❌ Nicht die Lösung

### 2. KST 0-9 statt nur KST 0
- **Ergebnis:** 5.184.654,12 € (viel zu viel)
- **Status:** ❌ Nicht die Lösung

### 3. 424xx/438xx mit KST 1-7 (inkl. 4,5) statt nur 1,2,3,6,7
- **Ergebnis:** 2.457.776,74 € (keine Änderung)
- **Status:** ❌ Keine KST 4,5 in 424xx/438xx vorhanden

### 4. Ohne 89xxxx
- **Ergebnis:** 2.547.277,53 € (zu viel, Diff: 67.660,45 €)
- **Status:** ❌ Nicht die Lösung

### 5. Ohne 891xxx
- **Ergebnis:** 2.497.815,79 € (Diff: 18.198,71 €)
- **Status:** ⚠️ Näher, aber noch nicht exakt

### 6. Ohne 896xxx
- **Ergebnis:** 2.507.238,48 € (Diff: 27.621,40 €)
- **Status:** ❌ Nicht die Lösung

### 7. 435xxx/459xxx KST 1-7 zusätzlich
- **Ergebnis:** 2.506.528,22 € (zu viel, Diff: 26.911,14 €)
- **Status:** ❌ Nicht die Lösung

---

## MÖGLICHE URSACHEN

### 1. Rundungsdifferenzen
- PostgreSQL vs. Cognos Rundungslogik
- Unterschiedliche Behandlung von HABEN-Buchungen

### 2. Spezifische Filter-Logik in Globalcube
- Möglicherweise werden bestimmte Kontenbereiche anders behandelt
- Oder: Spezifische Buchungen, die Globalcube anders filtert

### 3. Kombination von vielen kleinen Beträgen
- Viele kleine Beträge könnten zusammen 21.840,34 € ergeben
- Aber: Keine exakte Kombination gefunden

### 4. Unterschiedliche Behandlung von 89xxxx
- 89xxxx hat -89.500,79 € (negativ)
- Möglicherweise zählt Globalcube 89xxxx anders oder gar nicht

---

## NÄCHSTE SCHRITTE

1. ⏳ **Weitere Analyse:** Prüfen, ob bestimmte Kontenbereiche ausgeschlossen werden sollten
2. ⏳ **89xxxx detailliert:** Analysieren, welche Konten in 89xxxx ausgeschlossen werden sollten
3. ⏳ **Cognos Reports analysieren:** Filter-Logik in Cognos Reports finden
4. ⏳ **Monat-für-Monat-Vergleich:** Identifizieren, in welchen Monaten die Differenz entsteht

---

## EMPFEHLUNG

**Die -21.840,34 € Differenz (0,88%) ist relativ gering.**

**Priorität:**
1. ✅ **Direkte Kosten:** Code-Änderung implementieren (411xxx + 489xxx + 410021 ausschließen)
2. ⏳ **Indirekte Kosten:** Weitere Analyse nach Implementierung der direkten Kosten

**Begründung:**
- Die Abweichung von 0,88% ist deutlich kleiner als die ursprüngliche DB3-Abweichung von 5,8%
- Die Hauptursache (direkte Kosten) ist identifiziert und kann behoben werden
- Indirekte Kosten können später analysiert werden, wenn die direkten Kosten korrekt sind

---

## ZUSAMMENFASSUNG

**Status:**
- ✅ **Umsätze, Einsätze, Variable Kosten:** Analog zu Globalcube (validiert)
- ✅ **Direkte Kosten:** Fast perfekt nach Ausschluss von 411xxx + 489xxx + 410021 (nur 23,99 € Rundungsdifferenz)
- ⚠️ **Indirekte Kosten:** -21.840,34 € Differenz (0,88%) - weitere Analyse möglich, aber nicht kritisch

**Nächste Aktion:**
1. Code-Änderung für direkte Kosten implementieren
2. Danach: Indirekte Kosten weiter analysieren (falls nötig)
