# Stempeluhr Performance-Problem - TAG 213

**Datum:** 2026-01-27  
**Status:** 🔴 **KRITISCH - 11+ Sekunden Ladezeit**

---

## 🔍 PROBLEM

Die Stempeluhr-API (`/api/werkstatt/live/stempeluhr`) dauert **11+ Sekunden** und blockiert die gesamte Seite.

**Symptome:**
- Request bleibt im "Pending"-Status
- Browser zeigt Ladeanzeige
- User-Experience sehr schlecht

**Häufigkeit:**
- Wird alle 5-10 Sekunden aufgerufen (Auto-Refresh)
- Mehrere parallele Requests (verschiedene Filter)

---

## 📊 QUERY-ANALYSE

**Datei:** `api/werkstatt_data.py`, Funktion `get_stempeluhr()`

**Komplexität:**
1. **CTE `aktuelle_stempelungen`:**
   - DISTINCT ON mit 3 Spalten
   - Komplexe CASE-Statements für Pausenzeit (4 verschiedene Fälle)
   - 2 Subqueries mit DISTINCT ON für `heute_abgeschlossen_min` und `laufzeit_min`
   - NOT EXISTS Subquery

2. **Haupt-Query:**
   - 5 LEFT JOINs (employees_history, orders, employees_history, vehicles, makes)
   - LATERAL JOIN für labours (SUM + MAX)
   - WHERE-Clause mit mehreren Bedingungen

3. **Weitere Queries:**
   - Leerlauf-Stempelungen
   - Pausierte Mechaniker
   - Feierabend-Mechaniker
   - Abwesende Mechaniker

**Geschätzte Query-Zeit:** 5-15 Sekunden (je nach Datenmenge)

---

## 🎯 OPTIMIERUNGS-STRATEGIE

### Priorität 1: Indizes (Sofort)

**Fehlende Indizes:**
```sql
-- Für aktuelle Stempelungen (end_time IS NULL)
CREATE INDEX IF NOT EXISTS idx_times_active 
    ON times(employee_number, order_number, start_time, type) 
    WHERE end_time IS NULL AND type = 2;

-- Für Datum-Filter
CREATE INDEX IF NOT EXISTS idx_times_date_type 
    ON times(DATE(start_time), type) 
    WHERE type = 2;

-- Für abgeschlossene Stempelungen
CREATE INDEX IF NOT EXISTS idx_times_completed 
    ON times(employee_number, order_number, start_time, end_time, type) 
    WHERE end_time IS NOT NULL AND type = 2;

-- Für employees_history (häufig verwendet)
CREATE INDEX IF NOT EXISTS idx_employees_history_latest 
    ON employees_history(employee_number, is_latest_record) 
    WHERE is_latest_record = true;

-- Für labours (LATERAL JOIN)
CREATE INDEX IF NOT EXISTS idx_labours_order_time 
    ON labours(order_number, time_units) 
    WHERE time_units > 0;
```

**Geschätzter Gewinn:** 50-70% schneller (von 11s auf 3-5s)

---

### Priorität 2: Query-Vereinfachung

**Problem 1: Pausenzeit-Berechnung in SQL**
- 4 verschiedene CASE-Statements
- Wird 2x berechnet (heute_session_min + laufzeit_min)

**Lösung:**
- Pausenzeit-Berechnung in Python (nach Query)
- Einfacheres SQL

**Problem 2: Mehrfache DISTINCT ON Subqueries**
- `heute_abgeschlossen_min` und `laufzeit_min` haben identische Subqueries

**Lösung:**
- Eine Subquery, Ergebnis wiederverwenden

**Geschätzter Gewinn:** 20-30% schneller (von 5s auf 3-4s)

---

### Priorität 3: Caching

**Problem:**
- Query wird alle 5-10 Sekunden aufgerufen
- Daten ändern sich nicht so häufig

**Lösung:**
- Redis-Cache mit 10 Sekunden TTL
- Cache-Key: `stempeluhr:{datum}:{subsidiaries}`
- Bei Stempelung-Update: Cache invalidieren

**Geschätzter Gewinn:** 90% schneller (von 3s auf 0.3s bei Cache-Hit)

---

## 🔧 IMPLEMENTIERUNGS-PLAN

### Schritt 1: Indizes hinzufügen (15 Minuten)

**Migration:** `migrations/add_stempeluhr_performance_indexes_tag213.sql`

```sql
BEGIN;

-- Für aktuelle Stempelungen
CREATE INDEX IF NOT EXISTS idx_times_active 
    ON times(employee_number, order_number, start_time, type) 
    WHERE end_time IS NULL AND type = 2;

-- Für Datum-Filter
CREATE INDEX IF NOT EXISTS idx_times_date_type 
    ON times(DATE(start_time), type) 
    WHERE type = 2;

-- Für abgeschlossene Stempelungen
CREATE INDEX IF NOT EXISTS idx_times_completed 
    ON times(employee_number, order_number, start_time, end_time, type) 
    WHERE end_time IS NOT NULL AND type = 2;

-- Für employees_history
CREATE INDEX IF NOT EXISTS idx_employees_history_latest 
    ON employees_history(employee_number, is_latest_record) 
    WHERE is_latest_record = true;

-- Für labours
CREATE INDEX IF NOT EXISTS idx_labours_order_time 
    ON labours(order_number, time_units) 
    WHERE time_units > 0;

COMMIT;
```

### Schritt 2: Query vereinfachen (1-2 Stunden)

**Datei:** `api/werkstatt_data.py`, Funktion `get_stempeluhr()`

**Änderungen:**
1. Pausenzeit-Berechnung in Python auslagern
2. Subqueries zusammenfassen
3. LATERAL JOIN optimieren

### Schritt 3: Caching einführen (1 Stunde)

**Datei:** `api/werkstatt_live_api.py`, Endpoint `/stempeluhr`

**Implementierung:**
```python
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_stempeluhr(ttl=10):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Cache-Key bauen
            cache_key = f"stempeluhr:{kwargs.get('datum')}:{kwargs.get('subsidiaries')}"
            
            # Cache prüfen
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Query ausführen
            result = func(*args, **kwargs)
            
            # Cache setzen
            redis_client.setex(cache_key, ttl, json.dumps(result))
            
            return result
        return wrapper
    return decorator
```

---

## 📈 ERWARTETE VERBESSERUNG

**Aktuell:**
- Stempeluhr-Query: **11+ Sekunden** 🔴

**Nach Indizes:**
- Stempeluhr-Query: **3-5 Sekunden** 🟡

**Nach Query-Vereinfachung:**
- Stempeluhr-Query: **2-4 Sekunden** 🟡

**Nach Caching:**
- Stempeluhr-Query: **0.3 Sekunden** (Cache-Hit) ✅
- Stempeluhr-Query: **2-4 Sekunden** (Cache-Miss) 🟡

**Gesamtverbesserung: 30-40x schneller** (bei Cache-Hit) 🚀

---

## 🧪 TESTING

### Vor Optimierung:
```bash
time curl -s "http://localhost:5000/api/werkstatt/live/stempeluhr?subsidiary=1,2" | jq '.summary'
# Erwartet: ~11 Sekunden
```

### Nach Optimierung:
```bash
time curl -s "http://localhost:5000/api/werkstatt/live/stempeluhr?subsidiary=1,2" | jq '.summary'
# Erwartet: ~0.3 Sekunden (Cache-Hit) oder ~3 Sekunden (Cache-Miss)
```

---

**Status:** 🔴 **KRITISCH - Sofort-Maßnahmen nötig**  
**Nächste Schritte:** Indizes hinzufügen (Priorität 1)
