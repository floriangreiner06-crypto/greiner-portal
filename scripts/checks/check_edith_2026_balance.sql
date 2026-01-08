-- Prüfe Edith's Balance 2026
-- TAG 167: Warum zeigt sie noch -3?

-- 1. View 2026 für Edith
SELECT 
    employee_id,
    name,
    anspruch,
    verbraucht,
    geplant,
    resturlaub
FROM v_vacation_balance_2026
WHERE name LIKE '%Edith%' OR name LIKE '%Egner%';

-- 2. View 2025 für Edith (zum Vergleich)
SELECT 
    employee_id,
    name,
    anspruch,
    verbraucht,
    geplant,
    resturlaub
FROM v_vacation_balance_2025
WHERE name LIKE '%Edith%' OR name LIKE '%Egner%';

-- 3. Ansprüche 2025 vs 2026
SELECT 
    year,
    total_days,
    carried_over,
    added_manually,
    (total_days + COALESCE(carried_over, 0) + COALESCE(added_manually, 0)) as anspruch_gesamt
FROM vacation_entitlements
WHERE employee_id = 11
ORDER BY year;

-- 4. Buchungen 2026 für Edith
SELECT 
    COUNT(*) FILTER (WHERE vb.day_part = 'full') as volle_tage,
    COUNT(*) FILTER (WHERE vb.day_part = 'half') as halbe_tage,
    (COUNT(*) FILTER (WHERE vb.day_part = 'full') * 1.0 +
     COUNT(*) FILTER (WHERE vb.day_part = 'half') * 0.5) as tage_gesamt,
    COUNT(*) as anzahl_buchungen
FROM vacation_bookings vb
JOIN employees e ON vb.employee_id = e.id
WHERE e.id = 11
  AND EXTRACT(YEAR FROM vb.booking_date) = 2026
  AND vb.status IN ('approved', 'pending');

-- 5. Alle Buchungen Edith (alle Jahre)
SELECT 
    EXTRACT(YEAR FROM vb.booking_date) as jahr,
    vb.status,
    COUNT(*) FILTER (WHERE vb.day_part = 'full') as volle_tage,
    COUNT(*) FILTER (WHERE vb.day_part = 'half') as halbe_tage,
    (COUNT(*) FILTER (WHERE vb.day_part = 'full') * 1.0 +
     COUNT(*) FILTER (WHERE vb.day_part = 'half') * 0.5) as tage_gesamt
FROM vacation_bookings vb
JOIN employees e ON vb.employee_id = e.id
WHERE e.id = 11
GROUP BY EXTRACT(YEAR FROM vb.booking_date), vb.status
ORDER BY jahr, vb.status;

