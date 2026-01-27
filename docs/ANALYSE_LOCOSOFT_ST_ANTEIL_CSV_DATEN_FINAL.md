# Analyse: Locosoft St-Anteil Berechnung aus CSV-Daten

**Datum:** 2026-01-21  
**TAG:** 206  
**Zweck:** Verstehen, wie Locosoft St-Anteil berechnet (basierend auf CSV-Daten)

---

## 📊 VERGLEICH: LOCOSOFT CSV vs. DRIVE

### Locosoft (CSV - direkt aus Locosoft exportiert) ✅

| Betrieb | St-Anteil | Status |
|---------|-----------|--------|
| **DEGO** | 9.10 Std (9:06) | ✅ **KORREKT** |
| **DEGH** | 3.98 Std (3:59) | ✅ **KORREKT** |
| **GESAMT** | 13.08 Std (13:05) | ✅ **KORREKT** |

### DRIVE - Verschiedene Berechnungsmethoden

| Methode | DEGO | DEGH | GESAMT | Abweichung | Status |
|---------|------|------|--------|------------|--------|
| **Position-basiert (OHNE Deduplizierung)** | 13.52 Std | 24.52 Std | 38.04 Std | +24.96 Std (+191%) | ❌ Viel zu hoch |
| **Auftrags-basiert (MIT Deduplizierung)** | 3.21 Std | 4.43 Std | 8.04 Std | -5.04 Std (-38.5%) | ❌ Viel zu niedrig |
| **Zeit-Spanne** | 8.05 Std | 5.17 Std | - | - | ❌ DEGO nah, DEGH falsch |

**Erkenntnis:** **KEINE unserer Methoden passt perfekt zu Locosoft!**

---

## 🔍 DETAILANALYSE: CSV-DATEN

### Stempelungen aus CSV (MA 5007, 07.01.2026)

**Wichtig:** CSV-Spalten sind verschoben!
- Spalte "AW-Ant." enthält **St-Anteil** (nicht AW-Anteil!)
- Spalte "AuAW" enthält **AW-Anteil**
- Spalte "St-Ant." enthält **Leistungsgrad in %**

### Beispiel: Auftrag 39527 (DEGO)

**CSV-Daten:**
- Dauer: 0:54 Std (54 Min)
- St-Anteil: 4:30 Std (270 Min) - **5× höher als Dauer!**
- AW-Anteil: 0:24 Std (24 Min)

**DB-Daten:**
- 4 Positionen zur gleichen Zeit (08:46-09:40)
- Dauer: 53.85 Min pro Position
- AW-Einheiten: 4.00 (nur 1 Position in labours)

**Berechnung:**
- 270 Min / 54 Min = **5.0**
- Möglicherweise 5 Positionen? Oder andere Logik?

### Beispiel: Auftrag 220542 (DEGH)

**CSV-Daten:**
- 5 Positionen in CSV
- St-Anteil gesamt: 2:29 Std (149 Min)
- Dauer: 2:29 Std (149 Min) - **Gleich!**

**Erkenntnis:**
- Bei Auftrag 220542: St-Anteil = Dauer ✅
- Bei Auftrag 39527: St-Anteil ≠ Dauer (5× höher) ❌

---

## 💡 MÖGLICHE LOCOSOFT-LOGIKEN

### Hypothese 1: St-Anteil = Dauer × Anzahl Positionen mit AW

**Beispiel Auftrag 39527:**
- Dauer: 54 Min
- Positionen mit AW: 5? (nicht 4 wie in DB)
- St-Anteil: 270 Min = 54 Min × 5

**Problem:** Passt nicht immer (z.B. Auftrag 220542)

### Hypothese 2: St-Anteil = Dauer × (AW-Gesamt / Dauer) × Faktor

**Beispiel Auftrag 39527:**
- Dauer: 54 Min
- AW-Anteil: 24 Min
- St-Anteil: 270 Min
- **270 / 54 = 5.0** → Möglicherweise 5 Positionen?

**Problem:** Wie wird der Faktor berechnet?

### Hypothese 3: St-Anteil wird nach AW-Anteil pro Position aufgeteilt

**Mögliche Logik:**
- Gesamte Stempelzeit wird nach AW-Anteil aufgeteilt
- Position mit mehr AW bekommt mehr St-Anteil
- **St-Anteil pro Position = Dauer × (AW-Position / AW-Gesamt)**

**Prüfung nötig:** Vergleich AW-Anteil vs. St-Anteil in CSV

### Hypothese 4: St-Anteil = Summe der St-Anteil pro Position (aus labours)

**Mögliche Logik:**
- St-Anteil wird aus `labours`-Tabelle berechnet
- Pro Position mit AW-Anteil
- Summe aller Positionen = Gesamt St-Anteil

**Prüfung nötig:**
- Gibt es St-Anteil-Werte in `labours`?
- Oder wird St-Anteil aus `times` × AW-Verhältnis berechnet?

---

## 🔍 WEITERE ANALYSEN NÖTIG

### 1. Prüfe alle CSV-Dateien

**Dateien:**
- `Stempelzeiten-Übersicht 01.01.26 - 15.01.26.csv`
- `Stempelzeiten-Übersicht 01.01.26 - 18.01.26.csv`
- `Stempelzeiten-Übersicht 01.10.25 - 08.01.26.csv`
- `Stempelzeiten-Übersicht 01.12.25 - 15.01.26.csv`

**Fragen:**
- Gibt es Muster über verschiedene Zeiträume?
- Gibt es konsistente Berechnungslogik?
- Gibt es Unterschiede zwischen verschiedenen Tagen?

### 2. Prüfe andere Mechaniker

**Fragen:**
- Gibt es ähnliche Muster bei anderen Mechanikern?
- Gibt es konsistente Berechnungslogik?
- Gibt es Unterschiede zwischen verschiedenen Mechanikern?

### 3. Prüfe labours-Tabelle

**Fragen:**
- Gibt es St-Anteil-Werte in `labours`?
- Oder wird St-Anteil aus `times` berechnet?
- Wie wird St-Anteil pro Position zugeordnet?

---

## 🎯 NÄCHSTE SCHRITTE

### 1. Analysiere weitere CSV-Dateien

**Ziel:** Muster erkennen über verschiedene Zeiträume

### 2. Prüfe labours-Tabelle

**Ziel:** Verstehen, wie St-Anteil pro Position berechnet wird

### 3. Teste verschiedene Berechnungsmethoden

**Ziel:** Finde Methode, die zu CSV-Daten passt

---

**Status:** ✅ Analyse abgeschlossen  
**Erkenntnis:** Locosoft verwendet komplexe Berechnungslogik - **weitere Analysen nötig!**
