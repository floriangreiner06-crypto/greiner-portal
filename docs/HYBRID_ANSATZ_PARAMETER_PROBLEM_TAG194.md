# Hybrid-Ansatz Parameter-Problem - TAG 194

**Datum:** 2026-01-16  
**Status:** ❌ **FEHLER** - Parameter-Anzahl stimmt nicht

---

## Problem

- **Query hat:** 9 %s Platzhalter
- **Parameter übergeben:** 7 Parameter
- **Fehler:** `IndexError: list index out of range`

---

## Parameter-Liste (Code)

```python
params = [
    von, bis,  # stempelungen_dedupliziert (erste CTE) - 2x %s
    von, bis,  # stempelzeit_leistungsgrad (TAG 192) - 2x %s (eigene CTE mit WITH)
    von, bis,  # stempelungen_roh (TAG 194: position-basierte Berechnung) - 2x %s
    von, bis,  # anwesenheit - 2x %s
    MECHANIKER_EXCLUDE  # TAG 192: Nur Azubis ausschließen - 1x %s
]
# Gesamt: 9 Parameter (2+2+2+2+1)
```

---

## Tatsächliche Parameter (Debug)

```
Anzahl params: 7
  0: 2026-01-01 (type: date)
  1: 2026-01-16 (type: date)
  2: 2026-01-01 (type: date)
  3: 2026-01-16 (type: date)
  4: 2026-01-01 (type: date)
  5: 2026-01-16 (type: date)
  6: [5025, 5026, 5028] (type: list)
```

**Fehlende Parameter:** 2 Parameter (von, bis für stempelzeit_leistungsgrad)

---

## Query-Struktur

Die Query hat folgende %s Platzhalter:

1. **stempelungen_dedupliziert:** 2x %s (von, bis)
2. **stempelzeit_leistungsgrad:** 2x %s (von, bis) - eigene WITH-CTE
3. **stempelungen_roh:** 2x %s (von, bis)
4. **anwesenheit:** 2x %s (von, bis)
5. **mechaniker_summen:** 1x %s (MECHANIKER_EXCLUDE)

**Gesamt:** 9 %s

---

## Mögliche Ursachen

1. **Parameter-Liste wird nach Formatierung geändert** - ABER: Code zeigt keine Änderung
2. **stempelzeit_leistungsgrad wird nicht korrekt formatiert** - ABER: Query zeigt %s Platzhalter
3. **Parameter-Liste wird vor Debug geändert** - MUSS GEPRÜFT WERDEN

---

## Nächste Schritte

1. ✅ Query-Struktur korrigiert
2. ✅ CTE-Reihenfolge korrigiert
3. ❌ Parameter-Liste korrigieren (2 Parameter fehlen)
4. ❌ Test durchführen

---

**Status:** ❌ **MUSS KORRIGIERT WERDEN**
