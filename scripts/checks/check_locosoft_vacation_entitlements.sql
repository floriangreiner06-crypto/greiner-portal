-- Prüfe wo Urlaubsansprüche in Locosoft gespeichert sind
-- TAG 167: Edith hat 39 Tage, nicht 27

-- 1. Prüfe absence_reasons (könnte Jahresansprüche enthalten)
SELECT * FROM absence_reasons WHERE is_annual_vacation = true LIMIT 10;

-- 2. Prüfe ob es eine Tabelle für Jahresansprüche gibt
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND (table_name LIKE '%jahr%' OR table_name LIKE '%year%' OR table_name LIKE '%anspruch%')
ORDER BY table_name;

-- 3. Prüfe employees_history Spalten (könnte vacation_days enthalten)
SELECT column_name, data_type 
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'employees_history'
ORDER BY column_name;

-- 4. Prüfe ob es eine Konfigurationstabelle gibt
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND (table_name LIKE '%config%' OR table_name LIKE '%setting%' OR table_name LIKE '%parameter%')
ORDER BY table_name;

