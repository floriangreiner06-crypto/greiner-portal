-- Fix: Edith's Urlaubsanspruch auf 39 Tage (wie in Locosoft)
-- TAG 167: Locosoft zeigt J.Url.ges. = 39, Portal hat nur 27

-- 1. Update für 2026
UPDATE vacation_entitlements
SET 
    total_days = 39.0,
    updated_at = CURRENT_TIMESTAMP
WHERE employee_id = 11
  AND year = 2026;

-- 2. Prüfen
SELECT 
    employee_id,
    year,
    total_days,
    carried_over,
    added_manually,
    (total_days + COALESCE(carried_over, 0) + COALESCE(added_manually, 0)) as anspruch_gesamt
FROM vacation_entitlements
WHERE employee_id = 11
ORDER BY year;

-- 3. View 2026 prüfen
SELECT 
    employee_id,
    name,
    anspruch,
    verbraucht,
    geplant,
    resturlaub
FROM v_vacation_balance_2026
WHERE name LIKE '%Edith%';

