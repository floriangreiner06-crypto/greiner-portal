# Bug: teile_status_api.py - GROUP BY Fehler (TAG 176)

**Datum:** 2026-01-09  
**Status:** ⚠️ Warning beim Service-Start  
**Impact:** Lieferzeiten-Cache wird nicht geladen

---

## 🚨 PROBLEM

**Fehlermeldung:**
```
WARNING:api.teile_status_api:Konnte Lieferzeiten nicht laden: 
column "loco_parts_inbound_delivery_notes.supplier_number" must appear 
in the GROUP BY clause or be used in an aggregate function
LINE 9: ...t_number, MIN(delivery_note_date) as lieferdatum, supplier_n...
```

**Betroffene Funktion:**
- `load_lieferzeiten()` - Zeile 40-94
- Wird beim Service-Start aufgerufen (Zeile 94)

**Impact:**
- ❌ Lieferzeiten-Cache wird nicht geladen
- ⚠️ Fallback-Werte werden verwendet (Zeile 86-90)
- ⚠️ Funktion funktioniert, aber mit veralteten Daten

---

## 🔍 URSACHE

**Problem in Zeile 56-59:**
```sql
erste_lieferung AS (
    SELECT part_number, MIN(delivery_note_date) as lieferdatum, supplier_number
    FROM loco_parts_inbound_delivery_notes
    WHERE delivery_note_date >= CURRENT_DATE - INTERVAL '180 days'
    GROUP BY part_number  -- ❌ FEHLT: supplier_number
)
```

**PostgreSQL-Regel:**
- Alle Spalten in SELECT müssen entweder:
  1. In GROUP BY stehen, ODER
  2. Aggregiert werden (MIN, MAX, SUM, etc.)

**Problem:**
- `supplier_number` wird selektiert, aber nicht gruppiert
- `MIN(delivery_note_date)` ist aggregiert ✅
- `part_number` ist in GROUP BY ✅
- `supplier_number` ist NICHT in GROUP BY ❌

**Warum funktioniert es nicht?**
- Ein Teil kann mehrere Lieferanten haben
- PostgreSQL weiß nicht, welchen `supplier_number` es nehmen soll
- Muss explizit in GROUP BY oder als Aggregat

---

## 💡 LÖSUNG

### Option 1: supplier_number in GROUP BY (Einfach)

**Problem:** Ein Teil kann mehrere Lieferanten haben
- Wenn ein Teil von mehreren Lieferanten geliefert wurde, gibt es mehrere Zeilen
- Dann müssen wir später filtern/aggregieren

**Änderung:**
```sql
erste_lieferung AS (
    SELECT part_number, MIN(delivery_note_date) as lieferdatum, supplier_number
    FROM loco_parts_inbound_delivery_notes
    WHERE delivery_note_date >= CURRENT_DATE - INTERVAL '180 days'
    GROUP BY part_number, supplier_number  -- ✅ supplier_number hinzugefügt
)
```

**Nachteil:**
- Mehr Zeilen (ein Teil pro Lieferant)
- Muss später filtern (nur erste Lieferung pro Teil)

---

### Option 2: Window Function (Besser)

**Idee:** Nur die erste Lieferung pro Teil (unabhängig vom Lieferanten)

**Änderung:**
```sql
erste_lieferung AS (
    SELECT DISTINCT ON (part_number)
        part_number,
        delivery_note_date as lieferdatum,
        supplier_number
    FROM loco_parts_inbound_delivery_notes
    WHERE delivery_note_date >= CURRENT_DATE - INTERVAL '180 days'
    ORDER BY part_number, delivery_note_date ASC
)
```

**Vorteil:**
- ✅ Nur eine Zeile pro Teil (erste Lieferung)
- ✅ supplier_number ist klar (vom ersten Lieferanten)
- ✅ Kein GROUP BY nötig

---

### Option 3: Subquery mit MIN (Sicher)

**Idee:** Erst MIN(delivery_note_date) finden, dann supplier_number holen

**Änderung:**
```sql
erste_lieferung AS (
    SELECT 
        el1.part_number,
        el1.delivery_note_date as lieferdatum,
        el1.supplier_number
    FROM loco_parts_inbound_delivery_notes el1
    INNER JOIN (
        SELECT part_number, MIN(delivery_note_date) as min_date
        FROM loco_parts_inbound_delivery_notes
        WHERE delivery_note_date >= CURRENT_DATE - INTERVAL '180 days'
        GROUP BY part_number
    ) el2 ON el1.part_number = el2.part_number 
         AND el1.delivery_note_date = el2.min_date
    WHERE el1.delivery_note_date >= CURRENT_DATE - INTERVAL '180 days'
)
```

**Vorteil:**
- ✅ Sicher (funktioniert immer)
- ✅ Klar welcher supplier_number (vom ersten Lieferanten)

**Nachteil:**
- ⚠️ Komplexer
- ⚠️ Wenn mehrere Lieferanten am gleichen Tag: Mehrere Zeilen

---

## 🎯 EMPFOHLENE LÖSUNG

**Option 2 (Window Function mit DISTINCT ON)** - Am einfachsten und klarsten

**Grund:**
- PostgreSQL-spezifisch, aber wir nutzen PostgreSQL
- Einfach und performant
- Klar: Erste Lieferung pro Teil

**Änderung in Zeile 55-60:**
```sql
erste_lieferung AS (
    SELECT DISTINCT ON (part_number)
        part_number,
        delivery_note_date as lieferdatum,
        supplier_number
    FROM loco_parts_inbound_delivery_notes
    WHERE delivery_note_date >= CURRENT_DATE - INTERVAL '180 days'
    ORDER BY part_number, delivery_note_date ASC
)
```

**Gleiche Änderung auch in Zeile 468-472** (für `/lieferanten` Endpoint)

---

## 📋 NÄCHSTE SCHRITTE

1. ✅ **Schnell fixen:** Option 2 implementieren
2. ✅ **Testen:** Service neu starten, Warning sollte weg sein
3. ✅ **Verifizieren:** Lieferzeiten-Cache wird geladen

---

**Status:** ⚠️ Bug identifiziert - Lösung bereit
