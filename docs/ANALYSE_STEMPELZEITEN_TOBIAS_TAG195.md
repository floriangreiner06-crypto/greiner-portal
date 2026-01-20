# Analyse: Stempelzeiten von Tobias - Auftrag 220521

**Datum:** 2026-01-16  
**TAG:** 195  
**Problem:** Wie können 17 Stunden auf einen Auftrag gestempelt sein?

---

## 🔍 Problem-Identifikation

### Auftrag 220521 (Tobias, 13.01.2026)

**OHNE Deduplizierung:**
- 30 Stempelungen
- Summiert: **45.33 Stunden** (2720 Min)
- Zeit-Spanne: 8.90 Stunden (08:00 - 16:55)

**MIT Deduplizierung (DISTINCT ON):**
- 3 Stempelungen
- Summiert: **4.56 Stunden** (273 Min)
- Zeit-Spanne: **8.90 Stunden** (534 Min)

**DIFFERENZ:** 2461 Min zu viel!

---

## 📊 Detaillierte Analyse

### Stempelungen (30x dupliziert)

**Zeitblock 1:**
- 10x: 08:00:51 - 08:55:22 (55 Min)
- Positionen: 1/1, 1/2, 1/3, 1/4, 1/5, 1/6, 1/7, 1/8, 1/9, 1/99

**Zeitblock 2:**
- 10x: 11:30:38 - 13:12:45 (102 Min)
- Positionen: 1/1, 1/2, 1/3, 1/4, 1/5, 1/6, 1/7, 1/8, 1/9, 1/99

**Zeitblock 3:**
- 10x: 14:58:16 - 16:55:02 (117 Min)
- Positionen: 1/1, 1/2, 1/3, 1/4, 1/5, 1/6, 1/7, 1/8, 1/9, 1/99

### Deduplizierte Stempelungen (3x)

1. 08:00:51 - 08:55:22: 55 Min
2. 11:30:38 - 13:12:45: 102 Min
3. 14:58:16 - 16:55:02: 117 Min

**Summe:** 273 Min (4.56 Stunden)  
**Zeit-Spanne:** 534 Min (8.90 Stunden)  
**Lücken:** 261 Min (zwischen den Stempelungen)

---

## 🔧 Wie funktioniert unsere Berechnung?

### `get_stempelzeit_locosoft()` verwendet:

1. **Deduplizierung:** `DISTINCT ON (employee_number, DATE(start_time), start_time, end_time)`
   - Reduziert 30 Stempelungen → 3 Stempelungen ✅

2. **Zeit-Spanne:** `MAX(end_time) - MIN(start_time)`
   - 08:00:51 - 16:55:02 = 534 Min (8.90 Stunden) ✅

3. **Lücken-Berechnung:** Zeit zwischen Stempelungen
   - 08:55:22 - 11:30:38 = 155 Min
   - 13:12:45 - 14:58:16 = 105 Min
   - Gesamt: 261 Min ✅

4. **Pausen:** Konfigurierte Pausenzeiten (wenn innerhalb Zeit-Spanne)

5. **Ergebnis:** Zeit-Spanne - Lücken - Pausen = **Stempelzeit**

---

## ❓ Was macht Locosoft?

**Mögliche Erklärungen für 17 Stunden:**

1. **Locosoft summiert OHNE Deduplizierung:**
   - 30 Stempelungen × durchschnittlich 90 Min = 45.33 Stunden ❌ (zu viel)

2. **Locosoft summiert MIT Deduplizierung:**
   - 3 Stempelungen = 273 Min = 4.56 Stunden ❌ (zu wenig)

3. **Locosoft verwendet Zeit-Spanne:**
   - 534 Min = 8.90 Stunden ❌ (zu wenig)

4. **Locosoft verwendet Zeit-Spanne + Lücken:**
   - 534 Min + 261 Min = 795 Min = 13.25 Stunden ❌ (immer noch zu wenig)

5. **Locosoft summiert ALLE Positionen (auch über mehrere Tage):**
   - Vielleicht gibt es Stempelungen an anderen Tagen? ✅ (zu prüfen)

---

## 🔍 Nächste Schritte

1. **Prüfe alle Aufträge von Tobias am 13.01.2026:**
   - Gibt es mehrere Aufträge, die zusammen 17 Stunden ergeben?
   - Oder gibt es Stempelungen an anderen Tagen für Auftrag 220521?

2. **Prüfe Locosoft-UI:**
   - Wie zeigt Locosoft die 17 Stunden an?
   - Welche Berechnung verwendet Locosoft genau?

3. **Prüfe andere Aufträge:**
   - Gibt es ähnliche Muster bei anderen Aufträgen?
   - Ist das ein systematisches Problem?

---

## 📝 Erkenntnisse

1. **Duplikate sind das Hauptproblem:**
   - Locosoft erstellt für jede Position eine separate Zeile in `times`
   - Gleiche Start-/Endzeit wird mehrfach gezählt

2. **Unsere Deduplizierung funktioniert:**
   - `DISTINCT ON` reduziert 30 → 3 Stempelungen ✅
   - Zeit-Spanne-Berechnung ist korrekt ✅

3. **17 Stunden sind nicht erklärbar:**
   - Weder durch Summierung noch durch Zeit-Spanne
   - Möglicherweise mehrere Aufträge oder mehrere Tage?

---

**Erstellt:** TAG 195 (16.01.2025)  
**Status:** 🔍 **Weitere Analyse erforderlich**
