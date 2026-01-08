-- Test Edith nach View-Fix
SELECT employee_id, name, anspruch, verbraucht, geplant, resturlaub 
FROM v_vacation_balance_2025 
WHERE name LIKE '%Edith%';

