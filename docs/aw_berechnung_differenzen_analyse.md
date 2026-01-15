# AW-Berechnung Differenzen-Analyse

**Datum:** 2026-01-14  
**Mechaniker:** 5018 (Jan)  
**Datum:** 13.01.26

## Aktuelle Werte

| Metrik | DRIVE | Locosoft | Differenz |
|--------|-------|----------|-----------|
| AW | 9.6 | 10.0 | -0.4 AW |
| Stempelzeit | 452 Min | 451 Min | +1 Min |
| Leistungsgrad | 123.5% | 133.0% | -9.5% |

## Identifizierte Differenzen

### 1. AW-Berechnung

**Problem:** AW-Ant. wird nicht konsistent berechnet.

**Beobachtungen:**
- Für die meisten Positionen: AW-Ant. = AuAW (z.B. 220441, 220375, 220696, 220695)
- Für 220471: AW-Ant. = 0.567 Stunden ≠ AuAW = 1.9 Stunden

**Beispiel 220471:**
- CSV: AW-Ant. = 0:34 = 0.567 Stunden, St-Ant. = 0:29 = 0.483 Stunden
- Datenbank: time_units = 19.00 AW = 1.9 Stunden, Stempelzeit = 28.88 Min
- Verhältnis: AW-Ant. / St-Ant. = 1.172

**Mögliche Erklärungen:**
1. AW-Ant. wird aus einer anderen Quelle berechnet (nicht aus time_units)
2. AW-Ant. wird proportional zur Stempelzeit berechnet, aber mit einem anderen Faktor
3. Es gibt eine separate Stempelzeit pro Position, die nicht in der times Tabelle gespeichert ist

### 2. Stempelzeit

**Problem:** Stempelzeit weicht um 1 Minute ab.

**Mögliche Ursachen:**
1. Rundungsunterschiede
2. Unterschiedliche Pausenberechnung
3. Unterschiedliche Zeitgrenzen (z.B. 07:37 vs. 07:37:00)

### 3. Leistungsgrad

**Problem:** Leistungsgrad weicht um 9.5% ab.

**Formel:** Leistungsgrad = (AW-Ant. / St-Ant.) * 100

**Berechnung:**
- DRIVE: (9.6 / 7.533) * 100 = 127.4% (aber Python gibt 123.5% zurück)
- Locosoft: 133.0%

**Mögliche Ursachen:**
1. Unterschiedliche AW-Berechnung (siehe Punkt 1)
2. Unterschiedliche Stempelzeit-Berechnung (siehe Punkt 2)
3. Unterschiedliche Formel

## CSV-Analyse

**Positionen in CSV (9 Positionen):**
- 220247: Pos 1, Zeile 3 (0.9 Stunden), Pos 1, Zeile 4 (0.1 Stunden), Pos 3, Zeile 2 (0.1 Stunden)
- 220375: Pos 1, Zeile 1 (0.5 Stunden)
- 220441: Pos 1, Zeile 1 (0.5 Stunden), Pos 1, Zeile 4 (0.1 Stunden)
- 220471: Pos 1, Zeile 1 (0.567 Stunden) ← **AUSREISSER**
- 220695: Pos 1, Zeile 4 (0.3 Stunden)
- 220696: Pos 1, Zeile 2 (0.4 Stunden)

**Summe CSV:** 3.467 Stunden = 34.7 AW  
**Locosoft Gesamtsumme:** 10:00 = 10.0 AW

**WICHTIG:** Die CSV-Datei zeigt "10:00" als Gesamtsumme, was 10.0 AW bedeutet (nicht 10.0 Stunden)!

## Nächste Schritte

1. **Prüfe, ob AW-Ant. für 220471 aus einer anderen Quelle berechnet wird**
2. **Prüfe, ob es eine separate Stempelzeit pro Position gibt**
3. **Prüfe, ob die Stempelzeit-Berechnung korrekt ist (1 Min Differenz)**
4. **Prüfe, ob die Leistungsgrad-Formel korrekt ist**

## Offene Fragen

1. Warum ist AW-Ant. für 220471 = 0.567 Stunden statt 1.9 Stunden?
2. Wie wird die Stempelzeit pro Position berechnet (wenn times Tabelle keine order_position hat)?
3. Warum weicht die Stempelzeit um 1 Minute ab?
4. Warum weicht der Leistungsgrad um 9.5% ab?
