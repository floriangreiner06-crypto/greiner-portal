-- Prüfe Aleyna Irep 05.01.2026 in Locosoft
-- TAG 167: Diskrepanz zwischen DRIVE (Schulung) und Locosoft (Krankheit)

-- 1. Locosoft: absence_calendar für Aleyna am 05.01.2026
SELECT 
    'Locosoft' as quelle,
    ac.date,
    ac.reason,
    ac.day_contingent,
    ac.employee_number
FROM absence_calendar ac
WHERE ac.employee_number = (
    SELECT employee_number 
    FROM employees_history 
    WHERE (first_name LIKE '%Aleyna%' OR last_name LIKE '%Irep%')
      AND is_latest_record = true
    LIMIT 1
)
  AND ac.date = '2026-01-05'
ORDER BY ac.date;

-- 2. Prüfe alle Buchungen von Aleyna im Januar 2026 in Locosoft
SELECT 
    'Locosoft Alle Jan' as quelle,
    ac.date,
    ac.reason,
    ac.day_contingent
FROM absence_calendar ac
WHERE ac.employee_number = (
    SELECT employee_number 
    FROM employees_history 
    WHERE (first_name LIKE '%Aleyna%' OR last_name LIKE '%Irep%')
      AND is_latest_record = true
    LIMIT 1
)
  AND ac.date >= '2026-01-01'
  AND ac.date < '2026-02-01'
ORDER BY ac.date;

