-- Prüfe Edith Egner's Urlaubsdaten
-- TAG 167: Warum zeigt sie -8 Tage?

-- 1. Balance aus View
SELECT employee_id, name, anspruch, verbraucht, geplant, resturlaub 
FROM v_vacation_balance_2025 
WHERE name LIKE '%Edith%' OR name LIKE '%Egner%';

-- 2. Anspruch aus vacation_entitlements
SELECT 
    e.id,
    e.first_name || ' ' || e.last_name as name,
    ve.total_days as anspruch,
    ve.carried_over,
    ve.added_manually,
    (ve.total_days + COALESCE(ve.carried_over, 0) + COALESCE(ve.added_manually, 0)) as anspruch_gesamt
FROM employees e
LEFT JOIN vacation_entitlements ve ON e.id = ve.employee_id AND ve.year = 2025
WHERE e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%';

-- 3. Buchungen 2025
SELECT 
    vb.booking_date,
    vb.day_part,
    vb.status,
    vt.name as vacation_type,
    CASE WHEN vb.day_part = 'full' THEN 1.0 ELSE 0.5 END as tage
FROM vacation_bookings vb
LEFT JOIN vacation_types vt ON vb.vacation_type_id = vt.id
JOIN employees e ON vb.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND EXTRACT(YEAR FROM vb.booking_date) = 2025
ORDER BY vb.booking_date;

-- 4. Summe verbrauchte Tage
SELECT 
    e.id,
    e.first_name || ' ' || e.last_name as name,
    COUNT(*) FILTER (WHERE vb.status = 'approved' AND vb.day_part = 'full') as volle_tage_approved,
    COUNT(*) FILTER (WHERE vb.status = 'approved' AND vb.day_part = 'half') as halbe_tage_approved,
    COUNT(*) FILTER (WHERE vb.status = 'pending' AND vb.day_part = 'full') as volle_tage_pending,
    COUNT(*) FILTER (WHERE vb.status = 'pending' AND vb.day_part = 'half') as halbe_tage_pending,
    (COUNT(*) FILTER (WHERE vb.status = 'approved' AND vb.day_part = 'full') * 1.0 +
     COUNT(*) FILTER (WHERE vb.status = 'approved' AND vb.day_part = 'half') * 0.5) as verbraucht_gesamt,
    (COUNT(*) FILTER (WHERE vb.status = 'pending' AND vb.day_part = 'full') * 1.0 +
     COUNT(*) FILTER (WHERE vb.status = 'pending' AND vb.day_part = 'half') * 0.5) as geplant_gesamt
FROM employees e
LEFT JOIN vacation_bookings vb ON e.id = vb.employee_id 
  AND EXTRACT(YEAR FROM vb.booking_date) = 2025
WHERE e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%'
GROUP BY e.id, e.first_name, e.last_name;

