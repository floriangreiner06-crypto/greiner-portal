# Systematische Suche: 1369 Min Differenz bei Tobias - TAG 194

**Datum:** 2026-01-16  
**Problem:** St-Anteil bei Tobias (5007) zeigt 1369 Min Differenz zu Locosoft

---

## 📊 Ausgangslage

- **Locosoft zeigt:** 4971 Min (82:51)
- **Unsere Berechnung OHNE anteilige Verteilung:** 3602 Min
- **Differenz:** 1369 Min (22.8 Stunden, 27.5%)

---

## 🔍 Getestete Berechnungen

| # | Berechnung | Ergebnis | Diff zu Locosoft | Status |
|---|------------|----------|------------------|--------|
| 1 | Alle Aufträge (auch order_number <= 31) | 3602 Min | 1369 Min (27.5%) | ❌ |
| 2 | MIT Stempelungen OHNE Positionen | 3602 Min | 1369 Min (27.5%) | ❌ |
| 3 | Alle Stempelungs-Typen (nicht nur type=2) | 3602 Min | 1369 Min (27.5%) | ❌ |
| 4 | Dedupliziert pro Tag (nicht pro Auftrag) | 3602 Min | 1369 Min (27.5%) | ❌ |
| 5 | OHNE Deduplizierung | 18674 Min | 13703 Min (275.7%) | ❌ |
| **6** | **Zeit-Spanne (erste bis letzte Stempelung)** | **3691 Min** | **1280 Min (25.7%)** | ⚠️ **NÄHER!** |
| 7 | MIT AW anteilig + OHNE AW gesamte Stempelzeit | 15409 Min | 10438 Min (210.0%) | ❌ |
| 8 | Pro Position (summiert, nur Positionen MIT AW) | 6624 Min | 1653 Min (33.3%) | ❌ |
| 9 | Aufträge OHNE AW-Positionen | 183 Min | 1186 Min | ❌ |
| 10 | Zeit-Spanne MINUS Lücken | 3602 Min | 1369 Min (27.5%) | ❌ |
| 11 | Zeit-Spanne MINUS Lücken MINUS Pausen | 3294 Min | 1677 Min (33.7%) | ❌ |
| 12 | Zeit-Spanne (ALLE Aufträge) | 3691 Min | 1280 Min (25.7%) | ⚠️ |
| 13 | Zeit-Spanne (OHNE Filter auf order_position) | 3691 Min | 1280 Min (25.7%) | ⚠️ |

---

## 💡 Erkenntnisse

### Zeit-Spanne ist am nächsten!
- **Zeit-Spanne:** 3691 Min (erste bis letzte Stempelung pro Tag)
- **Locosoft:** 4971 Min
- **Differenz:** 1280 Min (25.7%) - **besser als 1369 Min!**

### Mögliche Erklärung
- Locosoft verwendet möglicherweise die **Zeit-Spanne** als Basis
- Plus **zusätzliche 1280 Min** (statt 1369 Min)
- Diese 1280 Min könnten von Positionen OHNE AW kommen (10.6% von 12049 Min)

---

## 📝 Nächste Schritte

1. ⚠️ **Prüfe Positionen OHNE AW:**
   - Werden diese teilweise berücksichtigt?
   - Nur wenn sie innerhalb der Zeit-Spanne liegen?
   - Nur wenn sie auf Aufträgen MIT AW sind?

2. 🔍 **Weitere Tests:**
   - Kombination: Zeit-Spanne + Positionen OHNE AW (teilweise)
   - Prüfe ob bestimmte Positionen ausgeschlossen werden

---

**Status:** ⚠️ **Zeit-Spanne ist am nächsten (1280 Min Diff) - weitere Analyse nötig**
