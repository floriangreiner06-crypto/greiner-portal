-- Prüfe Andrea Pfeffer und Michael Ulrich
-- TAG 167: Sollten ausgeschieden sein

SELECT 
    id,
    first_name || ' ' || last_name as name,
    aktiv,
    exit_date
FROM employees
WHERE (first_name LIKE '%Andrea%' AND last_name LIKE '%Pfeffer%')
   OR (first_name LIKE '%Michael%' AND last_name LIKE '%Ulrich%');

