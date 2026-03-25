-- Margit Loibl: Anspruch 2026 in Locosoft 27/28, im Portal fälschlich 23
-- Korrektur auf 27 Tage (Standard Vollzeit)
UPDATE vacation_entitlements
SET total_days = 27, updated_at = CURRENT_TIMESTAMP
WHERE employee_id = (SELECT id FROM employees WHERE first_name = 'Margit' AND last_name = 'Loibl' AND aktiv = true LIMIT 1)
  AND year = 2026;
