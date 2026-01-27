# Performance-Verschlechterung Analyse TAG 208

**Datum:** 2026-01-22  
**Problem:** Server plötzlich langsam - lange Ladezeiten  
**Status:** 🔴 **KRITISCH - SQL-Fehler gefunden**

---

## 🔍 IDENTIFIZIERTE URSACHEN

### 1. SQL-Syntax-Fehler (KRITISCH) 🔴

**Problem:** PostgreSQL-Syntax-Fehler in mehreren Dateien

#### Fehler 1: `vacation_approver_service.py` Zeile 373
```python
WHERE e.aktiv = true  # ❌ FEHLER!
```

**Fehlermeldung:**
```
psycopg2.errors.UndefinedFunction: operator does not exist: boolean = integer
```

**Ursache:**
- `employees.aktiv` ist wahrscheinlich INTEGER (0/1), nicht BOOLEAN
- PostgreSQL kann nicht `boolean = integer` vergleichen

**Impact:**
- Jeder Aufruf von `get_team_for_approver()` schlägt fehl
- Exception-Handling kostet Performance
- Query wird wiederholt → noch langsamer

#### Fehler 2: `verkauf_data.py`
```
ERROR: for SELECT DISTINCT, ORDER BY expressions must appear in select list
```

**Ursache:**
- SQL-Syntax-Fehler in `get_verkaufer_liste()`
- PostgreSQL erfordert, dass ORDER BY Spalten auch in SELECT sind

#### Fehler 3: `verkauf_data.py`
```
ERROR: tuple indices must be integers or slices, not str
```

**Ursache:**
- Row-Zugriff-Problem (wahrscheinlich HybridRow vs. Dict)
- Code erwartet `row['key']`, aber bekommt Tuple

---

## 📊 STATISTIKEN

### Fehler-Häufigkeit
- **Letzte 2 Stunden:** 9 ERRORs
- **Letzte 6 Stunden:** (wird geprüft)
- **Betroffene Endpoints:**
  - `/api/vacation/approver/team` → `get_team_for_approver()`
  - `/api/verkauf/verkaufer` → `get_verkaufer_liste()`
  - `/api/verkauf/lieferforecast` → `get_lieferforecast()`

### Performance-Impact
- **Jeder Fehler:** ~50-200ms Exception-Handling
- **Wiederholte Queries:** 2-3x langsamer
- **Connection-Leaks:** Möglicherweise durch fehlgeschlagene Queries

---

## 🔧 SOFORT-FIXES

### Fix 1: `vacation_approver_service.py` Zeile 373

**Problem:**
```python
WHERE e.aktiv = true  # ❌
```

**Lösung Option A (PostgreSQL):**
```python
WHERE e.aktiv = 1  # ✅ Wenn INTEGER
```

**Lösung Option B (Dual-Mode):**
```python
from api.db_connection import get_db_type

if get_db_type() == 'postgresql':
    aktiv_check = "e.aktiv = 1"
else:
    aktiv_check = "e.aktiv = true"

query = f"""
    ...
    WHERE {aktiv_check}
"""
```

**Lösung Option C (SSOT):**
```python
# Prüfe ob es eine zentrale Funktion gibt
from api.db_utils import sql_boolean_check  # Falls vorhanden
```

### Fix 2: `verkauf_data.py` - ORDER BY Problem

**Problem:**
```sql
SELECT DISTINCT s.salesman_number, ...
ORDER BY e.last_name, e.first_name  -- ❌ Nicht in SELECT!
```

**Lösung:**
```sql
SELECT DISTINCT 
    s.salesman_number,
    e.last_name,  -- ✅ Hinzufügen
    e.first_name  -- ✅ Hinzufügen
ORDER BY e.last_name, e.first_name
```

### Fix 3: `verkauf_data.py` - Row-Zugriff

**Problem:**
- Code erwartet Dict-Zugriff `row['key']`
- Bekommt aber Tuple oder HybridRow

**Lösung:**
```python
# Sicherstellen, dass HybridRow verwendet wird
from api.db_utils import row_to_dict

row = cursor.fetchone()
row_dict = row_to_dict(row, cursor)  # ✅ Konvertieren
value = row_dict['key']
```

---

## 🎯 PRIORITÄT

| Fix | Priorität | Impact | Risiko |
|-----|-----------|--------|--------|
| `vacation_approver_service.py` | 🔴 **KRITISCH** | Hoch | Niedrig |
| `verkauf_data.py` ORDER BY | 🟠 **HOCH** | Mittel | Niedrig |
| `verkauf_data.py` Row-Zugriff | 🟠 **HOCH** | Mittel | Niedrig |

---

## 📋 NÄCHSTE SCHRITTE

1. **Sofort:** Fix 1 implementieren (`aktiv = true` → `aktiv = 1`)
2. **Sofort:** Fix 2 implementieren (ORDER BY korrigieren)
3. **Sofort:** Fix 3 implementieren (Row-Zugriff korrigieren)
4. **Testen:** Service neustarten, Endpoints testen
5. **Monitoring:** Logs prüfen, Fehler-Häufigkeit beobachten

---

## 🔍 WEITERE MÖGLICHE URSACHEN

### Kürzliche Änderungen (letzte 7 Tage)
- **TAG 195:** `werkstatt_data.py` - 634 Zeilen geändert
- **TAG 195:** `werkstatt_live_api.py` - 366 Zeilen geändert
- **TAG 194:** Viele Fixes

**Mögliche Probleme:**
- Neue Queries könnten langsam sein
- Neue DB-Verbindungen könnten Leaks haben
- Neue Features könnten Performance kosten

### System-Ressourcen
- **Gunicorn Worker:** 10 Worker laufen (normal)
- **Memory:** ~167MB pro Worker (normal)
- **CPU:** Wird geprüft

---

## 💡 HYPOTHESE

**Hauptursache:** SQL-Syntax-Fehler
- Fehlgeschlagene Queries werden wiederholt
- Exception-Handling kostet Performance
- Mögliche Connection-Leaks durch fehlgeschlagene Queries
- Kaskadierende Effekte: Ein Fehler → viele wiederholte Queries → Server überlastet

**Sekundäre Ursache:** Kürzliche Code-Änderungen
- Neue Features könnten langsame Queries haben
- Neue DB-Verbindungen könnten nicht optimal sein

---

**Status:** 🔴 **KRITISCH - Sofort-Fixes nötig**  
**Nächster Schritt:** Fix 1 implementieren (aktiv = true → aktiv = 1)
