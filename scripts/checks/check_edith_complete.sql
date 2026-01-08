-- Komplette Analyse Edith Egner
-- TAG 167: Warum -3 Tage?

-- 1. Alle Abwesenheiten aus Locosoft (alle Typen)
SELECT 
    ac.date,
    ac.day_contingent,
    ac.reason,
    ac.type,
    CASE 
        WHEN ac.reason IN ('Url', 'BUr') THEN 'Urlaub'
        WHEN ac.reason = 'ZA.' THEN 'Zeitausgleich'
        WHEN ac.reason = 'Krn' THEN 'Krank'
        ELSE 'Sonstige'
    END as typ_kategorie
FROM loco_absence_calendar ac
JOIN loco_employees le ON ac.employee_number = le.employee_number AND le.is_latest_record = true
JOIN ldap_employee_mapping lem ON le.employee_number = lem.locosoft_id
JOIN employees e ON lem.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND EXTRACT(YEAR FROM ac.date) = 2025
ORDER BY ac.date, ac.reason;

-- 2. Summe nach Typ
SELECT 
    CASE 
        WHEN ac.reason IN ('Url', 'BUr') THEN 'Urlaub'
        WHEN ac.reason = 'ZA.' THEN 'Zeitausgleich'
        WHEN ac.reason = 'Krn' THEN 'Krank'
        ELSE 'Sonstige'
    END as typ_kategorie,
    COUNT(*) as anzahl_tage,
    SUM(ac.day_contingent) as tage_gesamt
FROM loco_absence_calendar ac
JOIN loco_employees le ON ac.employee_number = le.employee_number AND le.is_latest_record = true
JOIN ldap_employee_mapping lem ON le.employee_number = lem.locosoft_id
JOIN employees e ON lem.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND EXTRACT(YEAR FROM ac.date) = 2025
GROUP BY typ_kategorie
ORDER BY typ_kategorie;

-- 3. Prüfe ob es Buchungen aus anderen Jahren gibt die mitgezählt werden
SELECT 
    EXTRACT(YEAR FROM vb.booking_date) as jahr,
    COUNT(*) FILTER (WHERE vb.day_part = 'full') as volle_tage,
    COUNT(*) FILTER (WHERE vb.day_part = 'half') as halbe_tage,
    (COUNT(*) FILTER (WHERE vb.day_part = 'full') * 1.0 +
     COUNT(*) FILTER (WHERE vb.day_part = 'half') * 0.5) as tage_gesamt
FROM vacation_bookings vb
JOIN employees e ON vb.employee_id = e.id
WHERE (e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%')
  AND vb.status = 'approved'
GROUP BY EXTRACT(YEAR FROM vb.booking_date)
ORDER BY jahr;

-- 4. Aktuelle Balance mit Details
SELECT 
    'View' as quelle,
    employee_id,
    name,
    anspruch,
    verbraucht,
    geplant,
    resturlaub,
    (anspruch - verbraucht - geplant) as resturlaub_berechnet
FROM v_vacation_balance_2025 
WHERE name LIKE '%Edith%' OR name LIKE '%Egner%';

-- 5. Prüfe ob Anspruch korrekt ist (sollte 27 Standard sein?)
SELECT 
    e.id,
    e.first_name || ' ' || e.last_name as name,
    ve.year,
    ve.total_days,
    ve.carried_over,
    ve.added_manually,
    (ve.total_days + COALESCE(ve.carried_over, 0) + COALESCE(ve.added_manually, 0)) as anspruch_gesamt,
    e.vacation_days_per_year,
    e.vacation_entitlement
FROM employees e
LEFT JOIN vacation_entitlements ve ON e.id = ve.employee_id AND ve.year = 2025
WHERE e.first_name LIKE '%Edith%' OR e.last_name LIKE '%Egner%';

