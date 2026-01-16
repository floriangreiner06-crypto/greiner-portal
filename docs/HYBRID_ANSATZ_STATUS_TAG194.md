# Hybrid-Ansatz Status - TAG 194

**Datum:** 2026-01-16  
**Status:** ⚠️ **IN ARBEIT** - Parameter-Problem

---

## Problem

- **Query hat:** 9 %s Platzhalter ✅
- **Parameter-Liste:** 9 Parameter ✅
- **Fehler:** `IndexError: list index out of range` ❌

---

## Analyse

### Query-Struktur

Die Query hat 9 %s Platzhalter in dieser Reihenfolge:

1. **stempelungen_dedupliziert** (erste CTE): 2x %s (Positionen 1-2)
2. **stempelungen_dedupliziert** (innerhalb stempelzeit_leistungsgrad): 2x %s (Positionen 3-4)
3. **anwesenheit**: 2x %s (Positionen 5-6)
4. **stempelungen_roh**: 2x %s (Positionen 7-8)
5. **mechaniker_summen**: 1x %s (Position 9)

**Gesamt:** 9 %s Platzhalter

### Parameter-Liste

```python
params = [
    von, bis,  # 1-2: stempelungen_dedupliziert (erste CTE)
    von, bis,  # 3-4: stempelungen_dedupliziert (innerhalb stempelzeit_leistungsgrad)
    von, bis,  # 5-6: anwesenheit
    von, bis,  # 7-8: stempelungen_roh
    MECHANIKER_EXCLUDE  # 9: Nur Azubis ausschließen
]
```

**Gesamt:** 9 Parameter

---

## Problem

Trotz korrekter Parameter-Liste (9 Parameter) und korrekter Query (9 %s) tritt weiterhin `IndexError: list index out of range` auf.

**Mögliche Ursachen:**
1. Parameter-Liste wird zwischen Erstellung und execute geändert
2. Query-Formatierung entfernt %s Platzhalter
3. psycopg2 behandelt verschachtelte CTEs anders

---

## Nächste Schritte

1. ✅ Query-Struktur analysiert
2. ✅ Parameter-Liste korrigiert
3. ❌ Problem besteht weiterhin
4. 🔍 MUSS WEITER ANALYSIERT WERDEN

---

**Status:** ⚠️ **MUSS KORRIGIERT WERDEN**
