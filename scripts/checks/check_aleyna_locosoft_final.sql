-- Prüfe Aleyna Irep 05.01.2026 in Locosoft
-- TAG 167: Diskrepanz zwischen DRIVE (Schulung) und Locosoft (Krankheit)
-- Aleyna's employee_number: 4001 (aus vorheriger Query)

SELECT 
    'Locosoft 05.01' as quelle,
    ac.date,
    ac.reason,
    ac.day_contingent,
    ac.employee_number
FROM absence_calendar ac
WHERE ac.employee_number = 4001
  AND ac.date = '2026-01-05'
ORDER BY ac.date;

-- Alle Buchungen von Aleyna im Januar 2026
SELECT 
    'Locosoft Alle Jan' as quelle,
    ac.date,
    ac.reason,
    ac.day_contingent
FROM absence_calendar ac
WHERE ac.employee_number = 4001
  AND ac.date >= '2026-01-01'
  AND ac.date < '2026-02-01'
ORDER BY ac.date;

