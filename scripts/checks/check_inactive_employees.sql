-- Prüfe ausgeschiedene Mitarbeiter in Urlaubsplaner
-- TAG 167: Andrea und Ulrich sollten nicht mehr angezeigt werden

-- 1. Mitarbeiter mit aktiv=false
SELECT 
    id,
    first_name || ' ' || last_name as name,
    aktiv,
    updated_at
FROM employees
WHERE (first_name LIKE '%Andrea%' OR last_name LIKE '%Pfeffer%')
   OR (first_name LIKE '%Michael%' OR last_name LIKE '%Ulrich%')
ORDER BY id;

-- 2. Prüfe ob sie in vacation_entitlements sind
SELECT 
    ve.year,
    ve.employee_id,
    e.first_name || ' ' || e.last_name as name,
    e.aktiv,
    ve.total_days
FROM vacation_entitlements ve
JOIN employees e ON ve.employee_id = e.id
WHERE (e.first_name LIKE '%Andrea%' OR e.last_name LIKE '%Pfeffer%')
   OR (e.first_name LIKE '%Michael%' OR last_name LIKE '%Ulrich%')
ORDER BY ve.year, e.id;

-- 3. Prüfe ob sie in View 2026 sind
SELECT 
    employee_id,
    name,
    anspruch,
    verbraucht,
    resturlaub
FROM v_vacation_balance_2026
WHERE name LIKE '%Andrea%' 
   OR name LIKE '%Pfeffer%'
   OR name LIKE '%Michael%'
   OR name LIKE '%Ulrich%';

-- 4. Alle inaktiven Mitarbeiter in View 2026
SELECT 
    COUNT(*) as anzahl_inaktiv_in_view
FROM v_vacation_balance_2026 v
JOIN employees e ON v.employee_id = e.id
WHERE e.aktiv = false;

-- 5. View-Definition prüfen (sollte e.aktiv = true filtern)
SELECT 
    pg_get_viewdef('v_vacation_balance_2026', true) as view_definition;

