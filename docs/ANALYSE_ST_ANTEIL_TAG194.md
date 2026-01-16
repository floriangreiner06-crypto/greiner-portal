# Analyse St-Anteil Berechnung - TAG 194

**Datum:** 2026-01-16  
**Problem:** St-Anteil in DRIVE (23749 Min) vs. Excel (2321 Min) - Faktor 10x zu hoch!

---

## 🔍 Erkenntnisse

### 1. St-Ant. ist NICHT die gesamte Stempelzeit!

**Beispiel aus Excel:**
- Zeile 1: Dauer = 0:57 (57 Min), **St-Ant. = 0:33 (33 Min)** → Verhältnis 0.58
- Zeile 2: Dauer = 0:40 (40 Min), **St-Ant. = 0:24 (24 Min)** → Verhältnis 0.60
- Zeile 6: Dauer = 1:00 (60 Min), **St-Ant. = 0:11 (11 Min)** → Verhältnis 0.18

**Erkenntnis:** St-Ant. ist **kleiner** als die Dauer!

### 2. St-Ant. = Anteilige Stempelzeit auf Position

**Locosoft-Erklärung:**
> "Wenn mehrere Monteure auf eine Position oder ein Monteur auf mehrere Positionen stempelt, wird dies anteilige verteilt."

**Das bedeutet:**
- Wenn ein Mechaniker auf **mehrere Positionen** eines Auftrags stempelt → St-Ant. = Anteil pro Position
- Wenn **mehrere Mechaniker** auf eine Position stempeln → St-Ant. = Anteil pro Mechaniker

### 3. Excel zeigt aggregierte Werte pro Position

- **Eine Zeile in Excel = eine Position** (nicht eine Stempelung)
- **St-Ant. = Summe aller anteiligen Stempelzeiten** auf diese Position
- **AW-Ant. = Summe aller anteiligen AW** auf diese Position

---

## 📊 Vergleich Excel vs. DRIVE

| Metrik | Excel (Locosoft) | DRIVE (aktuell) | Differenz |
|--------|------------------|-----------------|-----------|
| AW-Anteil | 2820 Min (47.00h) | 4354 Min (72.56h) | +1534 Min |
| St-Anteil | 2321 Min (38.68h) | 23749 Min (395.82h) | +21428 Min ❌ |
| Leistungsgrad | 121.5% | 18.3% | -103.2% |

**Problem:** St-Anteil ist **10x zu hoch** in DRIVE!

---

## 🔧 Nächste Schritte

### 1. SQL-Query korrigieren

**Aktuell (FALSCH):**
```sql
-- Summiert ALLE Stempelzeiten pro Position
SUM(EXTRACT(EPOCH FROM (t.end_time - t.start_time)) / 60) as stempelanteil_minuten
```

**Soll (RICHTIG):**
```sql
-- Berechnet ANTEILIGE Stempelzeit pro Position
-- Wenn Mechaniker auf mehrere Positionen stempelt:
--   St-Ant. = Stempelzeit × (AW_Position / Summe_AW_Auftrag)
-- Wenn mehrere Mechaniker auf Position stempeln:
--   St-Ant. = Stempelzeit × (Stempelzeit_Mechaniker / Summe_Stempelzeit_Position)
```

### 2. Implementierung

Die SQL-Query muss:
1. **Anteilige Verteilung** bei mehreren Positionen berechnen
2. **Anteilige Verteilung** bei mehreren Mechanikern berechnen
3. **Aggregieren** pro Position (wie Excel)

### 3. Test

- Mechaniker 5018 (Jan Majer)
- Zeitraum: 01.01.26 - 15.01.26
- Vergleich: Excel vs. DRIVE

---

**Status:** ⚠️ Problem identifiziert - SQL-Query muss korrigiert werden
