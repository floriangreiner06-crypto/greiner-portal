-- Prüfe Aleyna's vacation_types und Mapping
-- TAG 167: Diskrepanz zwischen DRIVE (Schulung) und Locosoft (Krankheit)

-- 1. Prüfe vacation_types Tabelle
SELECT 
    'vacation_types' as quelle,
    id,
    name
FROM vacation_types
ORDER BY id;

-- 2. Prüfe Aleyna's Buchung am 05.01.2026
SELECT 
    'Aleyna 05.01' as quelle,
    vb.id,
    vb.employee_id,
    vb.booking_date,
    vb.vacation_type_id,
    vt.name as vacation_type_name,
    vb.status
FROM vacation_bookings vb
LEFT JOIN vacation_types vt ON vb.vacation_type_id = vt.id
WHERE vb.employee_id = 26
  AND vb.booking_date = '2026-01-05';

