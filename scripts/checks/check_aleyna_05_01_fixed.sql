-- Prüfe Aleyna Irep 05.01.2026
-- TAG 167: Diskrepanz zwischen DRIVE (Schulung) und Locosoft (Krankheit)

-- 1. DRIVE: vacation_bookings für Aleyna am 05.01.2026
SELECT 
    'DRIVE' as quelle,
    vb.id,
    vb.employee_id,
    e.first_name || ' ' || e.last_name as name,
    vb.booking_date,
    vb.status,
    vt.name as vacation_type,
    vb.day_part,
    vb.created_at,
    vb.updated_at
FROM vacation_bookings vb
JOIN employees e ON vb.employee_id = e.id
LEFT JOIN vacation_types vt ON vb.vacation_type_id = vt.id
WHERE (e.first_name LIKE '%Aleyna%' OR e.last_name LIKE '%Irep%')
  AND vb.booking_date = '2026-01-05'
ORDER BY vb.booking_date;

-- 2. Prüfe alle Buchungen von Aleyna im Januar 2026
SELECT 
    'DRIVE Alle Jan' as quelle,
    vb.booking_date,
    vt.name as vacation_type,
    vb.status,
    vb.day_part
FROM vacation_bookings vb
JOIN employees e ON vb.employee_id = e.id
LEFT JOIN vacation_types vt ON vb.vacation_type_id = vt.id
WHERE (e.first_name LIKE '%Aleyna%' OR e.last_name LIKE '%Irep%')
  AND vb.booking_date >= '2026-01-01'
  AND vb.booking_date < '2026-02-01'
ORDER BY vb.booking_date;

