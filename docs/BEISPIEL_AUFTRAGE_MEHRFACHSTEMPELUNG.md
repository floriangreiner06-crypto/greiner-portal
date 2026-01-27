# Beispiele: Aufträge mit Mehrfachstempelungen (analog zu 39527)

**Datum:** 2026-01-21  
**TAG:** 206  
**Zweck:** Identifikation weiterer Aufträge mit ähnlichen Mehrfachstempelungen wie 39527

---

## 📊 GEFUNDENE BEISPIELE

### Top 10 Aufträge mit meisten Mehrfachstempelungen (Januar 2026)

| Auftrag | Position | Datum | Lines | Dauer | Betrieb | MA |
|---------|----------|-------|-------|-------|---------|-----|
| **313575** | 2 | 20.01.26 | **14** | 0.78 Min | LAN (3) | 5016 |
| **39793** | 1 | 07.01.26 | **11** | 72.32 Min | DEGO (1) | 5018 |
| **220583** | 1 | 12.01.26 | **11** | 73.57 Min | DEGH (2) | 5008 |
| **313575** | 2 | 20.01.26 | **11** | 73.47 Min | LAN (3) | 5016 |
| **313575** | 2 | 21.01.26 | **11** | 258.43 Min | LAN (3) | 5016 |
| **220521** | 1 | 13.01.26 | **10** | 54.52 Min | DEGH (2) | **5007** |
| **220521** | 1 | 13.01.26 | **10** | 102.12 Min | DEGH (2) | **5007** |
| **220521** | 1 | 13.01.26 | **10** | 116.77 Min | DEGH (2) | **5007** |
| **220847** | 1 | 19.01.26 | **9** | 27.30 Min | DEGH (2) | 5007 |
| **39471** | 1 | 09.01.26 | **8** | 61.15 Min | DEGO (1) | 5007 |

**Erkenntnis:**
- **220521** hat 3× Mehrfachstempelungen (10 Lines) am gleichen Tag - **MA 5007** (wie 39527!)
- **313575** hat extrem viele Mehrfachstempelungen (14 Lines!)
- **39471** hat auch Mehrfachstempelungen - **MA 5007**

---

## 🔍 DETAILANALYSE: Auftrag 220521 (MA 5007, ähnlich 39527)

### Stempelungen am 13.01.2026

**3× Mehrfachstempelungen:**

| Zeit | Lines | Dauer | Status |
|------|-------|-------|--------|
| 08:00:51 - 08:55:22 | **10 Lines** | 54.52 Min | Mehrfachstempelung |
| 11:30:38 - 13:12:45 | **10 Lines** | 102.12 Min | Mehrfachstempelung |
| 14:58:16 - 16:55:02 | **10 Lines** | 116.77 Min | Mehrfachstempelung |

**Vergleich mit 39527:**
- **39527:** 4 Lines, 54 Min → St-Anteil: 4:30 Std (5×)
- **220521:** 10 Lines, 54 Min → St-Anteil möglicherweise: 9:00 Std (10×)?

**Erwartung:**
- Locosoft zeigt möglicherweise 10× die Dauer
- St-Anteil = 54 Min × 10 = 540 Min = 9:00 Std

---

## 🔍 DETAILANALYSE: Auftrag 313575 (extremes Beispiel)

### Stempelung am 20.01.2026, 08:16:18 - 08:17:05

**14 Lines zur gleichen Zeit!**

| Line | Dauer |
|------|-------|
| 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 99 | 0.78 Min |

**Berechnung:**
- Dauer: 0.78 Min (47 Sekunden!)
- Lines: 14
- **St-Anteil möglicherweise:** 0.78 Min × 14 = 10.92 Min

**Erwartung:**
- Locosoft zeigt möglicherweise 14× die Dauer
- St-Anteil = 0.78 Min × 14 = 10.92 Min

**Problem:**
- Sehr kurze Stempelzeit (47 Sekunden)
- Aber 14 Lines → St-Anteil wird stark überbewertet

---

## 🔍 DETAILANALYSE: Auftrag 39471 (MA 5007)

### Stempelung am 09.01.2026, 09:44:04 - 10:45:13

**8 Lines zur gleichen Zeit!**

| Lines | Dauer |
|-------|-------|
| 8 verschiedene Lines | 61.15 Min |

**Vergleich mit 39527:**
- **39527:** 4 Lines, 54 Min
- **39471:** 8 Lines, 61 Min
- **Erwartung:** St-Anteil = 61 Min × 8 = 488 Min = 8:08 Std

---

## 📊 ZUSAMMENFASSUNG

### Aufträge mit Mehrfachstempelungen (MA 5007)

| Auftrag | Datum | Lines | Dauer | Erwarteter St-Anteil |
|---------|-------|-------|-------|---------------------|
| **39527** | 07.01.26 | 4 | 54 Min | 4:30 Std (5×) |
| **220521** | 13.01.26 | 10 | 54 Min | 9:00 Std (10×) |
| **220521** | 13.01.26 | 10 | 102 Min | 17:00 Std (10×) |
| **220521** | 13.01.26 | 10 | 117 Min | 19:30 Std (10×) |
| **220847** | 19.01.26 | 9 | 27 Min | 4:03 Std (9×) |
| **39471** | 09.01.26 | 8 | 61 Min | 8:08 Std (8×) |

**Erkenntnis:**
- **220521** hat 3× Mehrfachstempelungen am gleichen Tag
- **Erwarteter St-Anteil:** 9:00 + 17:00 + 19:30 = **45:30 Std** (viel zu hoch!)
- **Tatsächliche Stempelzeit:** 54 + 102 + 117 = **273 Min = 4:33 Std**

**Abweichung:**
- Erwarteter St-Anteil: 45:30 Std
- Tatsächliche Stempelzeit: 4:33 Std
- **Faktor: 10× zu hoch!**

---

## 🎯 EMPFEHLUNG

### 1. Prüfe diese Aufträge in Locosoft UI

**Aufträge:**
- **220521** (MA 5007, 13.01.26) - 3× Mehrfachstempelungen
- **313575** (MA 5016, 20.01.26) - 14 Lines!
- **39471** (MA 5007, 09.01.26) - 8 Lines

**Fragen:**
- Zeigt Locosoft mehrfache Zeilen?
- Wie wird St-Anteil berechnet?
- Gibt es verschobene Positionen?

### 2. Prüfe CSV-Daten

**Fragen:**
- Gibt es CSV-Daten für diese Aufträge?
- Stimmt St-Anteil mit erwarteten Werten überein?
- Gibt es Abweichungen?

### 3. Dokumentiere Muster

**Fragen:**
- Gibt es konsistente Muster?
- Welche Aufträge sind betroffen?
- Wie häufig tritt das Problem auf?

---

**Status:** ✅ Analyse abgeschlossen  
**Erkenntnis:** Mehrere Aufträge mit ähnlichen Mehrfachstempelungen gefunden, besonders **220521** (MA 5007)!
