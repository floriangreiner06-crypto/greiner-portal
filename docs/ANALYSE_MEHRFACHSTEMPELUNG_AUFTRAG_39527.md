# Analyse: Mehrfachstempelung Auftrag 39527 - Locosoft Screenshot

**Datum:** 2026-01-21  
**TAG:** 206  
**Zweck:** Analyse der Mehrfachstempelung in Locosoft UI vs. DB-Daten

---

## 📊 LOCOSOFT SCREENSHOT ANALYSE

### Position 1,06 - 5× angezeigt!

**Locosoft UI zeigt:**
- **Position 1,06** wird **5× angezeigt** (5 identische Zeilen)
- Alle 5 Einträge zeigen:
  - **Auftr.AW:** 4,00
  - **Stemp.AW:** 45,00 (5× 9,00?)
  - **Abw. AW:** +41,00 (mit rotem Ausrufezeichen ⚠️)
  - **MA-Nr.:** 5007
  - **gestempelte:** 07.01.26 8:46
  - **Realzeit:** 9:40
  - **Zeitbasis:** 9,00
  - **%:** 100,00

**Andere Positionen:**
- Position 1,04: "verschoben --> Po.1,06"
- Position 1,05: "verschoben --> Po.1,06"
- Position 1,07: "verschoben --> Po.1,06"

**SUM-Zeile:**
- Auftr.AW: 4,00
- Stemp.AW: 45,00
- Abw. AW: +41,00

---

## 🔍 DB-DATEN ANALYSE

### times-Tabelle (4 Einträge)

| Position | Line | Start | End | Dauer |
|----------|------|-------|-----|-------|
| 1 | 4 | 08:46:42 | 09:40:33 | 53.85 Min |
| 1 | 5 | 08:46:42 | 09:40:33 | 53.85 Min |
| 1 | 6 | 08:46:42 | 09:40:33 | 53.85 Min |
| 1 | 7 | 08:46:42 | 09:40:33 | 53.85 Min |

**Ergebnis:**
- **4 Einträge** in DB (Lines 4, 5, 6, 7)
- Alle zur **gleichen Zeit** (08:46:42 - 09:40:33)
- **Dauer:** 53.85 Min pro Eintrag

### labours-Tabelle (1 Eintrag)

| Position | Line | AW-Einheiten | AW-Stunden |
|----------|------|--------------|------------|
| 1 | 6 | 4.00 | 0.40 Std |

**Ergebnis:**
- Nur **1 Eintrag** in labours (Line 6)
- **AW-Einheiten:** 4.00 (0.40 Std)

---

## ❓ DISKREPANZEN

### 1. Anzahl Einträge

| Quelle | Anzahl Einträge |
|--------|----------------|
| **Locosoft UI** | 5 Einträge (Position 1,06) |
| **DB times** | 4 Einträge (Lines 4, 5, 6, 7) |
| **DB labours** | 1 Eintrag (Line 6) |

**Frage:** Woher kommt der 5. Eintrag in Locosoft?

### 2. Stemp.AW Berechnung

**Locosoft zeigt:**
- Stemp.AW: **45,00** (5× 9,00?)
- Realzeit: 9:40 (54 Min = 0.90 Std)
- Zeitbasis: 9,00

**Berechnung:**
- 45,00 / 5 = **9,00** pro Eintrag
- 9,00 × 6 Min/Einheit = **54 Min** ✅ (passt zu Realzeit!)

**Aber:**
- DB zeigt nur 4 Einträge
- Woher kommt der 5. Eintrag?

### 3. AW-Abweichung

**Locosoft zeigt:**
- Auftr.AW: 4,00
- Stemp.AW: 45,00
- **Abw. AW: +41,00** (mit rotem Ausrufezeichen ⚠️)

**Berechnung:**
- 45,00 - 4,00 = **+41,00** ✅ (passt!)

**Problem:**
- Warum zeigt Locosoft 45,00 statt 4,00?
- Ist das ein Fehler in Locosoft?

---

## 💡 MÖGLICHE ERKLÄRUNGEN

### Hypothese 1: Locosoft zeigt alle Positionen, auch verschobene

**Mögliche Logik:**
- Position 1,04, 1,05, 1,07 wurden "verschoben --> Po.1,06"
- Locosoft zeigt diese als separate Einträge unter Position 1,06
- **5 Einträge = 1 Original (Line 6) + 4 verschobene (Lines 4, 5, 7 + ?)**

**Problem:**
- DB zeigt nur 4 Einträge (Lines 4, 5, 6, 7)
- Woher kommt der 5. Eintrag?

### Hypothese 2: Locosoft-Bug - Mehrfachanzeige

**Mögliche Logik:**
- Locosoft zeigt die gleiche Stempelung mehrfach (Bug?)
- Oder Locosoft zählt verschobene Positionen doppelt

**Problem:**
- Warum zeigt Locosoft 5× statt 4×?
- Ist das ein Fehler in Locosoft?

### Hypothese 3: 5. Eintrag existiert, aber nicht in times-Tabelle

**Mögliche Logik:**
- Es gibt eine 5. Position, die nicht in `times`-Tabelle ist
- Oder die 5. Position wurde gelöscht/geändert
- Locosoft zeigt historische Daten

**Problem:**
- Warum ist die 5. Position nicht in DB?

---

## 🎯 EINSCHÄTZUNG

### Ist das ein Fehler in Locosoft?

**JA, wahrscheinlich!**

**Gründe:**
1. **DB zeigt nur 4 Einträge**, Locosoft zeigt 5
2. **Stemp.AW: 45,00** ist viel zu hoch (sollte 4,00 sein?)
3. **Abw. AW: +41,00** mit rotem Ausrufezeichen ⚠️ deutet auf Problem hin
4. **Mehrfachanzeige** der gleichen Stempelung

**Mögliche Ursachen:**
- Locosoft zeigt verschobene Positionen mehrfach
- Locosoft zählt verschobene Positionen doppelt
- Locosoft-Bug bei der Anzeige von verschobenen Positionen

### Auswirkung auf St-Anteil Berechnung

**CSV zeigt:**
- St-Anteil für Auftrag 39527: **4:30 Std (270 Min)**

**Berechnung:**
- 270 Min / 54 Min = **5.0** → **5× die Dauer!**
- Passt zu **5 Einträgen** in Locosoft UI!

**Erkenntnis:**
- Locosoft summiert St-Anteil für **alle 5 Einträge**
- Auch wenn nur 4 in DB sind
- **St-Anteil = Dauer × Anzahl Einträge in Locosoft UI**

---

## 🔧 LÖSUNGSANSATZ

### Option 1: Position-basierte Berechnung (wie Locosoft)

**Methode:**
- Summiere St-Anteil für **alle Positionen** (nicht dedupliziert)
- Wie Locosoft UI zeigt

**Problem:**
- Wenn Locosoft-Bug → unsere Berechnung auch falsch
- Aber: CSV-Daten stimmen mit Locosoft UI überein

### Option 2: DB-basierte Berechnung (korrigiert)

**Methode:**
- Summiere St-Anteil nur für **tatsächliche DB-Einträge**
- Ignoriere Locosoft-Bug

**Problem:**
- Abweichung zu Locosoft UI/CSV
- Aber: Möglicherweise korrekter?

### Option 3: Hybrid-Ansatz

**Methode:**
- Verwende DB-Daten
- Aber: Berücksichtige verschobene Positionen
- Summiere alle Positionen, die zu Position 1,06 gehören

**Problem:**
- Wie erkenne ich verschobene Positionen?

---

## 📋 NÄCHSTE SCHRITTE

### 1. Prüfe weitere Aufträge

**Fragen:**
- Gibt es ähnliche Mehrfachanzeigen bei anderen Aufträgen?
- Gibt es konsistente Muster?

### 2. Prüfe verschobene Positionen

**Fragen:**
- Wie werden verschobene Positionen in DB gespeichert?
- Gibt es eine Tabelle für verschobene Positionen?

### 3. Kontaktiere Locosoft Support

**Fragen:**
- Warum zeigt Locosoft 5 Einträge statt 4?
- Ist das ein Bug oder gewollt?
- Wie sollte St-Anteil berechnet werden?

---

**Status:** ✅ Analyse abgeschlossen  
**Erkenntnis:** Locosoft zeigt möglicherweise **Mehrfachanzeige (Bug?)**, die St-Anteil Berechnung beeinflusst!
