# Manuelle Prüfung - Parameter-Problem TAG 194

**Datum:** 2026-01-16  
**Zweck:** Schritt-für-Schritt Anleitung zur manuellen Prüfung des Parameter-Problems

---

## Schritt 1: Debug-Dateien prüfen

### 1.1 Query prüfen

```bash
# Auf Server (10.80.80.20)
cat /tmp/debug_query.sql | less

# Oder spezifisch nach %s suchen
grep -n '%s' /tmp/debug_query.sql
```

**Prüfe:**
- Wie viele %s Platzhalter gibt es? (sollte 9 sein)
- Wo sind die %s Platzhalter? (in welchen CTEs)

### 1.2 Parameter-Liste prüfen

```bash
# Auf Server
cat /tmp/debug_params.txt
```

**Prüfe:**
- Wie viele Parameter werden übergeben? (sollte 9 sein)
- Welche Parameter sind das? (von, bis, MECHANIKER_EXCLUDE)

### 1.3 Parameter nach Erstellung prüfen

```bash
# Auf Server
cat /tmp/debug_params_created.txt
```

**Prüfe:**
- Werden 9 Parameter erstellt? ✅
- Werden nur 7 Parameter übergeben? ❌

---

## Schritt 2: Query direkt in PostgreSQL testen

### 2.1 Verbindung zur Datenbank

```bash
# Auf Server (10.80.80.20)
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal
```

### 2.2 Query mit Parametern testen

```sql
-- Kopiere die Query aus /tmp/debug_query.sql
-- Ersetze %s durch tatsächliche Werte:

-- Beispiel:
-- %s → '2026-01-01'::date
-- %s → '2026-01-16'::date
-- %s → ARRAY[5025, 5026, 5028]

-- Teste die Query:
WITH
-- ... (Query aus debug_query.sql)
SELECT * FROM mechaniker_summen WHERE employee_number = 5007;
```

**Prüfe:**
- Läuft die Query ohne Fehler? ✅
- Werden Ergebnisse zurückgegeben? ✅

---

## Schritt 3: Python-Code manuell testen

### 3.1 Parameter-Liste manuell erstellen

```python
# Auf Server im Python-Interpreter
from datetime import date
from api.werkstatt_data import MECHANIKER_EXCLUDE

von = date(2026, 1, 1)
bis = date(2026, 1, 16)

params = [
    von, bis,  # 1-2: stempelungen_dedupliziert (erste CTE)
    von, bis,  # 3-4: stempelungen_dedupliziert (innerhalb stempelzeit_leistungsgrad)
    von, bis,  # 5-6: anwesenheit
    von, bis,  # 7-8: stempelungen_roh
    MECHANIKER_EXCLUDE  # 9: Nur Azubis ausschließen
]

print(f"Parameter-Anzahl: {len(params)}")
print(f"MECHANIKER_EXCLUDE: {MECHANIKER_EXCLUDE}")
```

**Prüfe:**
- Werden 9 Parameter erstellt? ✅
- Ist MECHANIKER_EXCLUDE eine Liste? ✅

### 3.2 Query manuell formatieren

```python
# Lade die Query
with open('/tmp/debug_query.sql', 'r') as f:
    query = f.read()

# Zähle %s
count = query.count('%s')
print(f"%s Platzhalter: {count}")

# Prüfe Parameter-Anzahl
print(f"Parameter-Anzahl: {len(params)}")

# Prüfe ob sie übereinstimmen
if count == len(params):
    print("✅ Parameter-Anzahl stimmt überein")
else:
    print(f"❌ Parameter-Anzahl stimmt NICHT: {count} %s, {len(params)} params")
```

---

## Schritt 4: psycopg2 direkt testen

### 4.1 Verbindung testen

```python
from api.db_utils import locosoft_session
from psycopg2.extras import RealDictCursor

# Teste die Verbindung
with locosoft_session() as conn:
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Einfache Query testen
    cursor.execute("SELECT 1 as test")
    result = cursor.fetchone()
    print(f"Verbindung OK: {result}")
```

### 4.2 Query mit Parametern testen

```python
from api.db_utils import locosoft_session
from psycopg2.extras import RealDictCursor
from datetime import date

von = date(2026, 1, 1)
bis = date(2026, 1, 16)
MECHANIKER_EXCLUDE = [5025, 5026, 5028]

# Lade Query
with open('/tmp/debug_query.sql', 'r') as f:
    query = f.read()

# Erstelle Parameter-Liste
params = [von, bis, von, bis, von, bis, von, bis, MECHANIKER_EXCLUDE]

print(f"Query hat {query.count('%s')} %s Platzhalter")
print(f"Parameter-Liste hat {len(params)} Parameter")

# Teste execute
with locosoft_session() as conn:
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(query, params)
        result = cursor.fetchall()
        print(f"✅ Query erfolgreich! {len(result)} Ergebnisse")
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
```

---

## Schritt 5: Verschachtelte CTEs prüfen

### 5.1 stempelzeit_leistungsgrad CTE isolieren

```sql
-- Teste nur die stempelzeit_leistungsgrad CTE
WITH stempelzeit_leistungsgrad AS (
    WITH stempelungen_dedupliziert AS (
        SELECT DISTINCT ON (t.employee_number, DATE(t.start_time), t.start_time, t.end_time)
            t.employee_number,
            t.start_time,
            t.end_time
        FROM times t
        WHERE t.type = 2
          AND t.end_time IS NOT NULL
          AND t.order_number > 31
          AND t.order_number != ALL(ARRAY[300014,31])
          AND t.start_time >= '2026-01-01'::date 
          AND t.start_time < '2026-01-16'::date + INTERVAL '1 day'
        ORDER BY t.employee_number, DATE(t.start_time), t.start_time, t.end_time
    )
    SELECT
        employee_number,
        SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as stempel_min_leistungsgrad
    FROM stempelungen_dedupliziert
    GROUP BY employee_number
)
SELECT * FROM stempelzeit_leistungsgrad WHERE employee_number = 5007;
```

**Prüfe:**
- Läuft die CTE ohne Fehler? ✅
- Werden Ergebnisse zurückgegeben? ✅

---

## Schritt 6: Alternative Lösung testen

### 6.1 stempelzeit_leistungsgrad ohne verschachtelte CTE

```sql
-- Alternative: stempelzeit_leistungsgrad ohne verschachtelte CTE
stempelzeit_leistungsgrad AS (
    SELECT
        t.employee_number,
        SUM(EXTRACT(EPOCH FROM (t.end_time - t.start_time)) / 60) as stempel_min_leistungsgrad
    FROM (
        SELECT DISTINCT ON (t.employee_number, DATE(t.start_time), t.start_time, t.end_time)
            t.employee_number,
            t.start_time,
            t.end_time
        FROM times t
        WHERE t.type = 2
          AND t.end_time IS NOT NULL
          AND t.order_number > 31
          AND t.order_number != ALL(ARRAY[300014,31])
          AND t.start_time >= %s AND t.start_time < %s + INTERVAL '1 day'
        ORDER BY t.employee_number, DATE(t.start_time), t.start_time, t.end_time
    ) t
    GROUP BY t.employee_number
),
```

**Vorteil:**
- Keine verschachtelte WITH-CTE
- %s Platzhalter sind direkt in der CTE
- Einfacher zu debuggen

---

## Checkliste

- [ ] Debug-Dateien geprüft (`/tmp/debug_query.sql`, `/tmp/debug_params.txt`)
- [ ] Query direkt in PostgreSQL getestet
- [ ] Parameter-Liste manuell erstellt und geprüft
- [ ] psycopg2 execute direkt getestet
- [ ] Verschachtelte CTEs isoliert getestet
- [ ] Alternative Lösung getestet

---

## Häufige Probleme

### Problem 1: Parameter-Anzahl stimmt nicht

**Symptom:** `IndexError: list index out of range`

**Lösung:**
- Prüfe ob alle %s Platzhalter in der Query vorhanden sind
- Prüfe ob die Parameter-Liste korrekt erstellt wird
- Prüfe ob MECHANIKER_EXCLUDE korrekt übergeben wird

### Problem 2: Verschachtelte CTEs

**Symptom:** %s Platzhalter werden nicht korrekt zugeordnet

**Lösung:**
- Verwende keine verschachtelten WITH-CTEs
- Verwende Subqueries statt verschachtelter CTEs

### Problem 3: Query-Formatierung

**Symptom:** {leerlauf_filter} wird nicht formatiert

**Lösung:**
- Prüfe ob leerlauf_filter korrekt definiert ist
- Prüfe ob f-string Formatierung korrekt ist

---

**Status:** ✅ **BEREIT FÜR MANUELLE PRÜFUNG**
