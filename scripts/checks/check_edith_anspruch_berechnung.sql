-- Prüfe Edith's Anspruch-Berechnung
-- TAG 167: Sollte 39 Tage sein

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
