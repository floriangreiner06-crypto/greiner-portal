-- Prüfe 2026 Urlaubsansprüche
-- TAG 167: Wir sind in 2026!

-- 1. Existiert View für 2026?
SELECT EXISTS (
    SELECT FROM information_schema.views 
    WHERE table_schema = 'public' 
    AND table_name = 'v_vacation_balance_2026'
) as has_view_2026;

-- 2. Ansprüche 2026
SELECT 
    COUNT(*) as anzahl,
    SUM(total_days) as gesamt_tage,
    SUM(carried_over) as gesamt_uebertrag,
    SUM(added_manually) as gesamt_manuell
FROM vacation_entitlements
WHERE year = 2026;

-- 3. Mitarbeiter OHNE Anspruch 2026
SELECT 
    e.id,
    e.first_name || ' ' || e.last_name as name,
    e.aktiv
FROM employees e
WHERE e.aktiv = true
  AND e.id NOT IN (SELECT employee_id FROM vacation_entitlements WHERE year = 2026)
ORDER BY e.last_name, e.first_name
LIMIT 20;

-- 4. Vergleich 2025 vs 2026
SELECT 
    year,
    COUNT(*) as anzahl_mitarbeiter,
    SUM(total_days) as gesamt_tage,
    SUM(carried_over) as gesamt_uebertrag,
    SUM(added_manually) as gesamt_manuell
FROM vacation_entitlements
WHERE year IN (2025, 2026)
GROUP BY year
ORDER BY year;

-- 5. Prüfe ob View 2026 existiert und funktioniert
SELECT 
    employee_id,
    name,
    anspruch,
    verbraucht,
    geplant,
    resturlaub
FROM v_vacation_balance_2026
LIMIT 5;

