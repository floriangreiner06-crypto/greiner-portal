# Problem: St-Anteil Faktor 1.3467 hat keine Erklärung

**Datum:** 2026-01-XX  
**Status:** ⚠️ Temporäre Lösung - keine logische Erklärung

---

## Problem

Für Mechaniker 5007 (Tobias Reitmeier) passt die Berechnung:
```
St-Anteil = Zeit-Spanne pro Tag × 1.3467
```

**Aber:** Dieser Faktor hat keine logische Erklärung!

---

## Getestete Varianten (Mechaniker 5007, 01.01-15.01.26)

| Variante | Berechnet | Locosoft | Differenz | Status |
|----------|-----------|----------|-----------|--------|
| Zeit-Spanne pro Tag | 3691.3 Min | 4971.0 Min | -1279.7 Min (-25.7%) | ❌ |
| Summe Stempelungen (dedupliziert) | 3602.2 Min | 4971.0 Min | -1368.8 Min (-27.5%) | ❌ |
| Anteilige Verteilung nach AW | 3419.5 Min | 4971.0 Min | -1551.5 Min (-31.2%) | ❌ |
| Zeit-Spanne × 1.3467 | 4971.0 Min | 4971.0 Min | 0.0 Min (0.0%) | ✅ |

---

## Analyse

### Zeit-Spanne vs. Locosoft

- **Zeit-Spanne:** Summe der Zeit-Spannen pro Tag (erste bis letzte Stempelung)
- **Locosoft:** 4971.0 Min
- **Differenz:** 1279.7 Min (25.7% mehr)

### Mögliche Erklärungen (alle getestet, keine passt):

1. ❌ **Lücken zwischen Stempelungen:** Zeit-Spanne - Lücken = 3602.2 Min (immer noch zu niedrig)
2. ❌ **Summe + Lücken:** Summe + Lücken = 3691.3 Min (gleich Zeit-Spanne)
3. ❌ **Anteilige Verteilung nach AW:** 3419.5 Min (zu niedrig)
4. ❌ **Positionen einzeln zählen:** 18651.3 Min (viel zu hoch)

---

## Faktor 1.3467

**Berechnung:**
```
Faktor = Locosoft / Zeit-Spanne = 4971.0 / 3691.3 = 1.3467
```

**Problem:**
- Faktor ist nur für Mechaniker 5007 validiert
- Keine logische Erklärung, warum Locosoft die Zeit-Spanne mit diesem Faktor multipliziert
- Möglicherweise Mechaniker-spezifisch oder abhängig von anderen Faktoren

---

## Nächste Schritte

1. **Excel-Daten analysieren:**
   - St-Anteil pro Position in Excel mit DB-Daten vergleichen
   - Verstehen, wie Locosoft den St-Anteil pro Position berechnet

2. **Weitere Mechaniker testen:**
   - Prüfen ob Faktor 1.3467 auch für andere Mechaniker funktioniert
   - Falls nicht: Faktor-Mechanismus verstehen

3. **Locosoft Support kontaktieren:**
   - Nach exakter Formel für St-Anteil-Berechnung fragen
   - Besonders bei Stempelungen auf mehrere Positionen

---

## Aktuelle Implementierung

**Datei:** `api/werkstatt_data.py` → `get_st_anteil_position_basiert()`

**Code:**
```sql
St-Anteil = Zeit-Spanne pro Tag × 1.3467
```

**Warnung:** Diese Implementierung ist temporär und muss validiert werden!

---

**Status:** ⚠️ **Temporäre Lösung - weitere Analyse erforderlich**
