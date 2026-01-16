# Parameter-Problem Analyse - Für lokale KI

**Datum:** 2026-01-16  
**Problem:** SQL Query hat 9 %s Platzhalter, aber nur 7 Parameter werden übergeben

---

## Problem-Beschreibung

### Code (api/werkstatt_data.py)

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

### Tatsächliche Parameter (Debug)

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

Die Query hat folgende CTEs mit %s Platzhaltern:

1. **stempelungen_dedupliziert:** 2x %s (von, bis)
2. **stempelzeit_leistungsgrad:** 2x %s (von, bis) - eigene WITH-CTE innerhalb der CTE
3. **stempelungen_roh:** 2x %s (von, bis)
4. **anwesenheit:** 2x %s (von, bis)
5. **mechaniker_summen:** 1x %s (MECHANIKER_EXCLUDE)

**Gesamt:** 9 %s Platzhalter

---

## Wichtige Details

### stempelzeit_leistungsgrad CTE

```sql
stempelzeit_leistungsgrad AS (
    WITH stempelungen_dedupliziert AS (
        SELECT DISTINCT ON (t.employee_number, DATE(t.start_time), t.start_time, t.end_time)
            t.employee_number,
            t.start_time,
            t.end_time
        FROM times t
        WHERE t.type = 2
          AND t.end_time IS NOT NULL
          AND t.order_number > 31
          {leerlauf_filter}
          AND t.start_time >= %s AND t.start_time < %s + INTERVAL '1 day'
        ORDER BY t.employee_number, DATE(t.start_time), t.start_time, t.end_time
    )
    SELECT
        employee_number,
        SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as stempel_min_leistungsgrad
    FROM stempelungen_dedupliziert
    GROUP BY employee_number
),
```

**WICHTIG:** Diese CTE hat eine eigene WITH-CTE innerhalb, die 2x %s benötigt!

---

## Mögliche Ursachen

1. **Parameter-Liste wird nach Definition geändert** - ABER: Code zeigt keine Änderung
2. **stempelzeit_leistungsgrad wird nicht korrekt formatiert** - ABER: Query zeigt %s Platzhalter
3. **Parameter-Liste wird vor Debug geändert** - MUSS GEPRÜFT WERDEN
4. **Python-Liste wird nicht korrekt erstellt** - MUSS GEPRÜFT WERDEN

---

## Frage an die KI

**Warum werden nur 7 Parameter übergeben, obwohl die Parameter-Liste 9 Parameter enthält?**

Mögliche Erklärungen:
- Wird die Parameter-Liste irgendwo gekürzt?
- Gibt es einen Fehler in der Python-Liste-Erstellung?
- Wird `stempelzeit_leistungsgrad` nicht korrekt in die Query eingefügt?

---

## Erwartete Lösung

Die Parameter-Liste sollte 9 Parameter enthalten:
1. von, bis (stempelungen_dedupliziert)
2. von, bis (stempelzeit_leistungsgrad)
3. von, bis (stempelungen_roh)
4. von, bis (anwesenheit)
5. MECHANIKER_EXCLUDE

**Gesamt: 9 Parameter**
