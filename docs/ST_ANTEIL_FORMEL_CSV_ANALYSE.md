# St-Anteil Formel - CSV-Analyse

**Datum:** 2026-01-XX  
**Status:** ✅ **Formel identifiziert**

---

## 📊 CSV-Analyse Ergebnisse

### Datei analysiert
- `Stempelzeiten-Übersicht 01.10.25 - 08.01.26.csv`
- 3939 Stempelungen mit vollständigen Daten

### Erkenntnisse

1. **St-Anteil wird in Prozent angegeben**
   - Formel: `St-Anteil % = (St-Anteil in Min / Dauer) × 100`
   - Umgekehrt: `St-Anteil in Min = Dauer × (St-Ant. % / 100)`

2. **Beste Formel für St-Anteil in Min:**
   ```
   St-Anteil = Dauer × (AuAW / AW-Ant.)
   ```
   - Passt bei **57% der Fälle exakt** (Diff < 0.1 Min)
   - Passt bei **57.5% der Fälle nahe** (Diff < 1.0 Min)

3. **Alternative Formeln (schlechter):**
   - H2 (AuAW direkt): 17%
   - H4 (AW-Ant. × AuAW / Dauer): 17%
   - H7 (AW-Ant. direkt): 3%

### CSV-Spalten-Struktur

Die CSV-Spalten sind verschoben:
- Spalte 5 (`dauer_min_str`): Dauer in Minuten (z.B. "0:32")
- Spalte 6 (`auftrag_nummer`): Auftrag (z.B. "312553")
- Spalte 7 (`position_text`): Position (z.B. "1,02 W  Vorführung...")
- Spalte 8 (`auaw1`): AuAW in Minuten (z.B. "0:24")
- Spalte 10 (`aw_ant_min_str`): AW-Anteil in Minuten (z.B. "0:32")
- Spalte 11 (`st_ant_pct_str`): St-Anteil in Prozent (z.B. "75,0%")

### Beispiele aus CSV

**Beispiel 1:**
- Dauer: 32 Min
- AuAW: 24 Min
- AW-Ant.: 32 Min
- St-Ant. %: 75.0%
- St-Anteil (aus %): 24.0 Min
- H3 (Dauer × AuAW / AW-Ant.): 24.0 Min ✅

**Beispiel 2:**
- Dauer: 114 Min
- AuAW: 80 Min
- AW-Ant.: 47 Min
- St-Ant. %: 170.2%
- St-Anteil (aus %): 194.0 Min
- H3 (Dauer × AuAW / AW-Ant.): 194.0 Min ✅

---

## 🔧 Implementierung in DRIVE

### Aktuelle Logik (zu ändern)

Aktuell verwendet `get_st_anteil_position_basiert()`:
```
St-Anteil = Realzeit × (AuAW_Position / Summe_AuAW_Auftrag)
```

### Neue Logik (basierend auf CSV)

```
St-Anteil = Dauer × (AuAW / AW-Ant.)
```

**Problem:** AW-Ant. muss pro Position berechnet werden, nicht pro Mechaniker!

**Lösung:**
1. Berechne AW-Ant. pro Position (basierend auf Stempelzeit-Verteilung)
2. Dann: St-Anteil = Dauer × (AuAW / AW-Ant.)

---

## ⚠️ Offene Fragen

1. Wie wird AW-Ant. pro Position berechnet?
   - Ist es: `AW-Ant. = Dauer × (AuAW / Summe_AuAW_Auftrag)`?
   - Oder: `AW-Ant. = Stempelzeit, die dieser Position zugeordnet wird`?

2. Warum passt die Formel nur bei 57% der Fälle?
   - Gibt es Sonderfälle?
   - Gibt es eine komplexere Logik?

3. Wie werden mehrere Mechaniker auf eine Position behandelt?
   - Wird AW-Ant. dann anders berechnet?

---

## 📝 Nächste Schritte

1. ✅ CSV-Analyse abgeschlossen
2. ⏳ AW-Ant. pro Position berechnen
3. ⏳ St-Anteil-Berechnung in DRIVE anpassen
4. ⏳ Testen mit echten Daten (z.B. Mechaniker 5007)
