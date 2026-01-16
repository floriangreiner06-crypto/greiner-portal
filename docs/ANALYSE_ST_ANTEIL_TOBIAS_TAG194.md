# Analyse St-Anteil für Tobias (5007) - TAG 194

**Datum:** 2026-01-16  
**Mechaniker:** 5007 (Reitmeier, Tobias)  
**Zeitraum:** 01.01.26 - 16.01.26

---

## 📊 Vergleich DRIVE vs. Locosoft

| Metrik | DRIVE | Locosoft UI | Differenz | Status |
|--------|-------|-------------|-----------|--------|
| **AW-Anteil** | 3192 Min (53:12) | 3155 Min (52:35) | -37 Min (-1.2%) | ✅ Sehr gut |
| **St-Anteil** | 3360 Min (56:00) | 4971 Min (82:51) | +1611 Min (+32.4%) | ❌ Problem |
| **Leistungsgrad** | 88.5% | 63.5% | -25.0% | ❌ Problem |

---

## 🔍 Analyse St-Anteil

### Getestete Berechnungen:

1. **Position-basierte Stempelzeit (anteilig verteilt):** 3360 Min
   - Diff zu Locosoft: +1611 Min ❌

2. **Zeit-Spanne minus Lücken minus Pausen:** 3294 Min
   - Diff zu Locosoft: +1677 Min ❌

3. **Gesamte Stempelzeit (ohne Deduplizierung):** 18674 Min
   - Diff zu Locosoft: +13703 Min ❌

4. **Summe ALLER Stempelzeiten auf Positionen:** 18983 Min
   - Diff zu Locosoft: +14012 Min ❌

**Keine der Berechnungen passt zu Locosoft's 4971 Min!**

---

## 🔍 Mögliche Ursachen

1. **Locosoft verwendet eine andere Berechnungslogik:**
   - Vielleicht wird "St-Anteil" anders berechnet als "Stmp.Anteil"?
   - Vielleicht gibt es zusätzliche Filter oder Kriterien?

2. **Unterschiedliche Zeiträume:**
   - DRIVE: 01.01-16.01.26
   - Locosoft: 01.01.26-16.01.26 (möglicherweise inkl. 16.01?)

3. **Andere Filter:**
   - Vielleicht werden bestimmte Positionen oder Aufträge ausgeschlossen?
   - Vielleicht werden nur bestimmte Auftragsarten berücksichtigt?

---

## 📝 Nächste Schritte

1. ⚠️ **St-Anteil-Berechnung analysieren:**
   - Welche Berechnungslogik verwendet Locosoft für "St-Anteil"?
   - Gibt es Unterschiede zwischen "St-Anteil" und "Stmp.Anteil"?

2. 🔧 **Weitere Tests:**
   - Prüfe ob Zeitraum korrekt ist
   - Prüfe ob Filter korrekt sind
   - Prüfe ob Locosoft andere Kriterien verwendet

---

**Status:** ⚠️ **AW-Anteil passt sehr gut (1.2% Diff), aber St-Anteil zeigt große Abweichung (32.4% Diff)**
