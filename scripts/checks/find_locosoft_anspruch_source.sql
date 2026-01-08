-- Finde wo in Locosoft der Jahresurlaubsanspruch (J.Url.ges.) gespeichert ist
-- TAG 167: Edith hat 39 Tage, muss aus Locosoft importiert werden

-- 1. Prüfe alle Tabellen die "jahr" oder "year" enthalten
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND (table_name LIKE '%jahr%' OR table_name LIKE '%year%' OR table_name LIKE '%calendar%')
ORDER BY table_name;

-- 2. Prüfe year_calendar (könnte Jahresansprüche enthalten)
SELECT column_name, data_type 
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'year_calendar'
ORDER BY column_name;

-- 3. Prüfe ob absence_calendar eine Spalte für Jahresanspruch hat
SELECT column_name, data_type 
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'absence_calendar'
ORDER BY column_name;

-- 4. Prüfe configuration_numeric (könnte Standard-Ansprüche enthalten)
SELECT * FROM configuration_numeric 
WHERE name LIKE '%urlaub%' OR name LIKE '%vacation%' OR name LIKE '%anspruch%'
LIMIT 20;

-- 5. Prüfe ob es eine Tabelle für Mitarbeiter-Verträge gibt
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND (table_name LIKE '%contract%' OR table_name LIKE '%vertrag%' OR table_name LIKE '%employee%')
ORDER BY table_name;

