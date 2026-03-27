# Urlaubsplaner Debug Round 3 - Alle SQL-Queries korrigiert

**Datum:** 2025-12-29  
**Problem:** Syntax-Fehler nach Restart  
**Status:** ✅ ALLE SQL-Queries korrigiert

---

## Gefundene Probleme

### 1. INSERT-Query in Loop (Zeile 2458-2465)
**Problem:** Query wurde innerhalb von `cursor.execute()` String definiert
```python
# FALSCH:
cursor.execute("""
    query = f"""
        INSERT INTO ...
    """
    query = convert_placeholders(query)
    cursor.execute(query, ...)
""")
```

**Fix:** Query außerhalb der Loop definieren
```python
# RICHTIG:
insert_query = f"""
    INSERT INTO ...
"""
insert_query = convert_placeholders(insert_query)
for d in dates:
    cursor.execute(insert_query, ...)
```

### 2. UPDATE-Queries mit gemischten Placeholdern
**Problem:** UPDATE-Queries verwendeten `%s` UND `?` gemischt

**Betroffene Stellen:**
- `/api/vacation/approve` - Zeile ~1269
- `/api/vacation/reject` - Zeile ~1383
- `/api/vacation/cancel` - Zeile ~2224
- `/api/vacation/cancel-batch` - Zeile ~2690

**Fix:** Alle auf `sql_placeholder()` umgestellt

### 3. Weitere SELECT-Queries mit hardcodierten `%s`
**Betroffene Stellen:**
- Zeile ~1936: `SELECT id FROM vacation_bookings WHERE employee_id = %s AND booking_date = %s`
- Zeile ~2454: `SELECT id FROM vacation_bookings WHERE employee_id = %s AND booking_date = %s`

**Fix:** Alle auf `sql_placeholder()` umgestellt

---

## Zusammenfassung aller Fixes

### Round 1:
- ✅ `EXTRACT(YEAR FROM ...)` → `sql_year()`
- ✅ 5 SELECT-Queries korrigiert

### Round 2:
- ✅ 2 INSERT-Queries korrigiert
- ✅ 7 SELECT-Queries korrigiert

### Round 3:
- ✅ 1 INSERT-Query in Loop korrigiert (kritischer Bug!)
- ✅ 4 UPDATE-Queries korrigiert
- ✅ 2 weitere SELECT-Queries korrigiert

**Gesamt:** 21 SQL-Queries korrigiert

---

## Nächste Schritte

1. **Service neustarten:**
   ```bash
   sudo systemctl restart greiner-portal
   ```

2. **Browser-Cache leeren:**
   - Strg + Shift + R

3. **Testen:**
   - Urlaub beantragen
   - Urlaub genehmigen
   - Urlaub stornieren
   - Batch-Buchung

---

## Erwartetes Ergebnis

✅ Keine SQL-Syntax-Fehler mehr  
✅ Alle INSERT/UPDATE/SELECT-Queries funktionieren  
✅ Urlaubsplaner vollständig funktionsfähig

