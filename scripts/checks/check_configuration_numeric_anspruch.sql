-- Prüfe configuration_numeric für Urlaubsansprüche
-- TAG 167: J.Url.ges. könnte hier gespeichert sein

-- 1. Alle Einträge die "urlaub" oder "vacation" enthalten
SELECT * FROM configuration_numeric 
WHERE name LIKE '%urlaub%' OR name LIKE '%vacation%' OR name LIKE '%anspruch%'
ORDER BY name
LIMIT 50;

-- 2. Prüfe ob es employee-spezifische Konfigurationen gibt
SELECT DISTINCT name 
FROM configuration_numeric 
WHERE name LIKE '%employee%' OR name LIKE '%mitarbeiter%'
ORDER BY name
LIMIT 50;

-- 3. Prüfe alle configuration_numeric Spalten
SELECT column_name, data_type 
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'configuration_numeric'
ORDER BY column_name;

