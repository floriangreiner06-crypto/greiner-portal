# Vergleich: Locosoft CSV vs. DRIVE - MA 5007, 07.01.2026

**Datum:** 2026-01-21  
**TAG:** 206  
**Zweck:** Vergleich der Locosoft CSV-Daten (korrekt) mit unserer DRIVE-Berechnung

---

## 📊 ERGEBNISSE

### Locosoft (CSV - direkt aus Locosoft exportiert) ✅

| Betrieb | St-Anteil | Status |
|---------|-----------|--------|
| **DEGO** | 9.10 Std (9:06) | ✅ Korrekt |
| **DEGH** | 3.98 Std (3:59) | ✅ Korrekt |
| **GESAMT** | 13.08 Std (13:05) | ✅ Korrekt |

### DRIVE (unsere DB-Berechnung) ❌

| Betrieb | St-Anteil | Abweichung | Status |
|---------|-----------|------------|--------|
| **DEGO** | 3.21 Std (3:21) | **-5.89 Std (-64.5%)** | ❌ Viel zu niedrig |
| **DEGH** | 4.43 Std (4:43) | **+0.45 Std (+11.3%)** | ❌ Zu hoch |
| **GESAMT** | 8.04 Std (8:04) | **-5.04 Std (-38.5%)** | ❌ Viel zu niedrig |

---

## 🔍 ERKENNTNISSE

### 1. Locosoft summiert St-Anteil PRO POSITION

**Beispiel: Auftrag 39527 (DEGO)**
- **Dauer:** 0:54 Std (54 Min) - tatsächliche Stempelzeit
- **St-Anteil (CSV):** 4:30 Std (270 Min) - **5× höher!**
- **Positionen in DB:** 4 Positionen zur gleichen Zeit (08:46-09:40)
- **Berechnung:** 270 Min / 54 Min = **5.0** → Möglicherweise 5 Positionen?

**Erkenntnis:**
- Locosoft berechnet St-Anteil **pro Position**
- Wenn 4-5 Positionen zur gleichen Zeit gestempelt werden, wird die Zeit **4-5× gezählt**
- **St-Anteil = Dauer × Anzahl Positionen** (oder ähnlich)

### 2. Unsere DB-Berechnung dedupliziert zu aggressiv

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

### 3. DEGO vs. DEGH: Unterschiedliche Abweichungen

**DEGO:**
- Locosoft: 9.10 Std
- DRIVE: 3.21 Std
- **Abweichung: -5.89 Std (-64.5%)**
- **Problem:** Viele Positionen zur gleichen Zeit → zu aggressiv dedupliziert

**DEGH:**
- Locosoft: 3.98 Std
- DRIVE: 4.43 Std
- **Abweichung: +0.45 Std (+11.3%)**
- **Problem:** Weniger Positionen zur gleichen Zeit → näher, aber immer noch falsch

---

## 💡 WIE BERECHNET LOCOSOFT ST-ANTEIL?

### Hypothese 1: St-Anteil = Dauer × Anzahl Positionen

**Beispiel Auftrag 39527:**
- Dauer: 54 Min
- Positionen: 4 (in DB) oder 5 (in CSV?)
- St-Anteil: 270 Min = 54 Min × 5

**Problem:** Passt nicht immer (z.B. Auftrag 219184: Dauer 19 Min, St-Anteil 19 Min)

### Hypothese 2: St-Anteil = Summe der St-Anteil pro Position

**Jede Position hat eigenen St-Anteil:**
- Position 1: St-Anteil = X Min
- Position 2: St-Anteil = Y Min
- Position 3: St-Anteil = Z Min
- **Gesamt = X + Y + Z**

**Problem:** Wie wird St-Anteil pro Position berechnet?

### Hypothese 3: St-Anteil = Zeit aufgeteilt nach AW-Anteil

**Mögliche Logik:**
- Gesamte Stempelzeit wird nach AW-Anteil aufgeteilt
- Position mit mehr AW bekommt mehr St-Anteil
- **St-Anteil pro Position = Dauer × (AW-Position / AW-Gesamt)**

**Prüfung nötig:** Vergleich AW-Anteil vs. St-Anteil in CSV

---

## 📋 CSV-DATEN ANALYSE

### Stempelungen aus CSV (MA 5007, 07.01.2026)

| von | bis | Dauer | Auftrag | St-Anteil | AW-Anteil | Position |
|-----|-----|-------|---------|-----------|-----------|----------|
| 08:46 | 09:40 | 0:54 | 39527 | **4:30** | 0:24 | 1,06 G |
| 09:40 | 09:59 | 0:19 | 219184 | **0:19** | 0:42 | 2,04 G |
| 09:59 | 10:47 | 0:47 | 220445 | **0:47** | 0:27 | 1,03 W |
| 10:47 | 11:03 | 0:17 | 220067 | **0:10** | 0:18 | 3,05 G |
| -""- | F | - | 220067 | **0:07** | 0:12 | 4,05 G |
| 11:04 | 11:10 | 0:07 | 39809 | **0:25** | 0:11 | 1,07 G |
| -""- | F | - | 39809 | **0:02** | 0:04 | 1,08 G |
| 11:11 | 11:37 | 0:27 | 39524 | **2:15** | 0:24 | 1,06 G |
| 11:37 | 11:44 | 0:07 | 220624 | **0:00** | 0:00 | 1,04 G |
| -""- | F | - | 220624 | **0:07** | 1:30 | 1,08 G |
| 11:44 | 14:58 | 2:29 | 220542 | **0:34** | 0:30 | 1,04 G |
| -""- | F | - | 220542 | **0:13** | 0:11 | 1,05 G |
| -""- | F | - | 220542 | **0:13** | 0:11 | 1,08 G |
| -""- | F | - | 220542 | **1:29** | 1:18 | 2,04 G |
| -""- | F | - | 220542 | **0:00** | 0:00 | 2,05 G |
| 14:58 | 16:52 | 1:54 | 39537 | **1:30** | 1:12 | 2,06 W |
| -""- | F | - | 39537 | **0:24** | 0:19 | 2,08 W |

**Gesamt St-Anteil:** 13.08 Std (13:05) ✅

---

## 🔍 DETAILANALYSE: Auftrag 39527

### DB-Daten (4 Positionen zur gleichen Zeit)

| Position | Line | Start | End | Dauer |
|----------|------|-------|-----|-------|
| 1 | 4 | 08:46:42 | 09:40:33 | 53.85 Min |
| 1 | 5 | 08:46:42 | 09:40:33 | 53.85 Min |
| 1 | 6 | 08:46:42 | 09:40:33 | 53.85 Min |
| 1 | 7 | 08:46:42 | 09:40:33 | 53.85 Min |

**Unsere Berechnung:**
- Dedupliziert: 1× 53.85 Min = **0.90 Std**

**Locosoft (CSV):**
- St-Anteil: **4:30 Std (270 Min)**
- **270 Min / 53.85 Min = 5.01** → Möglicherweise 5 Positionen?

**Frage:** Gibt es eine 5. Position, die nicht in `times`-Tabelle ist?

---

## 🎯 NÄCHSTE SCHRITTE

### 1. Prüfe Positionen in labours-Tabelle

**Query:**
```sql
SELECT 
    order_number,
    order_position,
    order_position_line,
    time_units,
    mechanic_no
FROM labours
WHERE order_number = 39527
  AND mechanic_no = 5007
ORDER BY order_position, order_position_line;
```

**Frage:** Gibt es mehr Positionen in `labours` als in `times`?

### 2. Prüfe wie Locosoft St-Anteil pro Position berechnet

**Mögliche Logiken:**
- St-Anteil = Dauer × (AW-Position / AW-Gesamt)
- St-Anteil = Dauer × Anzahl Positionen
- St-Anteil = Feste Zuordnung pro Position

### 3. Implementiere Position-basierte Berechnung

**Neue Methode:**
- St-Anteil = Summe der St-Anteil pro Position
- Jede Position einzeln zählen (wie Locosoft)

---

**Status:** ✅ Analyse abgeschlossen  
**Erkenntnis:** Locosoft summiert St-Anteil PRO POSITION, nicht pro Zeitblock!
