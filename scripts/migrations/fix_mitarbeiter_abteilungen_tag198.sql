-- ============================================================================
-- FIX: Mitarbeiter-Zuordnungen korrigieren (TAG 198)
-- ============================================================================
-- Korrigiert Abteilungs-Zuordnungen basierend auf User-Test-Ergebnissen
-- ============================================================================

-- 1. Silvia Eiglmaier → "Disposition"
UPDATE employees 
SET department_name = 'Disposition'
WHERE first_name = 'Silvia' AND last_name = 'Eiglmaier';

-- 2. Sandra Schimmer → "Fahrzeuge"
UPDATE employees 
SET department_name = 'Fahrzeuge'
WHERE first_name = 'Sandra' AND last_name = 'Schimmer';

-- 3. Stephan Wittmann → "Fahrzeuge"
UPDATE employees 
SET department_name = 'Fahrzeuge'
WHERE first_name = 'Stephan' AND last_name = 'Wittmann';

-- 4. Götz Klein → "Fahrzeuge"
UPDATE employees 
SET department_name = 'Fahrzeuge'
WHERE first_name = 'Götz' AND last_name = 'Klein';

-- 5. Daniel Thammer → "Werkstatt"
UPDATE employees 
SET department_name = 'Werkstatt'
WHERE first_name = 'Daniel' AND last_name = 'Thammer';

-- 6. Edith Egner → "Service"
UPDATE employees 
SET department_name = 'Service'
WHERE first_name = 'Edith' AND last_name = 'Egner';

-- Prüfe Ergebnisse
SELECT 
    id,
    first_name || ' ' || last_name as name,
    department_name,
    location
FROM employees
WHERE (first_name = 'Silvia' AND last_name = 'Eiglmaier')
   OR (first_name = 'Sandra' AND last_name = 'Schimmer')
   OR (first_name = 'Stephan' AND last_name = 'Wittmann')
   OR (first_name = 'Götz' AND last_name = 'Klein')
   OR (first_name = 'Daniel' AND last_name = 'Thammer')
   OR (first_name = 'Edith' AND last_name = 'Egner')
ORDER BY last_name, first_name;
