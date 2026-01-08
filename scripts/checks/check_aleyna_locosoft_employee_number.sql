-- Prüfe Aleyna's employee_number in Locosoft
-- TAG 167: Diskrepanz zwischen DRIVE (Schulung) und Locosoft (Krankheit)

-- 1. Finde Aleyna in employees_history
SELECT 
    'Locosoft employees_history' as quelle,
    employee_number,
    first_name,
    last_name,
    is_latest_record
FROM employees_history
WHERE first_name LIKE '%Aleyna%' OR last_name LIKE '%Irep%'
ORDER BY is_latest_record DESC, employee_number;

-- 2. Prüfe alle Einträge für employee_number 1025 im Januar 2026
SELECT 
    'Locosoft 1025 Jan' as quelle,
    ac.date,
    ac.reason,
    ac.day_contingent
FROM absence_calendar ac
WHERE ac.employee_number = 1025
  AND ac.date >= '2026-01-01'
  AND ac.date < '2026-02-01'
ORDER BY ac.date;

