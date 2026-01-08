-- Prüfe Edith's 2024 Urlaub in Locosoft
-- TAG 167: Wurden 2024-Tage fälschlicherweise in 2025 gezählt?

-- 1. Urlaub 2024 aus Locosoft
SELECT 
    ac.date,
    ac.day_contingent,
    ac.reason,
    ac.type,
    CASE 
        WHEN ac.reason IN ('Url', 'BUr') THEN 'Urlaub'
        ELSE 'Sonstige'
    END as typ_kategorie
FROM loco_absence_calendar ac
JOIN loco_employees le ON ac.employee_number = le.employee_number AND le.is_latest_record = true
JOIN ldap_employee_mapping lem ON le.employee_number = lem.locosoft_id
JOIN employees e ON lem.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND EXTRACT(YEAR FROM ac.date) = 2024
  AND ac.reason IN ('Url', 'BUr')
ORDER BY ac.date;

-- 2. Summe 2024 vs 2025 aus Locosoft
SELECT 
    EXTRACT(YEAR FROM ac.date) as jahr,
    COUNT(*) FILTER (WHERE ac.day_contingent >= 1.0) as volle_tage,
    COUNT(*) FILTER (WHERE ac.day_contingent < 1.0 AND ac.day_contingent > 0) as halbe_tage,
    COALESCE(SUM(ac.day_contingent), 0) as tage_gesamt
FROM loco_absence_calendar ac
JOIN loco_employees le ON ac.employee_number = le.employee_number AND le.is_latest_record = true
JOIN ldap_employee_mapping lem ON le.employee_number = lem.locosoft_id
JOIN employees e ON lem.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND ac.reason IN ('Url', 'BUr')
  AND EXTRACT(YEAR FROM ac.date) IN (2024, 2025)
GROUP BY EXTRACT(YEAR FROM ac.date)
ORDER BY jahr;

-- 3. Vergleich: Portal 2025 vs Locosoft 2024+2025
SELECT 
    'Portal 2025' as quelle,
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
    'Locosoft 2024' as quelle,
    COUNT(*) FILTER (WHERE ac.day_contingent >= 1.0) as volle_tage,
    COUNT(*) FILTER (WHERE ac.day_contingent < 1.0 AND ac.day_contingent > 0) as halbe_tage,
    COALESCE(SUM(ac.day_contingent), 0) as tage_gesamt
FROM loco_absence_calendar ac
JOIN loco_employees le ON ac.employee_number = le.employee_number AND le.is_latest_record = true
JOIN ldap_employee_mapping lem ON le.employee_number = lem.locosoft_id
JOIN employees e ON lem.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND EXTRACT(YEAR FROM ac.date) = 2024
  AND ac.reason IN ('Url', 'BUr')
UNION ALL
SELECT 
    'Locosoft 2025' as quelle,
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

-- 4. Prüfe ob Portal-Buchungen falsche Jahres-Datierung haben
SELECT 
    vb.booking_date,
    vb.day_part,
    vb.status,
    vb.created_at,
    CASE WHEN vb.day_part = 'full' THEN 1.0 ELSE 0.5 END as tage
FROM vacation_bookings vb
JOIN employees e ON vb.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND vb.status = 'approved'
ORDER BY vb.booking_date;

