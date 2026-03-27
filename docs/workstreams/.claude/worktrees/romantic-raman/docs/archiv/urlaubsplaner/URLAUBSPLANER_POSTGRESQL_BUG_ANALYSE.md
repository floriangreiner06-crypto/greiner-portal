# Urlaubsplaner PostgreSQL-Migration Bug Analyse

**Datum:** 2025-12-29  
**Problem:** Urlaubsplaner ist seit PostgreSQL-Migration buggy  
**Fehler:** "Unexpected token '<', " X"" (JSON-Parse-Fehler im Frontend)

---

## Problembeschreibung

Nach der PostgreSQL-Migration (TAG 135-139) funktioniert der Urlaubsplaner nicht mehr korrekt. Im Frontend erscheint der Fehler:
```
Unexpected token '<', " X"
```

Dies deutet darauf hin, dass die API HTML statt JSON zurückgibt, was typischerweise bei ungefangenen Exceptions oder SQL-Fehlern passiert.

---

## Identifizierte Probleme

### 1. Hardcodierte PostgreSQL-Syntax

**Problem:** Die `vacation_api.py` verwendet hardcodierte PostgreSQL-Syntax, die nicht mit dem Dual-Mode-System (`db_connection.py`) kompatibel ist.

**Betroffene Stellen:**

#### a) `EXTRACT(YEAR FROM ...)` statt `sql_year()` Helper

**Datei:** `api/vacation_api.py`

**Zeilen:**
- Zeile 1525: `WHERE EXTRACT(YEAR FROM vb.booking_date) = %s`
- Zeile 1663: `AND EXTRACT(YEAR FROM vb.booking_date) = %s`
- Zeile 1775: `AND EXTRACT(YEAR FROM vb.booking_date) = %s`
- Zeile 1942: `AND EXTRACT(YEAR FROM booking_date) = %s`
- Zeile 2378: `FROM vacation_bookings WHERE employee_id = %s AND EXTRACT(YEAR FROM booking_date) = %s`

**Problem:**
- `EXTRACT(YEAR FROM ...)` ist PostgreSQL-spezifisch
- Funktioniert nicht mit SQLite (braucht `strftime('%Y', ...)`)
- Wird nicht über `db_connection.py` Kompatibilitäts-Layer abgefangen

**Lösung:**
- Verwende `sql_year()` Helper aus `db_connection.py`
- Oder: Dynamische Query-Generierung basierend auf `get_db_type()`

#### b) Hardcodierte `%s` Placeholder

**Problem:**
- PostgreSQL verwendet `%s` als Placeholder
- SQLite verwendet `?` als Placeholder
- Die Queries verwenden direkt `%s` ohne `convert_placeholders()` zu nutzen

**Lösung:**
- Verwende `convert_placeholders()` aus `db_connection.py`
- Oder: Verwende `sql_placeholder()` für einzelne Placeholder

---

## 2. Fehlende Fehlerbehandlung

**Problem:** Wenn eine SQL-Query fehlschlägt, wird möglicherweise eine HTML-Fehlerseite zurückgegeben statt JSON.

**Aktueller Status:**
- Die meisten Endpoints haben `try/except` Blöcke
- ABER: SQL-Syntax-Fehler können vor dem Exception-Handler auftreten
- Flask gibt standardmäßig HTML-Fehlerseiten zurück

**Lösung:**
- Blueprint-spezifische Error Handler hinzufügen
- Sicherstellen, dass alle Exceptions als JSON zurückgegeben werden

---

## 3. Fehlende Importe

**Problem:** `vacation_api.py` importiert nicht die SQL-Kompatibilitäts-Helper aus `db_connection.py`.

**Aktuell:**
```python
from api.db_utils import db_session, row_to_dict, rows_to_list
```

**Benötigt:**
```python
from api.db_connection import (
    get_db_type,
    sql_year,
    convert_placeholders,
    sql_placeholder
)
```

---

## Betroffene Endpoints

### `/api/vacation/all-bookings`
- **Zeile 1525:** `EXTRACT(YEAR FROM vb.booking_date) = %s`
- **Problem:** Hardcodierte PostgreSQL-Syntax

### `/api/vacation/my-bookings`
- **Zeile 1663:** `EXTRACT(YEAR FROM vb.booking_date) = %s`
- **Problem:** Hardcodierte PostgreSQL-Syntax

### `/api/vacation/requests`
- **Zeile 1775:** `EXTRACT(YEAR FROM vb.booking_date) = %s`
- **Problem:** Hardcodierte PostgreSQL-Syntax

### `/api/vacation/my-balance`
- **Zeile 1942:** `EXTRACT(YEAR FROM booking_date) = %s`
- **Zeile 2378:** `EXTRACT(YEAR FROM booking_date) = %s`
- **Problem:** Hardcodierte PostgreSQL-Syntax

---

## Lösung

### Schritt 1: Imports hinzufügen

```python
from api.db_connection import (
    get_db_type,
    sql_year,
    convert_placeholders,
    sql_placeholder
)
```

### Schritt 2: Queries anpassen

**Vorher:**
```python
WHERE EXTRACT(YEAR FROM vb.booking_date) = %s
```

**Nachher:**
```python
WHERE {sql_year('vb.booking_date')} = {sql_placeholder()}
```

Oder mit `convert_placeholders()`:
```python
query = f"""
    WHERE {sql_year('vb.booking_date')} = ?
"""
query = convert_placeholders(query)
```

### Schritt 3: Error Handler hinzufügen

```python
@vacation_api.errorhandler(Exception)
def handle_error(e):
    import traceback
    return jsonify({
        'success': False,
        'error': str(e),
        'traceback': traceback.format_exc()
    }), 500
```

---

## Test-Plan

1. **SQLite-Modus testen:**
   - `.env`: `DB_TYPE=sqlite`
   - Alle Urlaubsplaner-Endpoints testen
   - Sicherstellen, dass Queries funktionieren

2. **PostgreSQL-Modus testen:**
   - `.env`: `DB_TYPE=postgresql`
   - Alle Urlaubsplaner-Endpoints testen
   - Sicherstellen, dass Queries funktionieren

3. **Frontend testen:**
   - Urlaubsplaner öffnen
   - Sicherstellen, dass keine JSON-Parse-Fehler auftreten
   - Alle Funktionen testen (Buchung, Genehmigung, etc.)

---

## Priorität

**HOCH** - Der Urlaubsplaner ist ein kritisches Feature und wird täglich genutzt.

---

## Status

- [x] Imports hinzugefügt
- [x] Queries angepasst (alle 5 EXTRACT(YEAR FROM ...) Stellen korrigiert)
- [x] Error Handler hinzugefügt
- [ ] SQLite-Modus getestet
- [ ] PostgreSQL-Modus getestet
- [ ] Frontend getestet

## Durchgeführte Änderungen

### 1. Imports hinzugefügt (Zeile 48-53)
```python
from api.db_connection import (
    get_db_type,
    sql_year,
    convert_placeholders,
    sql_placeholder
)
```

### 2. Queries korrigiert

**Alle 5 betroffenen Stellen wurden korrigiert:**
- `/api/vacation/all-bookings` (Zeile ~1525)
- `/api/vacation/my-bookings` (Zeile ~1691)
- `/api/vacation/requests` (Zeile ~1803)
- `/api/vacation/my-balance` (Zeile ~1949, ~2378)

**Vorher:**
```python
WHERE EXTRACT(YEAR FROM vb.booking_date) = %s
```

**Nachher:**
```python
WHERE {sql_year('vb.booking_date')} = {sql_placeholder()}
query = convert_placeholders(query)
```

### 3. Error Handler hinzugefügt (Zeile ~90-100)
```python
@vacation_api.errorhandler(Exception)
def handle_vacation_error(e):
    """Globaler Error Handler für Vacation API."""
    import traceback
    return jsonify({
        'success': False,
        'error': str(e),
        'traceback': traceback.format_exc()
    }), 500
```

## Nächste Schritte

1. **Service neustarten:**
   ```bash
   sudo systemctl restart greiner-portal
   ```

2. **Frontend testen:**
   - Urlaubsplaner öffnen: `/urlaubsplaner/v2`
   - Prüfen ob JSON-Parse-Fehler verschwunden ist
   - Alle Funktionen testen (Buchung, Genehmigung, etc.)

3. **Beide Datenbank-Modi testen:**
   - SQLite: `.env` → `DB_TYPE=sqlite`
   - PostgreSQL: `.env` → `DB_TYPE=postgresql`

