-- Fix: Andrea Pfeffer und Michael Ulrich als inaktiv markieren
-- TAG 167: Haben exit_date in Locosoft, sollten inaktiv sein

-- 1. Andrea Pfeffer (ID=77, Locosoft=1034, leave_date=2025-09-16)
UPDATE employees
SET 
    aktiv = false,
    exit_date = '2025-09-16'
WHERE id = 77;

-- 2. Michael Ulrich (ID=78, Locosoft=1035, leave_date=2024-07-29)
UPDATE employees
SET 
    aktiv = false,
    exit_date = '2024-07-29'
WHERE id = 78;

-- 3. Prüfen
SELECT 
    id,
    first_name || ' ' || last_name as name,
    aktiv,
    exit_date,
    locosoft_id
FROM employees
WHERE id IN (77, 78);

