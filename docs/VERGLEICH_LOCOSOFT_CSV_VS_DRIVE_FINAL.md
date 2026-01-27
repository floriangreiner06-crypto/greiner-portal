# Vergleich: Locosoft CSV vs. DRIVE - FINALE ERKENNTNISSE

**Datum:** 2026-01-21  
**TAG:** 206  
**Zweck:** Vergleich der Locosoft CSV-Daten (korrekt) mit unserer DRIVE-Berechnung

---

## 📊 ERGEBNISSE

### Locosoft (CSV - direkt aus Locosoft exportiert) ✅

| Betrieb | St-Anteil | Status |
|---------|-----------|--------|
| **DEGO** | 9.10 Std (9:06) | ✅ **KORREKT** |
| **DEGH** | 3.98 Std (3:59) | ✅ **KORREKT** |
| **GESAMT** | 13.08 Std (13:05) | ✅ **KORREKT** |

### DRIVE (unsere DB-Berechnung) ❌

| Betrieb | St-Anteil | Abweichung | Status |
|---------|-----------|------------|--------|
| **DEGO** | 3.21 Std (3:21) | **-5.89 Std (-64.5%)** | ❌ Viel zu niedrig |
| **DEGH** | 4.43 Std (4:43) | **+0.45 Std (+11.3%)** | ❌ Zu hoch |
| **GESAMT** | 8.04 Std (8:04) | **-5.04 Std (-38.5%)** | ❌ Viel zu niedrig |

---

## 🎯 KRITISCHE ERKENNTNIS

### Locosoft summiert St-Anteil PRO POSITION, nicht pro Zeitblock!

**Beispiel: Auftrag 39527 (DEGO)**
- **Dauer (tatsächliche Stempelzeit):** 0:54 Std (54 Min)
- **St-Anteil (CSV):** 4:30 Std (270 Min) - **5× höher!**
- **Positionen in DB:** 4 Positionen zur gleichen Zeit (08:46-09:40)
- **Berechnung:** 270 Min / 54 Min = **5.0**

**Erkenntnis:**
- Locosoft berechnet St-Anteil **pro Position**
- Wenn mehrere Positionen zur gleichen Zeit gestempelt werden, wird die Zeit **mehrfach gezählt**
- **St-Anteil = Summe der St-Anteil aller Positionen** (nicht dedupliziert!)

### Unsere DB-Berechnung dedupliziert zu aggressiv

**Unsere Methode:**
```sql
DISTINCT ON (employee_number, order_number, start_time, end_time)
```

**Ergebnis:**
- 4 Positionen zur gleichen Zeit → nur 1× gezählt
- **St-Anteil = Dauer** (nicht × Anzahl Positionen)

**Problem:**
- Locosoft zählt jede Position einzeln
- Wir zählen nur den Zeitblock einmal

---

## 💡 WIE BERECHNET LOCOSOFT ST-ANTEIL PRO POSITION?

### Hypothese: St-Anteil pro Position = Dauer × (AW-Position / AW-Gesamt)

**Beispiel Auftrag 39527:**
- Dauer: 54 Min
- Positionen: 4-5 Positionen
- St-Anteil gesamt: 270 Min
- **270 Min / 54 Min = 5.0** → Möglicherweise 5 Positionen?

**Oder:**
- St-Anteil wird nach AW-Anteil aufgeteilt
- Position mit mehr AW bekommt mehr St-Anteil
- **St-Anteil pro Position = Dauer × (AW-Position / AW-Gesamt)**

### Prüfung nötig

**Frage:** Wie wird St-Anteil pro Position berechnet?
- Direkt aus `times`-Tabelle?
- Berechnet aus Dauer × AW-Verhältnis?
- Andere Logik?

---

## 🔧 LÖSUNGSANSATZ

### Option 1: Position-basierte Berechnung (wie Locosoft)

**Methode:**
```sql
-- Summiere St-Anteil pro Position (nicht dedupliziert)
SELECT 
    employee_number,
    SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 3600.0) AS stempelzeit_stunden
FROM times
WHERE type = 2
  AND end_time IS NOT NULL
  AND start_time >= %s
  AND start_time < %s + INTERVAL '1 day'
GROUP BY employee_number
-- KEINE Deduplizierung!
```

**Ergebnis:**
- Jede Position einzeln gezählt
- Gleiche Zeit, verschiedene Positionen → mehrfach gezählt
- **Wie Locosoft!**

**Problem:**
- Kann zu hohe Werte ergeben (wenn Positionen überlappen)
- Aber: CSV zeigt, dass Locosoft genau das macht!

### Option 2: St-Anteil aus labours-Tabelle

**Methode:**
- St-Anteil wird aus `labours`-Tabelle berechnet
- Pro Position mit AW-Anteil
- Summe aller Positionen = Gesamt St-Anteil

**Prüfung nötig:**
- Gibt es St-Anteil-Werte in `labours`?
- Oder wird St-Anteil aus `times` × AW-Verhältnis berechnet?

---

## 📋 NÄCHSTE SCHRITTE

### 1. Prüfe wie Locosoft St-Anteil pro Position berechnet

**Fragen:**
- Wird St-Anteil direkt aus `times`-Tabelle summiert (pro Position)?
- Oder wird St-Anteil aus Dauer × AW-Verhältnis berechnet?
- Gibt es eine andere Logik?

### 2. Teste Position-basierte Berechnung

**Test:**
- Summiere alle Stempelungen ohne Deduplizierung
- Vergleich mit CSV-Daten
- Prüfe ob Werte übereinstimmen

### 3. Implementiere Position-basierte Berechnung

**Wenn Position-basierte Berechnung passt:**
- Implementiere ohne Deduplizierung
- Summiere alle Positionen einzeln
- Vergleich mit CSV-Daten

---

## 🎯 EMPFEHLUNG

### Sofort: Position-basierte Berechnung testen

**Query:**
```sql
-- Position-basierte Berechnung (wie Locosoft)
SELECT 
    employee_number,
    o.subsidiary,
    SUM(EXTRACT(EPOCH FROM (t.end_time - t.start_time)) / 3600.0) AS stempelzeit_stunden
FROM times t
JOIN orders o ON t.order_number = o.number
WHERE t.type = 2
  AND t.end_time IS NOT NULL
  AND t.start_time >= '2026-01-07'
  AND t.start_time < '2026-01-08'
  AND t.employee_number = 5007
GROUP BY employee_number, o.subsidiary
ORDER BY o.subsidiary;
```

**Erwartung:**
- DEGO: ~9.10 Std (vs. CSV 9.10 Std)
- DEGH: ~3.98 Std (vs. CSV 3.98 Std)
- GESAMT: ~13.08 Std (vs. CSV 13.08 Std)

**Wenn passt:** Implementiere Position-basierte Berechnung!

---

**Status:** ✅ Analyse abgeschlossen  
**Erkenntnis:** Locosoft summiert St-Anteil PRO POSITION (nicht dedupliziert) - **Position-basierte Berechnung testen!**
