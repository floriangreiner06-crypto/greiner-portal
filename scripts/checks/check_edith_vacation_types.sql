-- Prüfe Edith's vacation_types
-- TAG 167: Werden Krankheitstage als Urlaub gezählt?

-- 1. Alle Buchungen mit vacation_type
SELECT 
    vb.booking_date,
    vb.day_part,
    vb.status,
    vb.vacation_type_id,
    vt.name as vacation_type,
    CASE WHEN vb.day_part = 'full' THEN 1.0 ELSE 0.5 END as tage
FROM vacation_bookings vb
LEFT JOIN vacation_types vt ON vb.vacation_type_id = vt.id
JOIN employees e ON vb.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND EXTRACT(YEAR FROM vb.booking_date) = 2025
ORDER BY vb.booking_date;

-- 2. Summe nach vacation_type
SELECT 
    vb.vacation_type_id,
    vt.name as vacation_type,
    COUNT(*) FILTER (WHERE vb.day_part = 'full') as volle_tage,
    COUNT(*) FILTER (WHERE vb.day_part = 'half') as halbe_tage,
    (COUNT(*) FILTER (WHERE vb.day_part = 'full') * 1.0 +
     COUNT(*) FILTER (WHERE vb.day_part = 'half') * 0.5) as tage_gesamt
FROM vacation_bookings vb
LEFT JOIN vacation_types vt ON vb.vacation_type_id = vt.id
JOIN employees e ON vb.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND EXTRACT(YEAR FROM vb.booking_date) = 2025
  AND vb.status = 'approved'
GROUP BY vb.vacation_type_id, vt.name
ORDER BY vb.vacation_type_id;

-- 3. Prüfe ob Anspruch korrekt ist
SELECT 
    e.id,
    e.first_name || ' ' || e.last_name as name,
    ve.year,
    ve.total_days,
    ve.carried_over,
    ve.added_manually,
    (ve.total_days + COALESCE(ve.carried_over, 0) + COALESCE(ve.added_manually, 0)) as anspruch_gesamt
FROM employees e
LEFT JOIN vacation_entitlements ve ON e.id = ve.employee_id AND ve.year = 2025
WHERE e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%';

-- 4. Was sollte der Anspruch sein? (Standard 27?)
-- Prüfe andere Mitarbeiter zum Vergleich
SELECT 
    e.id,
    e.first_name || ' ' || e.last_name as name,
    ve.total_days,
    ve.carried_over,
    ve.added_manually,
    (ve.total_days + COALESCE(ve.carried_over, 0) + COALESCE(ve.added_manually, 0)) as anspruch_gesamt
FROM employees e
LEFT JOIN vacation_entitlements ve ON e.id = ve.employee_id AND ve.year = 2025
WHERE e.aktiv = true
  AND ve.total_days IS NOT NULL
ORDER BY anspruch_gesamt DESC
LIMIT 10;

