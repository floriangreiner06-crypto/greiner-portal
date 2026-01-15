# Leistungsgrad-Berechnung in DRIVE - Erklärung für das Team

**Datum:** 2026-01-14  
**Version:** Aktuell (TAG 191)

---

## Was ist der Leistungsgrad?

Der **Leistungsgrad (LG)** zeigt, wie effizient ein Mechaniker gearbeitet hat. Er vergleicht die **erfassten Arbeitswerte (AW)** mit der **Stempelzeit**.

**Formel:**
```
Leistungsgrad = (AW in Stunden / Stempelzeit in Stunden) × 100
```

**Beispiel:**
- Ein Mechaniker hat 10 AW erfasst (= 1.0 Stunde)
- Er hat 0.75 Stunden (45 Minuten) gestempelt
- Leistungsgrad = (1.0 / 0.75) × 100 = **133.3%**

**Interpretation:**
- **100%** = Der Mechaniker hat genau die Vorgabezeit erreicht
- **> 100%** = Der Mechaniker war schneller als die Vorgabe (gut!)
- **< 100%** = Der Mechaniker war langsamer als die Vorgabe

---

## Wie berechnet DRIVE den Leistungsgrad?

### 1. AW-Berechnung (AW-Anteil)

**Grundprinzip:** AW werden **pro Position** berechnet und dann summiert.

**Formel pro Position:**
```
AW-Ant. = time_units_Position × (Stempelzeit_Mechaniker / Gesamt-Stempelzeit_Auftrag)
```

**Beispiel:**
- Auftrag hat 2 Positionen: Position 1 = 10 AW, Position 2 = 5 AW
- Mechaniker A hat 30 Min gestempelt, Mechaniker B hat 20 Min gestempelt
- Gesamt-Stempelzeit = 50 Min

**Für Mechaniker A:**
- Position 1: AW-Ant. = 10 AW × (30 Min / 50 Min) = 6 AW
- Position 2: AW-Ant. = 5 AW × (30 Min / 50 Min) = 3 AW
- **Gesamt AW = 9 AW**

**Für Mechaniker B:**
- Position 1: AW-Ant. = 10 AW × (20 Min / 50 Min) = 4 AW
- Position 2: AW-Ant. = 5 AW × (20 Min / 50 Min) = 2 AW
- **Gesamt AW = 6 AW**

**Wichtig:**
- Wenn nur **ein Mechaniker** an einem Auftrag arbeitet: AW-Ant. = time_units_Position
- Wenn **mehrere Mechaniker** arbeiten: AW werden proportional zur Stempelzeit verteilt

### 2. Stempelzeit-Berechnung

**Grundprinzip:** Stempelzeit = Summe aller gestempelten Zeiten an externen Aufträgen

**Filter:**
- Nur **externe Aufträge** (order_number > 31)
- Nur **Typ 2** (Arbeitszeit, nicht Anwesenheit)
- **Duplikate werden entfernt** (gleiche Start-/Endzeit)

**Beispiel:**
- Mechaniker stempelt von 08:00 bis 10:00 an Auftrag 12345 → 120 Min
- Mechaniker stempelt von 10:30 bis 12:00 an Auftrag 12346 → 90 Min
- **Gesamt Stempelzeit = 210 Min = 3.5 Stunden**

### 3. Leistungsgrad-Berechnung

**Formel:**
```
Leistungsgrad = (AW in Stunden / Stempelzeit_Leistungsgrad in Stunden) × 100
```

**Wichtig:** Es wird eine **separate Stempelzeit für den Leistungsgrad** verwendet!

**Stempelzeit_Leistungsgrad:**
- **Von:** Erste externe Stempelung des Tages
- **Bis:** Letzte externe Stempelung des Tages
- **Minus:** Lücken zwischen 10-60 Minuten
- **Minus:** Pausenzeiten (z.B. 12:00-12:44)

**Beispiel:**
- Erste Stempelung: 07:37
- Letzte Stempelung: 16:45
- Lücke 10:00-10:30 (30 Min) → wird abgezogen
- Pause 12:00-12:44 (44 Min) → wird abgezogen
- **Stempelzeit_Leistungsgrad = 9:14 - 0:30 - 0:44 = 8:00 Stunden**

**Berechnung:**
- AW = 10.0 AW = 1.0 Stunde
- Stempelzeit_Leistungsgrad = 8.0 Stunden
- **Leistungsgrad = (1.0 / 8.0) × 100 = 12.5%**

---

## Praktisches Beispiel

**Mechaniker:** Jan (5018)  
**Datum:** 13.01.26

### Schritt 1: AW-Berechnung

**Aufträge des Tages:**
- Auftrag 39413: Position 1 (10 AW), Position 2 (4 AW), Position 3 (1 AW), Position 4 (5 AW)
- Auftrag 220471: Position 1 (19 AW)
- ... weitere Aufträge

**Berechnung pro Position:**
- Auftrag 39413: Nur Jan arbeitet → AW-Ant. = 10 + 4 + 1 + 5 = 20 AW
- Auftrag 220471: Nur Jan arbeitet → AW-Ant. = 19 AW
- ... weitere Aufträge

**Gesamt AW = 101 AW = 10.1 Stunden**

### Schritt 2: Stempelzeit-Berechnung

**Stempelungen:**
- 07:37 - 08:06 (Auftrag 220471) → 29 Min
- 08:07 - 08:42 (Auftrag 220441) → 35 Min
- ... weitere Stempelungen

**Gesamt Stempelzeit = 452 Min = 7.53 Stunden**

### Schritt 3: Stempelzeit_Leistungsgrad

**Zeitspanne:**
- Erste Stempelung: 07:37
- Letzte Stempelung: 16:45
- **Spanne = 9:08 Stunden**

**Abzüge:**
- Lücken zwischen Stempelungen (10-60 Min)
- Pause 12:00-12:44 (44 Min)

**Stempelzeit_Leistungsgrad = 8.27 Stunden**

### Schritt 4: Leistungsgrad

```
Leistungsgrad = (10.1 Stunden / 8.27 Stunden) × 100 = 122.1%
```

**Interpretation:**
- Jan hat 122.1% der Vorgabezeit erreicht
- Er war **22.1% schneller** als die Vorgabe
- **Sehr gute Leistung!**

---

## Wichtige Punkte für das Team

### 1. AW werden proportional verteilt

**Wenn mehrere Mechaniker an einem Auftrag arbeiten:**
- AW werden **nicht einfach geteilt**
- Sondern **proportional zur Stempelzeit** verteilt
- **Fairer Anteil** für jeden Mechaniker

**Beispiel:**
- Auftrag mit 10 AW Vorgabe
- Mechaniker A: 60 Min gestempelt
- Mechaniker B: 40 Min gestempelt
- **Nicht:** 5 AW / 5 AW
- **Sondern:** 6 AW / 4 AW (proportional)

### 2. Stempelzeit_Leistungsgrad ≠ Stempelzeit

**Unterschied:**
- **Stempelzeit:** Summe aller gestempelten Zeiten
- **Stempelzeit_Leistungsgrad:** Erste bis letzte Stempelung minus Lücken/Pausen

**Warum?**
- Locosoft verwendet diese Logik
- Berücksichtigt Pausen und Lücken
- **Fairere Bewertung** der tatsächlichen Arbeitszeit

### 3. Nur fakturierte Positionen zählen

**Filter:**
- Nur Positionen mit `is_invoiced = true`
- Nur Positionen, bei denen der Mechaniker **tatsächlich gestempelt** hat
- Nur Positionen mit `time_units > 0`

**Warum?**
- Nur **verrechnete Arbeit** zählt
- Keine "Luftbuchungen"
- **Realistische Bewertung**

### 4. Aktuelle Abweichung zu Locosoft

**Problem:**
- DRIVE: 9.6 AW, Leistungsgrad 123.5%
- Locosoft: 10.0 AW, Leistungsgrad 133.0%
- **Differenz: 0.4 AW, 9.5% Leistungsgrad**

**Ursache:**
- Locosoft berechnet AW-Ant. anders (noch nicht vollständig verstanden)
- **Support-Anfrage an Locosoft** ist gestellt
- **Bis zur Klärung:** DRIVE-Werte sind sehr nahe, aber nicht identisch

---

## Häufige Fragen

### Q: Warum ist mein Leistungsgrad niedrig?

**A:** Mögliche Ursachen:
- Lange Pausen oder Lücken
- Viele Aufträge mit niedrigen AW-Vorgaben
- Stempelungen fehlen oder sind unvollständig

### Q: Warum weicht mein Leistungsgrad von Locosoft ab?

**A:** Aktuell gibt es eine kleine Abweichung (siehe oben). Wir arbeiten an der exakten Übereinstimmung.

### Q: Wie kann ich meinen Leistungsgrad verbessern?

**A:**
- **Schneller arbeiten** (mehr AW in weniger Zeit)
- **Weniger Pausen/Lücken** (kontinuierliche Arbeit)
- **Korrekte Stempelungen** (keine fehlenden Zeiten)

### Q: Zählen alle Aufträge?

**A:** Nein, nur:
- **Externe Aufträge** (nicht Leerlauf)
- **Fakturierte Positionen** (verrechnete Arbeit)
- **Positionen mit Stempelzeit** (tatsächlich gearbeitet)

---

## Zusammenfassung

**Leistungsgrad = (AW / Stempelzeit_Leistungsgrad) × 100**

**Wichtig:**
1. AW werden **proportional zur Stempelzeit** verteilt
2. Stempelzeit_Leistungsgrad berücksichtigt **Pausen und Lücken**
3. Nur **fakturierte Positionen** zählen
4. Aktuell kleine **Abweichung zu Locosoft** (wird geklärt)

**Ziel:** Fairer Vergleich der tatsächlichen Leistung jedes Mechanikers!
