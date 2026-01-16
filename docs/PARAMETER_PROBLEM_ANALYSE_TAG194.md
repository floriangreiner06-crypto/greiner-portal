# Parameter-Problem Analyse TAG 194

**Datum:** 2026-01-16  
**Status:** ❌ **PROBLEM BESTEHT WEITERHIN**

---

## Problem

`IndexError: list index out of range` bei `cursor.execute(query, params)`

---

## Analyse

### 1. Query-Struktur

- ✅ Query hat **9 %s Platzhalter** (korrekt gezählt)
- ✅ Alle %s sind in **SQL-Kontext** (nicht in Strings)
- ✅ Keine Formatierungsprobleme (keine `%%`, keine `{}`)

### 2. Parameter-Liste

- ✅ Parameter-Liste hat **9 Parameter** (korrekt)
- ✅ Parameter-Reihenfolge ist korrekt:
  1-2: `stempelungen_dedupliziert` (von, bis)
  3-4: `stempelzeit_leistungsgrad` (von, bis)
  5-6: `stempelungen_roh` (von, bis)
  7-8: `anwesenheit` (von, bis)
  9: `MECHANIKER_EXCLUDE` (Liste)

### 3. psycopg2 Tests

- ✅ Einfache Queries funktionieren (1-3 Parameter)
- ✅ Queries mit Listen funktionieren (`ALL(%s)`)
- ✅ Queries mit Datum funktionieren
- ❌ **Die tatsächliche Query funktioniert NICHT**

### 4. Query-Struktur Details

```
Query hat 9 %s Platzhalter in dieser Reihenfolge:
1. stempelungen_dedupliziert (Position 633)
2. stempelungen_dedupliziert (Position 653)
3. stempelzeit_leistungsgrad (Position 5988)
4. stempelzeit_leistungsgrad (Position 6010)
5. stempelungen_roh (Position 7672)
6. stempelungen_roh (Position 7694)
7. anwesenheit (Position 10496)
8. anwesenheit (Position 10516)
9. mechaniker_summen WHERE (Position 17454)
```

---

## Mögliche Ursachen

### 1. Query-Komplexität

Die Query ist sehr komplex mit vielen CTEs. Vielleicht gibt es ein Problem mit:
- Verschachtelten CTEs
- Subqueries
- JOINs

### 2. psycopg2 Parameter-Behandlung

Vielleicht behandelt psycopg2 die Parameter-Liste anders bei sehr komplexen Queries.

### 3. Query-Formatierung

Vielleicht gibt es ein Problem mit der Query-Formatierung, das nicht sichtbar ist.

---

## Nächste Schritte

1. **Query vereinfachen**: Teste mit weniger CTEs
2. **Query isolieren**: Teste einzelne CTEs
3. **Alternative Parameter-Übergabe**: Teste mit `execute_values` oder anderen Methoden
4. **psycopg2 Version prüfen**: Vielleicht gibt es ein bekanntes Problem

---

## Debug-Informationen

- Query gespeichert in: `/tmp/debug_query.sql`
- Parameter-Info gespeichert in: `/tmp/debug_params.txt`
- Query-Größe: ~283 Zeilen
- Parameter-Anzahl: 9

---

**Status:** ⚠️ **WEITERER DEBUGGING ERFORDERLICH**
