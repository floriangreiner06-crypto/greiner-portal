-- Prüfe Edith's Urlaub in Locosoft vs Portal
-- TAG 167: Vergleich Locosoft vs Portal

-- 1. Edith's Locosoft-ID finden
SELECT 
    e.id as employee_id,
    e.first_name || ' ' || e.last_name as name,
    lem.locosoft_id,
    le.employee_number as loco_employee_number
FROM employees e
LEFT JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
LEFT JOIN loco_employees le ON lem.locosoft_id = le.employee_number AND le.is_latest_record = true
WHERE e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%';

-- 2. Urlaub aus Locosoft absence_calendar (wenn Tabelle existiert)
-- Prüfe zuerst ob Tabelle existiert
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'loco_absence_calendar'
) as has_absence_calendar;

-- 3. Wenn Tabelle existiert: Urlaub aus Locosoft
SELECT 
    ac.date,
    ac.day_contingent,
    ac.reason,
    ac.type
FROM loco_absence_calendar ac
JOIN loco_employees le ON ac.employee_number = le.employee_number AND le.is_latest_record = true
JOIN ldap_employee_mapping lem ON le.employee_number = lem.locosoft_id
JOIN employees e ON lem.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND EXTRACT(YEAR FROM ac.date) = 2025
  AND ac.reason IN ('Url', 'BUr')  -- Urlaub
ORDER BY ac.date;

-- 4. Vergleich: Portal vs Locosoft (wenn möglich)
SELECT 
    'Portal' as quelle,
    COUNT(*) FILTER (WHERE vb.day_part = 'full') as volle_tage,
    COUNT(*) FILTER (WHERE vb.day_part = 'half') as halbe_tage,
    (COUNT(*) FILTER (WHERE vb.day_part = 'full') * 1.0 +
     COUNT(*) FILTER (WHERE vb.day_part = 'half') * 0.5) as tage_gesamt
FROM vacation_bookings vb
JOIN employees e ON vb.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND EXTRACT(YEAR FROM vb.booking_date) = 2025
  AND vb.status = 'approved'
UNION ALL
SELECT 
    'Locosoft' as quelle,
    COUNT(*) FILTER (WHERE ac.day_contingent >= 1.0) as volle_tage,
    COUNT(*) FILTER (WHERE ac.day_contingent < 1.0 AND ac.day_contingent > 0) as halbe_tage,
    COALESCE(SUM(ac.day_contingent), 0) as tage_gesamt
FROM loco_absence_calendar ac
JOIN loco_employees le ON ac.employee_number = le.employee_number AND le.is_latest_record = true
JOIN ldap_employee_mapping lem ON le.employee_number = lem.locosoft_id
JOIN employees e ON lem.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND EXTRACT(YEAR FROM ac.date) = 2025
  AND ac.reason IN ('Url', 'BUr');

