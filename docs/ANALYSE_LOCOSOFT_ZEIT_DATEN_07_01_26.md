# Analyse: Locosoft Zeit-Daten 07.01.26

**Datum:** 2026-01-21  
**TAG:** 206  
**Zweck:** Analyse der vorhandenen Locosoft-Daten vor Implementierung

---

## 📋 DATEI-STRUKTUR

### Datei
- **Pfad:** `/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/locosoft_zeit/Stempelzeiten-Übersicht 07.01.26.csv`
- **Format:** CSV mit Tabs als Separator
- **Encoding:** latin-1
- **Header:** Zeile 4 (0-basiert)

### Struktur

**Header-Zeile (Zeile 4):**
```
MA | Name | von | bis | (leer) | Dauer | Auftrag | Pos. Art Text | AuAW | AW-Ant. | St-Ant. | %Lstgrad | Anwes. | Produkt. | Pause
```

**Daten-Zeilen:**
- **Zeile 0 (MA-Info):**
  - Spalte 0: MA-Nummer (5007)
  - Spalte 1: Name (Reitmeier,Tobias)
  - Spalte 2: von (07:58)
  - Spalte 3: bis (> KOMMT)

- **Zeile 1+ (Stempelungen):**
  - **ACHTUNG:** Spalten sind verschoben!
  - Spalte 2 ("Name"): enthält "von"-Zeit
  - Spalte 3 ("von"): enthält "bis"-Zeit
  - Spalte 5 ("Unnamed: 5"): enthält "Dauer"
  - Spalte 6 ("Dauer"): enthält **Auftragsnummer**!
  - Spalte 7 ("Auftrag"): enthält Position-Info (z.B. "1,06 G  EINGRIFF...")
  - Spalte 10 ("AW-Ant."): enthält St-Anteil (in Stunden:Minuten)
  - Spalte 11 ("St-Ant."): enthält Leistungsgrad (in %)
  - Spalte 13 ("Anwes."): enthält Anwesenheit

---

## 🔍 ROHDATEN (MA 5007, 07.01.2026)

### Stempelungen aus CSV

| Zeile | von | bis | Dauer | Auftrag | St-Ant. (AW-Ant.) | AW-Ant. (AuAW) | Anwes. |
|-------|-----|-----|-------|---------|-------------------|----------------|--------|
| 1 | 08:46 | 09:40 | 0:54 | 39527 | 4:30 | 0:24 | 0:59 |
| 2 | 09:40 | 09:59 | 0:19 | 219184 | 0:19 | 0:42 | 1:18 |
| 3 | 09:59 | 10:47 | 0:47 | 220445 | 0:47 | 0:27 | 2:05 |
| 4 | 10:47 | 11:03 | 0:17 | 220067 | 0:10 | 0:18 | - |
| 5 | -""- | F | - | 220067 | 0:07 | 0:12 | 2:22 |
| 6 | 11:04 | 11:10 | 0:07 | 39809 | 0:25 | 0:11 | 2:29 |
| 7 | -""- | F | - | 39809 | 0:02 | 0:04 | 2:29 |
| 8 | 11:11 | 11:37 | 0:27 | 39524 | 2:15 | 0:24 | 2:56 |
| 9 | 11:37 | 11:44 | 0:07 | 220624 | -- | -- | - |

**⚠️ WICHTIG:** 
- Spalte "St-Ant." enthält **Leistungsgrad in %**, nicht Stempelzeit!
- Spalte "AW-Ant." enthält **Stempelzeit in Stunden:Minuten**!
- Spalte "AuAW" enthält **AW-Anteil**!

### Korrekte Zuordnung

| CSV-Spalte | Tatsächlicher Inhalt |
|------------|---------------------|
| "AW-Ant." | **St-Anteil (Stempelzeit)** in Stunden:Minuten |
| "St-Ant." | **Leistungsgrad** in % |
| "AuAW" | **AW-Anteil** in Stunden:Minuten |
| "Dauer" | **Auftragsnummer** |
| "Auftrag" | **Position-Info** (z.B. "1,06 G  EINGRIFF...") |

---

## 📊 BERECHNUNG AUS CSV-DATEN

### St-Anteil (aus Spalte "AW-Ant.")

**Summe aller St-Anteil-Werte:**
- 4:30 + 0:19 + 0:47 + 0:10 + 0:07 + 0:25 + 0:02 + 2:15 + (-- = 0)
- = 4.5 + 0.32 + 0.78 + 0.17 + 0.12 + 0.42 + 0.03 + 2.25
- = **8.59 Std** ≈ **8:35 Std**

**⚠️ ABER:** Locosoft zeigt 13:05 Std!

### Vergleich

| Quelle | St-Anteil |
|--------|-----------|
| **Locosoft (Screenshot)** | 13:05 Std |
| **CSV (Summe AW-Ant.)** | 8:35 Std |
| **Unsere DB-Berechnung** | 8:04 Std |
| **Abweichung CSV vs. Locosoft** | -4:30 Std |

---

## ❓ FRAGEN

1. **Warum weicht CSV von Locosoft ab?**
   - CSV zeigt 8:35 Std, Locosoft zeigt 13:05 Std
   - Abweichung: -4:30 Std (35% zu niedrig)

2. **Was fehlt in der CSV?**
   - Möglicherweise fehlen Positionen?
   - Möglicherweise andere Filter?

3. **Ist die CSV vollständig?**
   - CSV zeigt nur 9 Stempelungen
   - Unsere DB-Analyse zeigt 50 Einträge (type=2)

4. **Welche Daten sind korrekt?**
   - CSV: Export aus Locosoft?
   - DB: Direkt aus PostgreSQL?
   - Screenshot: UI-Anzeige?

---

## 🎯 NÄCHSTE SCHRITTE

1. **Prüfe weitere CSV-Dateien**
   - Andere Tage
   - Andere Mechaniker
   - Vergleich mit DB-Daten

2. **Prüfe Excel-Dateien**
   - Möglicherweise vollständigere Daten
   - Andere Struktur?

3. **Vergleiche CSV mit DB**
   - Gleiche Stempelungen?
   - Gleiche Werte?
   - Unterschiede?

---

**Status:** ⏳ Analyse in Bearbeitung  
**Nächste Aktion:** Prüfe weitere Dateien und vergleiche mit DB-Daten
