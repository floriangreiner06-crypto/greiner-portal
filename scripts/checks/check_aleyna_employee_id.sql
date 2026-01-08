-- Finde Aleyna's employee_number und employee_id
SELECT 
    'DRIVE' as quelle,
    e.id as employee_id,
    e.first_name || ' ' || e.last_name as name,
    e.locosoft_id
FROM employees e
WHERE e.first_name LIKE '%Aleyna%' OR e.last_name LIKE '%Irep%';

