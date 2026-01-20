# SQL-QUERIES: Werkstatt-KPI-Berechnungen

**Datum:** 2026-01-18  
**Zweck:** Vollständige SQL-Queries zum Testen und Überprüfen der Berechnungen

---

## 1. `get_st_anteil_position_basiert()` - Stempelanteil

**Datei:** `api/werkstatt_data.py` (Zeile 984-1007)

**Vollständige Query:**
```sql
WITH
-- 1. Alle Stempelungen (pro Position)
stempelungen_roh AS (
    SELECT DISTINCT ON (employee_number, order_number, order_position, order_position_line, start_time, end_time)
        employee_number,
        EXTRACT(EPOCH FROM (end_time - start_time)) / 60 AS dauer_minuten
    FROM times
    WHERE type = 2
      AND end_time IS NOT NULL
      AND order_number > 31
      AND order_position IS NOT NULL
      AND order_position_line IS NOT NULL
      AND start_time >= '2026-01-01'
      AND start_time < '2026-01-19'
)
-- 2. St-Anteil = 75 Prozent der Gesamt-Dauer (basierend auf CSV-Analyse)
SELECT 
    employee_number,
    ROUND(SUM(dauer_minuten)::numeric * 0.75, 0) AS stempelanteil_minuten
FROM stempelungen_roh
GROUP BY employee_number
HAVING SUM(dauer_minuten) > 0;
```

**Test für MA 5007:**
```sql
-- Ersetze WHERE-Klausel:
WHERE employee_number = 5007
```

**Erwartetes Ergebnis:**
- MA 5007: 14.926 Min = 248,8 Std
- Summe alle: 126.798 Min = 2.113,3 Std

**⚠️ PROBLEM:** Diese Funktion gibt **AW-Anteil (Vorgabezeit)** zurück, nicht St-Anteil!

---

## 2. `get_anwesenheit_rohdaten()` - Anwesenheit (Type=1)

**Datei:** `api/werkstatt_data.py` (Zeile 888-914)

**Vollständige Query:**
```sql
SELECT
    employee_number,
    DATE(start_time) as datum,
    SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as anwesend_min
FROM times
WHERE type = 1
  AND end_time IS NOT NULL
  AND start_time >= '2026-01-01' 
  AND start_time < '2026-01-19'
GROUP BY employee_number, DATE(start_time);
```

**Test für MA 5007:**
```sql
-- Ersetze WHERE-Klausel:
WHERE type = 1
  AND employee_number = 5007
  AND end_time IS NOT NULL
  AND start_time >= '2026-01-01' 
  AND start_time < '2026-01-19'
```

**Erwartetes Ergebnis:**
- MA 5007: 4.365 Min = 72,7 Std
- Summe alle: 37.584 Min = 626,4 Std

**⚠️ PROBLEM:** Diese Funktion gibt **St-Anteil (Stempelzeit)** zurück, nicht Anwesenheit!

---

## 3. `get_aw_verrechnet()` - AW-Anteil

**Datei:** `api/werkstatt_data.py` (Zeile 1041-1080)

**Vollständige Query:**
```sql
WITH auftraege_mit_stempelung AS (
    SELECT DISTINCT
        t.employee_number,
        t.order_number
    FROM times t
    WHERE t.type = 2
      AND t.end_time IS NOT NULL
      AND t.order_number > 31
      AND t.start_time >= '2026-01-01' 
      AND t.start_time < '2026-01-19'
),
aw_pro_mechaniker AS (
    SELECT
        ams.employee_number,
        SUM(l.time_units) as aw_gesamt,
        SUM(l.net_price_in_order) as umsatz_gesamt
    FROM auftraege_mit_stempelung ams
    JOIN labours l ON ams.order_number = l.order_number
    WHERE l.time_units > 0
    GROUP BY ams.employee_number
)
SELECT
    employee_number,
    aw_gesamt as aw,
    umsatz_gesamt as umsatz
FROM aw_pro_mechaniker;
```

**Test für MA 5007:**
```sql
-- Ersetze WHERE-Klausel in auftraege_mit_stempelung:
WHERE t.type = 2
  AND t.employee_number = 5007
  AND t.end_time IS NOT NULL
  AND t.order_number > 31
  AND t.start_time >= '2026-01-01' 
  AND t.start_time < '2026-01-19'
```

**Erwartetes Ergebnis:**
- MA 5007: 646,5 AW = 646,5 × 6 / 60 = 64,7 Std
- Summe alle: 5.641,7 AW = 564,2 Std

**✅ KORREKT:** Diese Funktion gibt korrekte AW-Einheiten zurück.

---

## 4. Vergleich: Type=2 roh (ohne 75% Faktor)

**Zum Vergleich mit `get_st_anteil_position_basiert()`:**

```sql
SELECT 
    employee_number,
    SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as stempelzeit_roh_min
FROM (
    SELECT DISTINCT ON (employee_number, order_number, order_position, order_position_line, start_time, end_time)
        employee_number,
        start_time,
        end_time
    FROM times
    WHERE type = 2
      AND end_time IS NOT NULL
      AND order_number > 31
      AND order_position IS NOT NULL
      AND order_position_line IS NOT NULL
      AND start_time >= '2026-01-01' 
      AND start_time < '2026-01-19'
) t
GROUP BY employee_number;
```

**Erwartetes Ergebnis:**
- MA 5007: ~19.901 Min = 331,7 Std (roh)
- Mit 75%: 14.926 Min = 248,8 Std (wie `get_st_anteil_position_basiert()`)

---

## 5. `get_stempelzeit_locosoft()` - Zeit-Spanne (Fallback)

**Datei:** `api/werkstatt_data.py` (Zeile 764-797)

**Vereinfachte Query (komplex mit Lücken/Pausen):**
```sql
-- Vereinfacht: Zeit-Spanne von erster bis letzter Stempelung pro Tag
SELECT
    employee_number,
    COUNT(DISTINCT DATE(start_time)) as tage,
    SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as stempel_min
FROM times
WHERE type = 2
  AND employee_number = 5007
  AND end_time IS NOT NULL
  AND order_number > 31
  AND start_time >= '2026-01-01' 
  AND start_time < '2026-01-19'
GROUP BY employee_number;
```

**Erwartetes Ergebnis:**
- MA 5007: ~3.733 Min = 62,2 Std (Zeit-Spanne)

---

## 6. Vergleich: Type=1 vs Type=2 für MA 5007

```sql
-- Type=1 (Anwesenheit)
SELECT 
    'Type=1' as typ,
    employee_number,
    SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as minuten
FROM times
WHERE type = 1
  AND employee_number = 5007
  AND end_time IS NOT NULL
  AND start_time >= '2026-01-01' 
  AND start_time < '2026-01-19'
GROUP BY employee_number

UNION ALL

-- Type=2 (Stempelzeit)
SELECT 
    'Type=2' as typ,
    employee_number,
    SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as minuten
FROM (
    SELECT DISTINCT ON (employee_number, order_number, order_position, order_position_line, start_time, end_time)
        employee_number,
        start_time,
        end_time
    FROM times
    WHERE type = 2
      AND employee_number = 5007
      AND end_time IS NOT NULL
      AND order_number > 31
      AND order_position IS NOT NULL
      AND order_position_line IS NOT NULL
      AND start_time >= '2026-01-01' 
      AND start_time < '2026-01-19'
) t
GROUP BY employee_number;
```

**Erwartetes Ergebnis:**
- Type=1: 4.365 Min = 72,7 Std
- Type=2: 19.901 Min = 331,7 Std (roh) oder 14.926 Min = 248,8 Std (mit 75%)

---

## 7. AW-Vergleich: get_aw_verrechnet() vs get_st_anteil_position_basiert()

```sql
-- AW aus get_aw_verrechnet()
WITH auftraege_mit_stempelung AS (
    SELECT DISTINCT
        t.employee_number,
        t.order_number
    FROM times t
    WHERE t.type = 2
      AND t.employee_number = 5007
      AND t.end_time IS NOT NULL
      AND t.order_number > 31
      AND t.start_time >= '2026-01-01' 
      AND t.start_time < '2026-01-19'
)
SELECT
    'AW aus get_aw_verrechnet()' as quelle,
    ams.employee_number,
    SUM(l.time_units) as aw_einheiten,
    SUM(l.time_units) * 6.0 / 60 as vorgabezeit_stunden
FROM auftraege_mit_stempelung ams
JOIN labours l ON ams.order_number = l.order_number
WHERE l.time_units > 0
GROUP BY ams.employee_number

UNION ALL

-- "Vorgabezeit" aus get_st_anteil_position_basiert() (mit 75% Faktor)
SELECT
    'Vorgabezeit aus get_st_anteil_position_basiert()' as quelle,
    employee_number,
    NULL as aw_einheiten,
    ROUND(SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60 * 0.75)::numeric, 0) / 60 as vorgabezeit_stunden
FROM (
    SELECT DISTINCT ON (employee_number, order_number, order_position, order_position_line, start_time, end_time)
        employee_number,
        start_time,
        end_time
    FROM times
    WHERE type = 2
      AND employee_number = 5007
      AND end_time IS NOT NULL
      AND order_number > 31
      AND order_position IS NOT NULL
      AND order_position_line IS NOT NULL
      AND start_time >= '2026-01-01' 
      AND start_time < '2026-01-19'
) t
GROUP BY employee_number;
```

**Erwartetes Ergebnis:**
- AW aus get_aw_verrechnet(): 646,5 AW = 64,7 Std
- Vorgabezeit aus get_st_anteil_position_basiert(): 248,8 Std

**⚠️ PROBLEM:** `get_st_anteil_position_basiert()` gibt 248,8 Std zurück, aber `get_aw_verrechnet()` gibt nur 64,7 Std zurück! Das passt nicht zusammen!

---

## 📊 AKTUELLE WERTE (01.01.2026 - 18.01.2026)

### Für MA 5007 (Reitmeier, Tobias):
- `get_st_anteil_position_basiert()`: 14.926 Min = **248,8 Std**
- `get_anwesenheit_rohdaten()`: 4.365 Min = **72,7 Std**
- `get_aw_verrechnet()`: 646,5 AW = **64,7 Std**
- `get_stempelzeit_locosoft()`: 3.733 Min = **62,2 Std**

### Finale Zuordnung (aktuell):
- `vorgabezeit` = 14.926 Min (248,8 Std) ← aus `get_st_anteil_position_basiert()`
- `stempelzeit` = 4.365 Min (72,7 Std) ← aus `get_anwesenheit_rohdaten()`
- `anwesenheit` = 5.238 Min (87,3 Std) ← Fallback aus `get_stempelzeit_locosoft()`

### KPIs:
- Leistungsgrad: 248,8 / 72,7 × 100 = **342,0%** (unrealistisch!)
- Produktivität: 72,7 / 87,3 × 100 = **83,3%** (realistisch)

---

## 🔍 FRAGEN ZUR ÜBERPRÜFUNG

1. **Warum gibt `get_st_anteil_position_basiert()` 248,8 Std zurück, aber `get_aw_verrechnet()` nur 64,7 Std?**
   - Sollte `get_st_anteil_position_basiert()` nicht den St-Anteil zurückgeben, nicht die Vorgabezeit?

2. **Warum gibt `get_anwesenheit_rohdaten()` 72,7 Std zurück, aber das ist weniger als die Stempelzeit?**
   - Sollte Anwesenheit nicht größer sein als Stempelzeit?

3. **Was zeigt Locosoft für MA 5007?**
   - St-Anteil: ?
   - AW-Anteil: ?
   - Anwesenheit: ?

---

**Erstellt:** TAG 196  
**Status:** 🔍 **ZU ÜBERPRÜFEN**
