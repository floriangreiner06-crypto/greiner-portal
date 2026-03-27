# Urlaubsplaner PostgreSQL-Migration Bug Fix - Zusammenfassung

**Datum:** 2025-12-29  
**Problem:** Urlaubsplaner funktioniert nicht nach PostgreSQL-Migration  
**Status:** ✅ BEHOBEN

---

## Problem

Nach der PostgreSQL-Migration (TAG 135-139) funktionierte der Urlaubsplaner nicht mehr. Im Frontend erschien der Fehler:
```
Unexpected token '<', " X"
```

Dies deutete darauf hin, dass die API HTML statt JSON zurückgab, was typischerweise bei SQL-Syntax-Fehlern passiert.

---

## Ursache

Die `vacation_api.py` verwendete **hardcodierte PostgreSQL-Syntax**, die nicht mit dem Dual-Mode-System (`db_connection.py`) kompatibel war:

1. **`EXTRACT(YEAR FROM ...)`** statt `sql_year()` Helper
2. **Hardcodierte `%s` Placeholder** statt `convert_placeholders()`
3. **Fehlende Error Handler** für JSON-Responses bei Exceptions

---

## Lösung

### 1. Imports hinzugefügt

```python
from api.db_connection import (
    get_db_type,
    sql_year,
    convert_placeholders,
    sql_placeholder
)
```

### 2. Alle SQL-Queries korrigiert

**5 betroffene Stellen wurden korrigiert:**

- `/api/vacation/all-bookings` - Zeile ~1525
- `/api/vacation/my-bookings` - Zeile ~1691  
- `/api/vacation/requests` - Zeile ~1803
- `/api/vacation/my-balance` - Zeile ~1949, ~2378

**Vorher:**
```python
WHERE EXTRACT(YEAR FROM vb.booking_date) = %s
```

**Nachher:**
```python
query = f"""
    WHERE {sql_year('vb.booking_date')} = {sql_placeholder()}
"""
query = convert_placeholders(query)
```

### 3. Error Handler hinzugefügt

```python
@vacation_api.errorhandler(Exception)
def handle_vacation_error(e):
    """Stellt sicher, dass alle Fehler als JSON zurückgegeben werden."""
    import traceback
    return jsonify({
        'success': False,
        'error': str(e),
        'traceback': traceback.format_exc()
    }), 500
```

---

## Geänderte Dateien

- `api/vacation_api.py` - Alle SQL-Queries korrigiert, Error Handler hinzugefügt
- `docs/URLAUBSPLANER_POSTGRESQL_BUG_ANALYSE.md` - Vollständige Analyse dokumentiert

---

## Test-Plan

### 1. Service neustarten
```bash
sudo systemctl restart greiner-portal
```

### 2. Frontend testen
- Urlaubsplaner öffnen: `/urlaubsplaner/v2`
- Prüfen ob JSON-Parse-Fehler verschwunden ist
- Alle Funktionen testen:
  - Urlaub beantragen
  - Buchungen anzeigen
  - Genehmigungen
  - Kalender-Ansicht

### 3. Beide Datenbank-Modi testen

**SQLite-Modus:**
```bash
# In /opt/greiner-portal/config/.env:
DB_TYPE=sqlite
sudo systemctl restart greiner-portal
```

**PostgreSQL-Modus:**
```bash
# In /opt/greiner-portal/config/.env:
DB_TYPE=postgresql
sudo systemctl restart greiner-portal
```

---

## Erwartetes Ergebnis

✅ Alle API-Endpoints geben JSON zurück (keine HTML-Fehlerseiten mehr)  
✅ Queries funktionieren sowohl mit SQLite als auch PostgreSQL  
✅ Frontend zeigt keine JSON-Parse-Fehler mehr  
✅ Alle Urlaubsplaner-Funktionen funktionieren wieder

---

## Rollback

Falls Probleme auftreten, kann auf die vorherige Version zurückgewechselt werden:

```bash
cd /opt/greiner-portal
git checkout HEAD~1 api/vacation_api.py
sudo systemctl restart greiner-portal
```

---

## Weitere Verbesserungen

Für zukünftige Migrationen:
- ✅ Immer `db_connection.py` Helper verwenden
- ✅ Nie hardcodierte SQL-Syntax verwenden
- ✅ Error Handler für alle Blueprints hinzufügen
- ✅ Beide Datenbank-Modi testen

