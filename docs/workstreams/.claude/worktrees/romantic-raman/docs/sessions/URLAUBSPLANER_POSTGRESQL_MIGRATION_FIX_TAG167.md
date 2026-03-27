# Urlaubsplaner PostgreSQL-Migration Fix - TAG 167

**Datum:** 2026-01-05  
**Problem:** Falsche Ansprüche und fehlende Resturlaub-Anzeige nach PostgreSQL-Migration

---

## Problem

Nach der Migration von SQLite zu PostgreSQL wurden im Urlaubsplaner:
1. **Falsche Ansprüche** angezeigt
2. **Resturlaub** wurde nicht bei Mitarbeiternamen angezeigt
3. Das hatte alles schon mal funktioniert

**Vermutung:** SQLite-Syntax in Views wurde nicht korrekt migriert.

---

## Analyse

### 1. View 2025 prüfen

**Problem:** View `v_vacation_balance_2025` verwendete möglicherweise noch SQLite-Syntax:
- `strftime('%Y', ...)` statt `EXTRACT(YEAR FROM ...)`
- `aktiv = 1` statt `aktiv = true`
- `e.department` statt `e.department_name`

**Lösung:** View 2025 neu erstellen mit PostgreSQL-Syntax:
```sql
-- scripts/migrations/fix_vacation_balance_view_postgresql.sql
CREATE OR REPLACE VIEW v_vacation_balance_2025 AS
SELECT 
    e.id as employee_id,
    e.first_name || ' ' || e.last_name as name,
    COALESCE(e.department_name, 'Unbekannt') as department,
    -- ...
    COALESCE(SUM(ve.total_days + COALESCE(ve.carried_over, 0) + COALESCE(ve.added_manually, 0)), 0) as anspruch,
    -- ...
    EXTRACT(YEAR FROM vb.booking_date) = 2025  -- PostgreSQL-Syntax
FROM employees e
WHERE e.aktiv = true  -- PostgreSQL boolean
```

### 2. View 2026 prüfen

**Status:** View 2026 war bereits korrekt (PostgreSQL-Syntax).

### 3. API-Endpoint prüfen

**Status:** API verwendet korrekt `v_vacation_balance_{year}`:
```python
# api/vacation_api.py
query = f"""
    SELECT
        employee_id,
        name,
        department,
        location,
        anspruch,
        verbraucht,
        geplant,
        resturlaub
    FROM v_vacation_balance_{year}
    WHERE 1=1
"""
```

### 4. Frontend prüfen

**Status:** Frontend zeigt `resturlaub` korrekt an:
```javascript
// templates/urlaubsplaner_v2.html
const restDisplay = showRest ? `<small>(${emp.resturlaub ?? '?'})</small>` : '';
bd += `<td class="emp emp-col">${emp.name} ${restDisplay}</td>`;
```

**Hinweis:** Resturlaub wird nur angezeigt für:
- Eigene Ansicht (`isMe`)
- Admin (`isAdmin`)
- Genehmiger (`isAppr`)

---

## Durchgeführte Fixes

### 1. View 2025 neu erstellen

**Script:** `scripts/migrations/fix_vacation_balance_view_postgresql.sql`

**Änderungen:**
- ✅ `strftime` → `EXTRACT(YEAR FROM ...)`
- ✅ `aktiv = 1` → `aktiv = true`
- ✅ `e.department` → `COALESCE(e.department_name, 'Unbekannt')`
- ✅ `anspruch` = `total_days + carried_over + added_manually`

**Ergebnis:**
- 73 Mitarbeiter in View 2025
- Keine NULL-Werte
- Korrekte Berechnung

### 2. View 2026 prüfen

**Status:** ✅ Bereits korrekt (PostgreSQL-Syntax)

**Daten:**
- Edith: 39 Anspruch, 31 Resturlaub ✅
- Florian: 54 Anspruch, 54 Resturlaub ✅

---

## Nächste Schritte

1. ✅ View 2025 neu erstellt
2. ✅ Service neu gestartet
3. ⏳ Browser-Cache leeren (Strg+F5)
4. ⏳ Prüfen ob Ansprüche korrekt angezeigt werden
5. ⏳ Prüfen ob Resturlaub bei Mitarbeiternamen angezeigt wird

---

## Test-Ergebnisse

**View 2026:**
- ✅ Keine NULL-Werte
- ✅ Edith: 39 Anspruch, 31 Resturlaub
- ✅ Florian: 54 Anspruch, 54 Resturlaub

**View 2025:**
- ✅ Keine NULL-Werte
- ✅ 73 Mitarbeiter
- ✅ PostgreSQL-Syntax korrekt

---

**Status:** ✅ Views korrigiert, Service neu gestartet

