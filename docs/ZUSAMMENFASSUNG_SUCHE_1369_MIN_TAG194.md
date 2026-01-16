# Zusammenfassung: Suche nach 1369 Min Differenz - TAG 194

**Datum:** 2026-01-16  
**Problem:** St-Anteil bei Tobias (5007) zeigt 1369 Min Differenz zu Locosoft

---

## 📊 Beste Ergebnisse

| Berechnung | Ergebnis | Diff zu Locosoft | Status |
|------------|----------|------------------|--------|
| **Zeit-Spanne (erste bis letzte Stempelung)** | **3691 Min** | **1280 Min (25.7%)** | ⚠️ **AM NÄCHSTEN!** |
| OHNE anteilige Verteilung | 3602 Min | 1369 Min (27.5%) | ❌ |
| Zeit-Spanne MINUS Lücken | 3602 Min | 1369 Min (27.5%) | ❌ |
| Zeit-Spanne MINUS Lücken MINUS Pausen | 3294 Min | 1677 Min (33.7%) | ❌ |

---

## 💡 Erkenntnisse

### Zeit-Spanne ist am nächsten!
- **Zeit-Spanne:** 3691 Min (erste bis letzte Stempelung pro Tag, summiert)
- **Locosoft:** 4971 Min
- **Differenz:** 1280 Min (25.7%) - **besser als 1369 Min!**

### Mögliche Erklärung
- Locosoft verwendet möglicherweise die **Zeit-Spanne** als Basis
- Plus **zusätzliche 1280 Min**
- Diese 1280 Min könnten von:
  - Positionen OHNE AW (10.6% von 12049 Min)
  - Oder einer anderen Berechnungslogik

---

## 🔍 Getestete Kombinationen

1. ❌ Zeit-Spanne + Positionen OHNE AW (gesamte Stempelzeit) = 15740 Min (zu hoch)
2. ❌ Zeit-Spanne + Positionen OHNE AW auf Aufträgen MIT AW = 15558 Min (zu hoch)
3. ❌ Zeit-Spanne + Positionen OHNE AW außerhalb der Zeit-Spanne = 3691 Min (keine zusätzlichen)
4. ⚠️ Zeit-Spanne + Positionen OHNE AW (anteilig verteilt) = noch zu testen

---

## 📝 Nächste Schritte

1. ⚠️ **Prüfe weitere Kombinationen:**
   - Zeit-Spanne + Positionen OHNE AW (anteilig verteilt)
   - Zeit-Spanne + bestimmter Anteil der Positionen OHNE AW
   - Andere Berechnungslogik für Positionen OHNE AW

2. 🔍 **Alternative Ansätze:**
   - Vielleicht verwendet Locosoft eine andere Deduplizierung?
   - Oder werden bestimmte Stempelungen doppelt gezählt?
   - Oder gibt es spezielle Filter, die wir noch nicht kennen?

---

**Status:** ⚠️ **Zeit-Spanne ist am nächsten (1280 Min Diff) - weitere Analyse nötig**
