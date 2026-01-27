# Analyse: Locosoft Automatismen-Einstellungen und Auswirkung auf St-Anteil

**Datum:** 2026-01-21  
**TAG:** 206  
**Zweck:** Interpretation der Locosoft Automatismen-Einstellungen und Zusammenhang mit Auftrag 39527

---

## 📋 LOCOSOFT AUTOMATISMEN-EINSTELLUNGEN

### Einstellung 1: Automatische Verschiebung von Stempelungen

**Text:**
> "Stempelungen auf die Garantiepositionen X,01 bis X,03 sowie X,99 werden IMMER automatisch auf die nächste bzw. vorherige gültige Auftragsposition verschoben."

**Zusätzliche Option (CHECKED):**
> "Dies soll auch bei anderen ungültigen Stempelungen IMMER erfolgen"

**Interpretation:**
- Stempelungen auf ungültigen Positionen (z.B. Garantiepositionen) werden **automatisch verschoben**
- Auch andere ungültige Stempelungen werden verschoben
- **Verschobene Stempelungen erscheinen möglicherweise mehrfach in der Anzeige!**

---

### Einstellung 2: Vorverteilung bei mehreren Positionen

**Text:**
> "Bei Stempelungen, die sich über mehrere Positionen erstrecken, wird die Zeit anhand der AW-Anzahlen anteilmäßig vorverteilt."

**Zusätzliche Option (CHECKED):**
> "In einer Stempelung, die KEINERLEI AW-Anzahlen oder Preiseinträge beinhaltet, soll die Anzahl der gestempelten Positionszeilen die Verteilungsbasis der Vorverteilung sein."

**Interpretation:**
- Wenn eine Stempelung **mehrere Positionen** umfasst, wird die Zeit **anteilmäßig** aufgeteilt
- **Verteilungsbasis:** AW-Anzahlen (wenn vorhanden) oder Anzahl der Positionszeilen
- **Diese Vorverteilungen sind die Berechnungsgrundlage weitergehender Auswertungen!**

---

## 🔍 ZUSAMMENHANG MIT AUFTRAG 39527

### Problem: Mehrfachanzeige in Locosoft

**Locosoft UI zeigt:**
- Position 1,06: **5× angezeigt** (5 identische Zeilen)
- Stemp.AW: 45,00 (5× 9,00?)
- Realzeit: 9:40 (54 Min)

**DB-Daten:**
- `times`: 4 Einträge (Lines 4, 5, 6, 7)
- `labours`: 1 Eintrag mit AW (Line 6, 4.00 AW)

**Verschobene Positionen (aus Screenshot):**
- Position 1,04: "verschoben --> Po.1,06"
- Position 1,05: "verschoben --> Po.1,06"
- Position 1,07: "verschoben --> Po.1,06"

---

## 💡 ERKLÄRUNG DURCH AUTOMATISMEN

### Hypothese: Automatische Verschiebung + Vorverteilung

**Schritt 1: Automatische Verschiebung**
- Positionen 1,04, 1,05, 1,07 wurden als "ungültig" erkannt
- Locosoft hat sie **automatisch auf Position 1,06 verschoben**
- **Ergebnis:** 3 verschobene Positionen + 1 Original = 4 Positionen

**Schritt 2: Vorverteilung**
- Die Stempelzeit (54 Min) wurde auf **alle Positionen** aufgeteilt
- **Verteilungsbasis:** Anzahl der Positionszeilen (4 in DB, aber 5 in Locosoft?)
- **Ergebnis:** Jede Position bekommt einen Anteil der Zeit

**Schritt 3: Mehrfachanzeige**
- Locosoft zeigt **alle verschobenen Positionen** unter Position 1,06
- **Original (Line 6) + verschobene (Lines 4, 5, 7) = 4 Einträge**
- **Aber:** Locosoft zeigt 5 Einträge! Woher kommt der 5.?

---

## ❓ MÖGLICHE URSACHEN FÜR 5. EINTRAG

### Option 1: Doppelte Verschiebung

**Mögliche Logik:**
- Position 1,04 wurde verschoben → erscheint als 1,06
- Position 1,05 wurde verschoben → erscheint als 1,06
- Position 1,07 wurde verschoben → erscheint als 1,06
- **Original 1,06 (Line 6)**
- **Zusätzlich:** Eine weitere Position wurde verschoben?

**Problem:** DB zeigt nur 4 Einträge

### Option 2: Vorverteilung erstellt zusätzlichen Eintrag

**Mögliche Logik:**
- Locosoft erstellt bei der Vorverteilung einen **zusätzlichen Eintrag**
- Dieser Eintrag existiert nur in Locosoft, nicht in DB
- **Ergebnis:** 4 DB-Einträge + 1 Vorverteilungs-Eintrag = 5 Einträge

### Option 3: Falsche Konfiguration

**Mögliche Logik:**
- Einstellung "Dies soll auch bei anderen ungültigen Stempelungen IMMER erfolgen" ist **zu aggressiv**
- Locosoft verschiebt Positionen, die nicht verschoben werden sollten
- **Ergebnis:** Mehrfachanzeige und falsche Berechnung

---

## 🎯 VERDACHT: FALSCH KONFIGURIERTE AUTOMATISCHE VERTEILUNG

### Problem 1: Zu aggressive Verschiebung

**Einstellung:**
> "Dies soll auch bei anderen ungültigen Stempelungen IMMER erfolgen" - **CHECKED**

**Auswirkung:**
- Locosoft verschiebt möglicherweise **zu viele** Positionen
- Positionen, die nicht verschoben werden sollten, werden verschoben
- **Ergebnis:** Mehrfachanzeige und falsche St-Anteil-Berechnung

### Problem 2: Vorverteilung basiert auf falscher Anzahl

**Einstellung:**
> "In einer Stempelung, die KEINERLEI AW-Anzahlen oder Preiseinträge beinhaltet, soll die Anzahl der gestempelten Positionszeilen die Verteilungsbasis der Vorverteilung sein." - **CHECKED**

**Auswirkung:**
- Wenn Positionen verschoben werden, zählt Locosoft möglicherweise **falsche Anzahl**
- **5 Einträge** statt 4 → St-Anteil wird falsch berechnet
- **Ergebnis:** St-Anteil = 5× Dauer statt 4× Dauer

### Problem 3: Vorverteilung wird in St-Anteil übernommen

**Einstellung:**
> "Diese Vorverteilungen sind die Berechnungsgrundlage weitergehender Auswertungen."

**Auswirkung:**
- Die **vorverteilten** Zeiten werden in St-Anteil übernommen
- Auch wenn sie nicht in DB sind
- **Ergebnis:** St-Anteil ist höher als tatsächliche Stempelzeit

---

## 🔧 LÖSUNGSANSATZ

### Option 1: Einstellungen anpassen

**Empfehlung:**
1. **"Dies soll auch bei anderen ungültigen Stempelungen IMMER erfolgen"** → **UNCHECKED**
   - Nur Garantiepositionen werden automatisch verschoben
   - Andere ungültige Stempelungen müssen manuell korrigiert werden

2. **Vorverteilung prüfen:**
   - Sollte nur auf tatsächliche Positionen basieren
   - Nicht auf verschobene Positionen

### Option 2: Manuelle Korrektur (wie bei 39527)

**Vorgehen:**
- Aufträge manuell korrigieren
- Verschobene Positionen zurückverschieben
- St-Anteil manuell anpassen

**Problem:**
- Sehr aufwändig
- Muss für jeden Auftrag gemacht werden

### Option 3: DB-basierte Berechnung (DRIVE)

**Vorgehen:**
- Verwende nur DB-Daten (4 Einträge)
- Ignoriere Locosoft-Vorverteilungen
- **Ergebnis:** Korrekte St-Anteil-Berechnung

**Problem:**
- Abweichung zu Locosoft UI/CSV
- Aber: Möglicherweise korrekter!

---

## 📊 AUSWIRKUNG AUF ST-ANTEIL BERECHNUNG

### Aktuelle Situation (falsch konfiguriert)

**Auftrag 39527:**
- DB: 4 Einträge (54 Min)
- Locosoft: 5 Einträge (270 Min = 5× 54 Min)
- **St-Anteil:** 4:30 Std (falsch, sollte 3:36 Std sein)

**Berechnung:**
- St-Anteil = Dauer × Anzahl Einträge in Locosoft
- 54 Min × 5 = 270 Min = 4:30 Std ❌

### Korrekte Berechnung (DB-basiert)

**Auftrag 39527:**
- DB: 4 Einträge (54 Min)
- **St-Anteil:** 3:36 Std (4× 54 Min = 216 Min) ✅

**Berechnung:**
- St-Anteil = Dauer × Anzahl Einträge in DB
- 54 Min × 4 = 216 Min = 3:36 Std ✅

---

## 🎯 EMPFEHLUNG

### 1. Locosoft-Einstellungen prüfen

**Fragen:**
- Soll "Dies soll auch bei anderen ungültigen Stempelungen IMMER erfolgen" aktiviert sein?
- Wie wird die Vorverteilung bei verschobenen Positionen berechnet?
- Warum zeigt Locosoft 5 Einträge statt 4?

### 2. Für DRIVE-Berechnung

**Empfehlung:**
- Verwende **DB-Daten** (4 Einträge)
- Ignoriere Locosoft-Vorverteilungen
- **Ergebnis:** Korrekte St-Anteil-Berechnung

**Begründung:**
- DB-Daten sind die "Source of Truth"
- Locosoft-Vorverteilungen sind möglicherweise falsch konfiguriert
- Manuelle Korrekturen (wie bei 39527) zeigen, dass DB-Daten korrekt sind

### 3. Dokumentation

**Empfehlung:**
- Dokumentiere die Locosoft-Einstellungen
- Dokumentiere die Auswirkung auf St-Anteil-Berechnung
- Dokumentiere manuelle Korrekturen

---

**Status:** ✅ Analyse abgeschlossen  
**Erkenntnis:** Automatische Verschiebung + Vorverteilung führt zu falscher St-Anteil-Berechnung!
