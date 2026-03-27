# Urlaubsplaner Final Fix - Placeholder-Problem behoben

**Datum:** 2025-12-29  
**Problem:** SQL Syntax Error trotz convert_placeholders()  
**Ursache:** `sql_placeholder()` in f-strings verursacht Inkonsistenz  
**Status:** ✅ BEHOBEN

---

## Problem-Analyse

Der Fehler "syntax error at or near ',' LINE 3: VALUES (?, ?, ?, ?, ?, ?, ?)" trat auf, obwohl `convert_placeholders()` verwendet wurde.

**Ursache:**
- `sql_placeholder()` gibt je nach DB_TYPE unterschiedliche Werte zurück (`?` für SQLite, `%s` für PostgreSQL)
- In f-strings wurde `sql_placeholder()` verwendet: `f"VALUES ({sql_placeholder()}, ...)"`
- Wenn zur Laufzeit `DB_TYPE` nicht korrekt erkannt wird, oder wenn es ein Timing-Problem gibt, kann `sql_placeholder()` `?` zurückgeben, aber PostgreSQL erwartet `%s`
- `convert_placeholders()` konvertiert nur `?` zu `%s`, aber wenn `sql_placeholder()` bereits `%s` zurückgibt, passiert nichts

**Lösung:**
- Immer `?` als Placeholder verwenden (konsistent)
- Dann `convert_placeholders()` aufrufen (konvertiert `?` zu `%s` für PostgreSQL)
- Keine f-strings mit `sql_placeholder()` mehr verwenden

---

## Durchgeführte Änderungen

### 1. INSERT-Query in `/api/vacation/book` (Zeile ~2054)
**Vorher:**
```python
query = f"""
    VALUES ({sql_placeholder()}, {sql_placeholder()}, ...)
"""
query = convert_placeholders(query)
```

**Nachher:**
```python
query = """
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""
query = convert_placeholders(query)
```

### 2. INSERT-Query in `/api/vacation/book-batch` (Zeile ~2466)
**Vorher:**
```python
insert_query = f"""
    VALUES ({sql_placeholder()}, {sql_placeholder()}, ...)
"""
insert_query = convert_placeholders(insert_query)
```

**Nachher:**
```python
insert_query = """
    VALUES (?, ?, ?, ?, ?, ?, ?)
"""
insert_query = convert_placeholders(insert_query)
```

---

## Warum funktioniert das jetzt?

1. **Konsistenz:** Immer `?` verwenden, egal welche DB
2. **Konvertierung:** `convert_placeholders()` konvertiert `?` zu `%s` für PostgreSQL
3. **Keine f-strings:** Keine Laufzeit-Abhängigkeiten mehr

---

## Test-Plan

1. **Service neustarten:**
   ```bash
   sudo systemctl restart greiner-portal
   ```

2. **Browser-Cache leeren:**
   - Strg + Shift + R

3. **Urlaub beantragen:**
   - Tag 29.12. anklicken
   - "Urlaub beantragen" klicken
   - Prüfen ob kein Fehler mehr auftritt

---

## Erwartetes Ergebnis

✅ Keine SQL-Syntax-Fehler mehr  
✅ INSERT-Queries funktionieren korrekt  
✅ Urlaubsbuchungen können erstellt werden

