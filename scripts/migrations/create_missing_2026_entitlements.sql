-- Erstelle fehlende Ansprüche 2026 für Mitarbeiter ohne Locosoft-Mapping
-- TAG 167

INSERT INTO vacation_entitlements (employee_id, year, total_days, carried_over, added_manually)
SELECT 
    e.id,
    2026,
    27.0,
    0.0,
    0.0
FROM employees e
WHERE e.aktiv = true
  AND e.id NOT IN (SELECT employee_id FROM vacation_entitlements WHERE year = 2026)
ON CONFLICT (employee_id, year) DO NOTHING;

-- Statistik
SELECT 
    COUNT(*) as anzahl_2026,
    SUM(total_days) as gesamt_tage
FROM vacation_entitlements
WHERE year = 2026;

-- Test: Edith
SELECT 
    employee_id,
    name,
    anspruch,
    verbraucht,
    geplant,
    resturlaub
FROM v_vacation_balance_2026
WHERE name LIKE '%Edith%';

