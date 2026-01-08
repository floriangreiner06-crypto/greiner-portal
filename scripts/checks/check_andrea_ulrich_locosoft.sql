-- Prüfe Andrea & Ulrich in Locosoft
-- TAG 167: Haben exit_date, sollten inaktiv sein

-- 1. In Locosoft prüfen
SELECT 
    eh.employee_number,
    eh.name,
    eh.employment_date,
    eh.leave_date,
    eh.termination_date,
    CASE 
        WHEN eh.leave_date IS NULL THEN 'Aktiv'
        WHEN eh.leave_date > CURRENT_DATE THEN 'Zukünftig ausgeschieden'
        ELSE 'Ausgeschieden'
    END as status
FROM employees_history eh
WHERE eh.is_latest_record = true
  AND (
    LOWER(eh.name) LIKE '%andrea%pfeffer%'
    OR LOWER(eh.name) LIKE '%pfeffer%andrea%'
    OR LOWER(eh.name) LIKE '%michael%ulrich%'
    OR LOWER(eh.name) LIKE '%ulrich%michael%'
  )
ORDER BY eh.employee_number;

-- 2. Im Portal prüfen
SELECT 
    e.id,
    e.first_name || ' ' || e.last_name as name,
    e.aktiv,
    e.exit_date,
    e.locosoft_id
FROM employees e
WHERE (e.first_name LIKE '%Andrea%' AND e.last_name LIKE '%Pfeffer%')
   OR (e.first_name LIKE '%Michael%' AND e.last_name LIKE '%Ulrich%');

