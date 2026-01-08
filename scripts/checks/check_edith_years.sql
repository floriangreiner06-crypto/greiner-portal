-- Prüfe Edith's Buchungen nach Jahren
-- TAG 167: Verbrauch aus 2024 vs 2025

-- 1. Alle Buchungen nach Jahr gruppiert
SELECT 
    EXTRACT(YEAR FROM vb.booking_date) as jahr,
    COUNT(*) FILTER (WHERE vb.day_part = 'full') as volle_tage,
    COUNT(*) FILTER (WHERE vb.day_part = 'half') as halbe_tage,
    (COUNT(*) FILTER (WHERE vb.day_part = 'full') * 1.0 +
     COUNT(*) FILTER (WHERE vb.day_part = 'half') * 0.5) as tage_gesamt,
    COUNT(*) as anzahl_buchungen
FROM vacation_bookings vb
JOIN employees e ON vb.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND vb.status = 'approved'
GROUP BY EXTRACT(YEAR FROM vb.booking_date)
ORDER BY jahr;

-- 2. Buchungen 2024 (detailliert)
SELECT 
    vb.booking_date,
    vb.day_part,
    vb.status,
    CASE WHEN vb.day_part = 'full' THEN 1.0 ELSE 0.5 END as tage
FROM vacation_bookings vb
JOIN employees e ON vb.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND EXTRACT(YEAR FROM vb.booking_date) = 2024
  AND vb.status = 'approved'
ORDER BY vb.booking_date;

-- 3. Buchungen 2025 (detailliert)
SELECT 
    vb.booking_date,
    vb.day_part,
    vb.status,
    CASE WHEN vb.day_part = 'full' THEN 1.0 ELSE 0.5 END as tage
FROM vacation_bookings vb
JOIN employees e ON vb.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND EXTRACT(YEAR FROM vb.booking_date) = 2025
  AND vb.status = 'approved'
ORDER BY vb.booking_date;

-- 4. Ansprüche nach Jahr
SELECT 
    ve.year,
    ve.total_days,
    ve.carried_over,
    ve.added_manually,
    (ve.total_days + COALESCE(ve.carried_over, 0) + COALESCE(ve.added_manually, 0)) as anspruch_gesamt
FROM vacation_entitlements ve
JOIN employees e ON ve.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
ORDER BY ve.year;

-- 5. View vs. manuelle Berechnung 2025
SELECT 
    'View 2025' as quelle,
    employee_id,
    name,
    anspruch,
    verbraucht,
    geplant,
    resturlaub
FROM v_vacation_balance_2025 
WHERE name LIKE '%Edith%' OR name LIKE '%Egner%'
UNION ALL
SELECT 
    'Manuell 2025' as quelle,
    e.id as employee_id,
    e.first_name || ' ' || e.last_name as name,
    (ve.total_days + COALESCE(ve.carried_over, 0) + COALESCE(ve.added_manually, 0))::numeric as anspruch,
    (SELECT SUM(CASE WHEN vb.day_part = 'full' THEN 1.0 ELSE 0.5 END)
     FROM vacation_bookings vb
     WHERE vb.employee_id = e.id
       AND EXTRACT(YEAR FROM vb.booking_date) = 2025
       AND vb.status = 'approved')::numeric as verbraucht,
    (SELECT SUM(CASE WHEN vb.day_part = 'full' THEN 1.0 ELSE 0.5 END)
     FROM vacation_bookings vb
     WHERE vb.employee_id = e.id
       AND EXTRACT(YEAR FROM vb.booking_date) = 2025
       AND vb.status = 'pending')::numeric as geplant,
    ((ve.total_days + COALESCE(ve.carried_over, 0) + COALESCE(ve.added_manually, 0)) -
     (SELECT SUM(CASE WHEN vb.day_part = 'full' THEN 1.0 ELSE 0.5 END)
      FROM vacation_bookings vb
      WHERE vb.employee_id = e.id
        AND EXTRACT(YEAR FROM vb.booking_date) = 2025
        AND vb.status IN ('approved', 'pending')))::numeric as resturlaub
FROM employees e
LEFT JOIN vacation_entitlements ve ON e.id = ve.employee_id AND ve.year = 2025
WHERE e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%';

