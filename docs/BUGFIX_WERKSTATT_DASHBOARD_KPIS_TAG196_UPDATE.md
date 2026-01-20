# BUGFIX UPDATE: Werkstatt-Dashboard KPIs (TAG 196)

**Datum:** 2026-01-18  
**Status:** ⚠️ **TEILWEISE BEHOBEN - Weitere Analyse erforderlich**

---

## ✅ Behobene Probleme

### 1. Gesamt-Leistungsgrad: Falscher Faktor
- **Fix:** `* 60` → `* 6.0` (korrekt: 1 AW = 6 Minuten)
- **Status:** ✅ **BEHOBEN**

### 2. Gesamt-Leistungsgrad: Falsche Datenquelle
- **Fix:** `stempelzeit_leistungsgrad` → `stempelzeit` (Stmp.Anteil)
- **Status:** ✅ **BEHOBEN**

### 3. Validierung für physikalische Unmöglichkeit
- **Fix:** Warnung wenn `stempelzeit > anwesenheit`, Cap auf 100%
- **Status:** ✅ **BEHOBEN**

---

## ⚠️ Verbleibende Probleme

### Problem #1: Stempelzeit > Anwesenheit bei einzelnen Mechanikern

**Beobachtung:**
```
MA 5018: St=21255 Min, Anw=5207 Min, Ratio=408.2% ❌
MA 5007: St=14926 Min, Anw=4365 Min, Ratio=342.0% ❌
MA 5014: St=14894 Min, Anw=2707 Min, Ratio=550.2% ❌
```

**Ursache:**
- Anwesenheitsdaten (`type=1`) fehlen oder sind unvollständig
- `get_anwesenheit_rohdaten()` findet keine oder zu wenige `type=1` Einträge

**Lösung:**
- Prüfe, ob `type=1` Daten in Locosoft vorhanden sind
- Prüfe, ob Filter in `get_anwesenheit_rohdaten()` zu restriktiv sind

---

### Problem #2: Dashboard zeigt falsche Anwesenheit

**Beobachtung:**
- Gesamt-Anwesenheit (Test): **3.244,4 Std** ✅
- Dashboard zeigt: **626,4 Std** ❌
- Faktor: ~5,2

**Mögliche Ursachen:**
1. Anwesenheit wird durch Anzahl Mechaniker geteilt (falsch!)
2. Anwesenheit wird aus anderen Datenquellen berechnet
3. Filter-Problem (nur bestimmte Mechaniker werden berücksichtigt)

**Nächste Schritte:**
- Prüfe, welche Datenquelle das Dashboard verwendet
- Prüfe, ob Filter auf Mechaniker angewendet werden

---

### Problem #3: `get_st_anteil_position_basiert()` verwendet 75% Faktor

**Aktuell:**
```sql
-- St-Anteil = 75 Prozent der Gesamt-Dauer
ROUND(SUM(dauer_minuten)::numeric * 0.75, 0) AS stempelanteil_minuten
```

**Sollte sein (laut TAG 195):**
1. Mittagspause (12:00-12:44) abziehen
2. Stempelzeit (Min) / 6 = AW ("Zeitbasis")
3. Summiere alle AW-Werte pro Mechaniker = "Stemp. AW, anteilig"
4. Rückgabe in Minuten (AW × 6)

**Status:** ⚠️ **NICHT IMPLEMENTIERT** - Funktion verwendet noch 75% Faktor statt echte Locosoft-Logik

---

## 📊 Test-Ergebnisse

### Gesamt-Werte (01.01-18.01.26):
```
Gesamt Stempelzeit (Stmp.Anteil): 126.798 Min = 2.113,3 Std ✅
Gesamt Anwesenheit: 194.663,6 Min = 3.244,4 Std ✅
Verhältnis: 65.1% (sollte ≤ 100% sein) ✅
```

**Status:** ✅ **Gesamt-Werte sind korrekt!**

### Einzelne Mechaniker:
```
MA 5018: St=21255 Min, Anw=5207 Min, Ratio=408.2% ❌
MA 5007: St=14926 Min, Anw=4365 Min, Ratio=342.0% ❌
MA 5014: St=14894 Min, Anw=2707 Min, Ratio=550.2% ❌
```

**Status:** ⚠️ **Einzelne Mechaniker haben Problem - Anwesenheitsdaten fehlen**

---

## 🔧 Nächste Schritte

1. **Prüfe Anwesenheitsdaten:**
   - Prüfe, ob `type=1` Daten in Locosoft vorhanden sind
   - Prüfe, ob Filter in `get_anwesenheit_rohdaten()` zu restriktiv sind

2. **Prüfe Dashboard-Anzeige:**
   - Prüfe, warum Dashboard 626,4 Std statt 3.244,4 Std anzeigt
   - Prüfe, ob Filter auf Mechaniker angewendet werden

3. **Implementiere echte Locosoft-Logik:**
   - Ersetze 75% Faktor durch echte Locosoft-Logik (Mittagspause, Zeitbasis in AW)

---

**Erstellt:** TAG 196  
**Status:** ⚠️ **TEILWEISE BEHOBEN - Weitere Analyse erforderlich**
