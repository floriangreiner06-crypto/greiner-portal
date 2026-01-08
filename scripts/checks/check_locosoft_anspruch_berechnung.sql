-- Berechne Jahresanspruch (J.Url.ges.) wie Locosoft
-- TAG 167: J.Url.ges. = Standard-Anspruch + Resturlaub aus Vorjahr

-- Für Edith (4003):
-- 1. Standard-Anspruch 2026 (angenommen 27 Tage, könnte auch individuell sein)
-- 2. Resturlaub aus 2025 berechnen:
--    - Anspruch 2025 (Standard + carried_over + added_manually)
--    - Verbraucht 2025 (Summe aller Url/BUr)
--    - Resturlaub = Anspruch - Verbraucht

-- 1. Verbrauch 2025 für Edith
SELECT 
    'Verbraucht 2025' as typ,
    COUNT(*) as anzahl,
    SUM(day_contingent) as tage
FROM absence_calendar
WHERE employee_number = 4003
  AND EXTRACT(YEAR FROM date) = 2025
  AND reason IN ('Url', 'BUr');

-- 2. Prüfe ob es einen Standard-Anspruch gibt (vielleicht in configuration?)
-- Für jetzt nehmen wir 27 Tage als Standard an

-- 3. Berechne Resturlaub 2025:
-- Standard-Anspruch 2025 = 27 Tage (angenommen)
-- Verbraucht 2025 = 35 Tage (aus Query 1)
-- Resturlaub 2025 = 27 - 35 = -8 Tage (negativ!)

-- ABER: In Locosoft zeigt es 39 Tage für 2026
-- Das bedeutet: Standard 2026 (27) + Resturlaub 2025 (12) = 39
-- Also: Resturlaub 2025 muss 12 Tage sein, nicht -8

-- 4. Prüfe ob Edith einen individuellen Anspruch hat (z.B. 30 oder 32 Tage)
-- Oder ob der Resturlaub anders berechnet wird

-- 5. Prüfe ob es Einträge gibt, die den Anspruch erhöhen (z.B. added_manually)
SELECT 
    'Alle Jahre' as typ,
    EXTRACT(YEAR FROM date) as jahr,
    COUNT(*) as anzahl,
    SUM(day_contingent) as tage
FROM absence_calendar
WHERE employee_number = 4003
  AND reason IN ('Url', 'BUr')
GROUP BY EXTRACT(YEAR FROM date)
ORDER BY jahr;

