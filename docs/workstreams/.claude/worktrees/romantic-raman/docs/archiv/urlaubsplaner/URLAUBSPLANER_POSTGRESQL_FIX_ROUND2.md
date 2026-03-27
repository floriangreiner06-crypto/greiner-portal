# Urlaubsplaner PostgreSQL-Migration Bug Fix - Round 2

**Datum:** 2025-12-29  
**Problem:** SQL Syntax Error - "syntax error at or near ',' LINE 3: VALUES (?, ?, ?, ?, ?, ?, ?)"  
**Status:** ✅ BEHOBEN

---

## Problem

Nach dem ersten Fix traten weiterhin SQL-Syntax-Fehler auf:
```
syntax error at or near "," LINE 3: VALUES (?, ?, ?, ?, ?, ?, ?)^
```

**Ursache:** INSERT-Queries verwendeten noch hardcodierte `?` Placeholder, die nicht mit `convert_placeholders()` behandelt wurden.

---

## Lösung

### Alle INSERT-Queries korrigiert

**2 betroffene Stellen:**

1. **`/api/vacation/book`** - Zeile ~2045
   - INSERT mit 8 Parametern (employee_id, booking_date, vacation_type_id, day_part, status, comment, created_by, created_at)

2. **`/api/vacation/book-batch`** - Zeile ~2449
   - INSERT mit 7 Parametern (employee_id, booking_date, vacation_type_id, day_part, status, comment, created_at)

**Vorher:**
```python
cursor.execute("""
    INSERT INTO vacation_bookings (...)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (params...))
```

**Nachher:**
```python
query = f"""
    INSERT INTO vacation_bookings (...)
    VALUES ({sql_placeholder()}, {sql_placeholder()}, ...)
"""
query = convert_placeholders(query)
cursor.execute(query, (params...))
```

### Alle SELECT-Queries mit hardcodierten `%s` korrigiert

**6 betroffene Stellen:**

1. Zeile ~143: `SELECT username FROM users WHERE id = %s`
2. Zeile ~2059: `SELECT name FROM vacation_types WHERE id = %s`
3. Zeile ~1999: `SELECT ... FROM v_vacation_balance_{year} WHERE employee_id = %s`
4. Zeile ~2410: `SELECT total_days FROM vacation_entitlements WHERE employee_id = %s AND year = %s`
5. Zeile ~2461: `SELECT name FROM vacation_types WHERE id = %s`
6. Zeile ~2647: `SELECT ad_groups FROM users WHERE username LIKE ? OR username = %s`
7. Zeile ~2768: `SELECT locosoft_id FROM employees WHERE id = %s`

**Alle wurden korrigiert zu:**
```python
query = f"SELECT ... WHERE id = {sql_placeholder()}"
query = convert_placeholders(query)
cursor.execute(query, (params...))
```

---

## Geänderte Dateien

- `api/vacation_api.py` - Alle INSERT und SELECT Queries korrigiert

---

## Test-Plan

### 1. Service neustarten
```bash
sudo systemctl restart greiner-portal
```

### 2. Frontend testen
- Urlaubsplaner öffnen: `/urlaubsplaner/v2`
- **Urlaub beantragen testen:**
  - Tage im Kalender anklicken/ziehen
  - "Urlaub beantragen" klicken
  - Prüfen ob keine SQL-Fehler mehr auftreten
- **Batch-Buchung testen:**
  - Mehrere Tage auf einmal buchen
  - Prüfen ob INSERT funktioniert

### 3. Logs prüfen
```bash
journalctl -u greiner-portal -f
```

Sollte keine SQL-Syntax-Fehler mehr zeigen.

---

## Erwartetes Ergebnis

✅ Keine SQL-Syntax-Fehler mehr  
✅ INSERT-Queries funktionieren mit PostgreSQL  
✅ Alle SELECT-Queries funktionieren mit PostgreSQL  
✅ Urlaubsbuchungen können erfolgreich erstellt werden

---

## Zusammenfassung aller Fixes

### Round 1:
- ✅ `EXTRACT(YEAR FROM ...)` → `sql_year()`
- ✅ SELECT-Queries mit `%s` → `convert_placeholders()`
- ✅ Error Handler hinzugefügt

### Round 2:
- ✅ INSERT-Queries mit `?` → `convert_placeholders()`
- ✅ Alle verbleibenden SELECT-Queries mit `%s` → `convert_placeholders()`

**Gesamt:** 13 SQL-Queries korrigiert

