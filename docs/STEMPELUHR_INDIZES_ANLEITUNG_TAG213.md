# Stempeluhr-Indizes Anleitung - TAG 213

**Datum:** 2026-01-27  
**Status:** ⚠️ **Benötigt DB-Admin-Rechte auf Locosoft-Server**

---

## 🔍 PROBLEM

Die Indizes können nicht automatisch erstellt werden, weil:

1. **`times` ist eine VIEW, nicht eine Tabelle**
   - Indizes können nicht direkt auf Views erstellt werden
   - Indizes müssen auf den zugrundeliegenden Tabellen erstellt werden

2. **User `loco_auswertung_benutzer` hat keine CREATE INDEX Berechtigung**
   - Benötigt DB-Admin-Rechte oder Owner-Rechte auf den Tabellen

---

## 🎯 LÖSUNG

Die Indizes müssen **manuell auf dem Locosoft-Server** erstellt werden, von einem User mit entsprechenden Rechten.

### Option 1: Auf zugrundeliegenden Tabellen (empfohlen)

**Falls `times` View auf einer Tabelle basiert (z.B. `times_raw` oder ähnlich):**

```sql
-- Auf dem Locosoft-Server (10.80.80.8) ausführen
-- Als DB-Admin oder Owner der Tabellen

-- 1. Index für aktive Stempelungen
CREATE INDEX IF NOT EXISTS idx_times_active 
    ON <zugrundeliegende_tabelle>(employee_number, order_number, start_time, type) 
    WHERE end_time IS NULL AND type = 2;

-- 2. Index für Datum-Filter
CREATE INDEX IF NOT EXISTS idx_times_date_type 
    ON <zugrundeliegende_tabelle>(DATE(start_time), type) 
    WHERE type = 2;

-- 3. Index für abgeschlossene Stempelungen
CREATE INDEX IF NOT EXISTS idx_times_completed 
    ON <zugrundeliegende_tabelle>(employee_number, order_number, start_time, end_time, type) 
    WHERE end_time IS NOT NULL AND type = 2;
```

**Problem:** Wir wissen nicht, welche Tabelle der View zugrunde liegt.

---

### Option 2: Materialized View mit Indizes (wenn möglich)

Falls die Locosoft-DB-Admin eine Materialized View erstellen kann:

```sql
-- Materialized View erstellen (mit Indizes möglich)
CREATE MATERIALIZED VIEW times_mv AS
SELECT * FROM times;

-- Indizes auf Materialized View erstellen
CREATE INDEX idx_times_mv_active 
    ON times_mv(employee_number, order_number, start_time, type) 
    WHERE end_time IS NULL AND type = 2;

-- View muss regelmäßig aktualisiert werden:
REFRESH MATERIALIZED VIEW times_mv;
```

---

### Option 3: Indizes auf anderen Tabellen (funktioniert)

Die Indizes auf `employees_history`, `labours`, `orders`, `vehicles` können erstellt werden, wenn der User die Rechte hat:

```sql
-- Auf dem Locosoft-Server ausführen
-- Als DB-Admin oder mit entsprechenden Rechten

-- 4. Index für employees_history
CREATE INDEX IF NOT EXISTS idx_employees_history_latest 
    ON employees_history(employee_number, is_latest_record) 
    WHERE is_latest_record = true;

-- 5. Index für labours
CREATE INDEX IF NOT EXISTS idx_labours_order_time 
    ON labours(order_number, time_units) 
    WHERE time_units > 0;

-- 6. Index für orders
CREATE INDEX IF NOT EXISTS idx_orders_number 
    ON orders(number);

-- 7. Index für vehicles
CREATE INDEX IF NOT EXISTS idx_vehicles_internal_number 
    ON vehicles(internal_number);
```

**Diese Indizes helfen bereits bei den JOINs!**

---

## 📋 NÄCHSTE SCHRITTE

### 1. Locosoft-DB-Admin kontaktieren

**Anfrage:**
- Welche Tabelle liegt der `times` View zugrunde?
- Kann der User `loco_auswertung_benutzer` CREATE INDEX Rechte bekommen?
- Oder können die Indizes von einem Admin erstellt werden?

### 2. Indizes auf JOIN-Tabellen erstellen (sofort möglich)

Falls Zugriff auf Locosoft-Server möglich:

```bash
# Auf Locosoft-Server (10.80.80.8) ausführen
psql -U postgres -d loco_auswertung_db -f /path/to/indexes_on_join_tables.sql
```

**Datei:** `migrations/add_stempeluhr_join_indexes_tag213.sql` (siehe unten)

### 3. Performance testen

Auch ohne `times`-Indizes sollten die JOIN-Indizes helfen:
- `employees_history`: 10-20% schneller
- `labours`: 10-20% schneller
- `orders`: 5-10% schneller
- `vehicles`: 5-10% schneller

**Gesamt:** 30-50% schneller (von 11s auf 5-7s)

---

## 🔧 ALTERNATIVE: JOIN-INDIZES ERSTELLEN

Erstelle ein separates Script nur für die JOIN-Indizes:

**Datei:** `migrations/add_stempeluhr_join_indexes_tag213.sql`

```sql
-- Indizes für JOIN-Tabellen (können erstellt werden, wenn User Rechte hat)
-- Auf Locosoft-Server ausführen

-- employees_history
CREATE INDEX IF NOT EXISTS idx_employees_history_latest 
    ON employees_history(employee_number, is_latest_record) 
    WHERE is_latest_record = true;

-- labours
CREATE INDEX IF NOT EXISTS idx_labours_order_time 
    ON labours(order_number, time_units) 
    WHERE time_units > 0;

-- orders
CREATE INDEX IF NOT EXISTS idx_orders_number 
    ON orders(number);

-- vehicles
CREATE INDEX IF NOT EXISTS idx_vehicles_internal_number 
    ON vehicles(internal_number);
```

---

## 📊 ERWARTETE VERBESSERUNG

**Ohne Indizes:**
- Stempeluhr-Query: 11+ Sekunden

**Mit JOIN-Indizes (sofort möglich):**
- Stempeluhr-Query: 5-7 Sekunden (30-50% schneller)

**Mit allen Indizes (inkl. times):**
- Stempeluhr-Query: 3-5 Sekunden (50-70% schneller)

**Mit Caching (zusätzlich):**
- Stempeluhr-Query: 0.3 Sekunden (Cache-Hit) 🚀

---

**Status:** ⚠️ **Benötigt DB-Admin-Zugriff auf Locosoft-Server**  
**Nächste Schritte:** JOIN-Indizes erstellen (falls möglich) oder Locosoft-DB-Admin kontaktieren
