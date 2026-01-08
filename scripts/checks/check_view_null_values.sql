-- Prüfe View auf NULL-Werte
-- TAG 167: Falsche Ansprüche und fehlende Resturlaub-Anzeige

-- 1. Prüfe View 2026 auf NULL-Werte
SELECT 
    'View 2026' as view_name,
    COUNT(*) as total,
    COUNT(CASE WHEN anspruch IS NULL THEN 1 END) as anspruch_null,
    COUNT(CASE WHEN resturlaub IS NULL THEN 1 END) as resturlaub_null,
    COUNT(CASE WHEN verbraucht IS NULL THEN 1 END) as verbraucht_null,
    COUNT(CASE WHEN geplant IS NULL THEN 1 END) as geplant_null
FROM v_vacation_balance_2026;

-- 2. Prüfe View 2025 auf NULL-Werte
SELECT 
    'View 2025' as view_name,
    COUNT(*) as total,
    COUNT(CASE WHEN anspruch IS NULL THEN 1 END) as anspruch_null,
    COUNT(CASE WHEN resturlaub IS NULL THEN 1 END) as resturlaub_null,
    COUNT(CASE WHEN verbraucht IS NULL THEN 1 END) as verbraucht_null,
    COUNT(CASE WHEN geplant IS NULL THEN 1 END) as geplant_null
FROM v_vacation_balance_2025;

-- 3. Prüfe Edith & Florian in View 2026
SELECT 
    employee_id,
    name,
    anspruch,
    verbraucht,
    geplant,
    resturlaub,
    CASE 
        WHEN anspruch IS NULL THEN 'NULL'
        WHEN resturlaub IS NULL THEN 'NULL'
        ELSE 'OK'
    END as status
FROM v_vacation_balance_2026
WHERE name LIKE '%Edith%' OR name LIKE '%Florian Greiner%'
ORDER BY name;

