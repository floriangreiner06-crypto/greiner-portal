-- Prüfe Edith's Balance 2026
-- TAG 167: Sollte 24 Tage Resturlaub zeigen, nicht -3

SELECT 
    employee_id,
    name,
    anspruch,
    verbraucht,
    geplant,
    resturlaub
FROM v_vacation_balance_2026
WHERE name LIKE '%Edith%';

