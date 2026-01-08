-- Prüfe View 2025 auf SQLite-Syntax
SELECT 
    CASE 
        WHEN view_definition LIKE '%strftime%' THEN 'SQLite-Syntax: strftime'
        WHEN view_definition LIKE '%date(%' THEN 'SQLite-Syntax: date()'
        WHEN view_definition LIKE '%aktiv = 1%' THEN 'SQLite-Syntax: aktiv=1'
        WHEN view_definition LIKE '%aktiv = true%' THEN 'PostgreSQL: aktiv=true'
        ELSE 'Unbekannt'
    END as syntax_check,
    LENGTH(view_definition) as view_length
FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name = 'v_vacation_balance_2025';

-- Prüfe View 2025 Daten (Edith)
SELECT 
    employee_id,
    name,
    anspruch,
    verbraucht,
    geplant,
    resturlaub
FROM v_vacation_balance_2025
WHERE name LIKE '%Edith%'
LIMIT 1;

