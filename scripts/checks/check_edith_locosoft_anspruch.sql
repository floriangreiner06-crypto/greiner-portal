-- Prüfe Edith's Urlaubsanspruch in Locosoft
-- TAG 167: J.Url.ges. = 39 Tage

-- 1. employees_history für Edith (4003)
SELECT 
    employee_number,
    name,
    employment_date,
    leave_date,
    subsidiary
FROM employees_history
WHERE employee_number = 4003
  AND is_latest_record = true;

-- 2. Prüfe ob es eine Tabelle für Urlaubsansprüche gibt
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND (table_name LIKE '%urlaub%' OR table_name LIKE '%vacation%' OR table_name LIKE '%absence%')
ORDER BY table_name;

-- 3. Prüfe absence_calendar für Edith 2026 (J.Url.ges. sollte 39 sein)
-- Das ist die Summe aller Url/BUr Einträge für 2026
SELECT 
    COUNT(*) as anzahl_urlaubstage,
    SUM(day_contingent) as gesamt_urlaub_2026
FROM absence_calendar
WHERE employee_number = 4003
  AND EXTRACT(YEAR FROM date) = 2026
  AND reason IN ('Url', 'BUr');

-- 4. Prüfe ob es eine Tabelle für Jahresansprüche gibt
SELECT 
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'employees_history'
  AND (column_name LIKE '%urlaub%' OR column_name LIKE '%vacation%' OR column_name LIKE '%anspruch%' OR column_name LIKE '%entitlement%')
ORDER BY column_name;

