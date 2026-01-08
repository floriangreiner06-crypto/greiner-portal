-- Detaillierte Prüfung Edith Egner
-- TAG 167: Warum zeigt sie -3 Tage?

-- 1. Kompletter Anspruch (alle Komponenten)
SELECT 
    e.id,
    e.first_name || ' ' || e.last_name as name,
    ve.total_days,
    ve.carried_over,
    ve.added_manually,
    (ve.total_days + COALESCE(ve.carried_over, 0) + COALESCE(ve.added_manually, 0)) as anspruch_gesamt
FROM employees e
LEFT JOIN vacation_entitlements ve ON e.id = ve.employee_id AND ve.year = 2025
WHERE e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%';

-- 2. Alle Buchungen 2025 (detailliert)
SELECT 
    vb.booking_date,
    vb.day_part,
    vb.status,
    vt.name as vacation_type,
    CASE WHEN vb.day_part = 'full' THEN 1.0 ELSE 0.5 END as tage,
    vb.comment
FROM vacation_bookings vb
LEFT JOIN vacation_types vt ON vb.vacation_type_id = vt.id
JOIN employees e ON vb.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND EXTRACT(YEAR FROM vb.booking_date) = 2025
ORDER BY vb.booking_date, vb.status;

-- 3. Summe nach Status
SELECT 
    vb.status,
    COUNT(*) FILTER (WHERE vb.day_part = 'full') as volle_tage,
    COUNT(*) FILTER (WHERE vb.day_part = 'half') as halbe_tage,
    (COUNT(*) FILTER (WHERE vb.day_part = 'full') * 1.0 +
     COUNT(*) FILTER (WHERE vb.day_part = 'half') * 0.5) as tage_gesamt
FROM vacation_bookings vb
JOIN employees e ON vb.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND EXTRACT(YEAR FROM vb.booking_date) = 2025
GROUP BY vb.status
ORDER BY vb.status;

-- 4. View vs. manuelle Berechnung
SELECT 
    'View' as quelle,
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
    'Manuell' as quelle,
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

-- 5. Prüfe ob es Buchungen aus Locosoft gibt die nicht im Portal sind
SELECT 
    ac.date,
    ac.day_contingent,
    ar.reason,
    ar.is_annual_vacation
FROM loco_absence_calendar ac
JOIN absence_reasons ar ON ac.reason = ar.id
JOIN loco_employees le ON ac.employee_number = le.employee_number AND le.is_latest_record = 1
JOIN ldap_employee_mapping lem ON le.employee_number = lem.locosoft_id
JOIN employees e ON lem.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND EXTRACT(YEAR FROM ac.date) = 2025
  AND ar.is_annual_vacation = true
ORDER BY ac.date;

