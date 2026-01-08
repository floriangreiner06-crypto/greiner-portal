-- Prüfe View, API und Frontend-Daten
-- TAG 167: Falsche Ansprüche und fehlende Resturlaub-Anzeige

-- 1. View 2026 Daten (Edith & Florian)
SELECT 
    employee_id,
    name,
    anspruch,
    verbraucht,
    geplant,
    resturlaub
FROM v_vacation_balance_2026
WHERE name LIKE '%Edith%' OR name LIKE '%Florian%'
ORDER BY name;

-- 2. Prüfe ob View korrekt ist (PostgreSQL-Syntax)
SELECT 
    view_definition
FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name = 'v_vacation_balance_2026';

-- 3. Prüfe ob es SQLite-Syntax gibt (strftime, date(), aktiv=1)
SELECT 
    CASE 
        WHEN view_definition LIKE '%strftime%' THEN 'SQLite-Syntax gefunden: strftime'
        WHEN view_definition LIKE '%date(%' THEN 'SQLite-Syntax gefunden: date()'
        WHEN view_definition LIKE '%aktiv = 1%' THEN 'SQLite-Syntax gefunden: aktiv=1'
        ELSE 'OK - PostgreSQL-Syntax'
    END as syntax_check
FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name = 'v_vacation_balance_2026';

