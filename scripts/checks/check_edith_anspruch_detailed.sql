-- Detaillierte Prüfe Edith's Anspruch-Berechnung
-- TAG 167: Locosoft zeigt 39 Tage, Portal berechnet 27

-- 1. Portal-Daten 2025
SELECT 
    'Portal 2025' as quelle,
    total_days,
    carried_over,
    added_manually,
    (total_days + COALESCE(carried_over, 0) + COALESCE(added_manually, 0)) as anspruch_gesamt
FROM vacation_entitlements
WHERE employee_id = 11 AND year = 2025;

-- 2. Locosoft-Verbrauch 2025
SELECT 
    'Locosoft Verbrauch 2025' as quelle,
    COUNT(*) as anzahl,
    SUM(day_contingent) as tage
FROM absence_calendar
WHERE employee_number = 4003
  AND EXTRACT(YEAR FROM date) = 2025
  AND reason IN ('Url', 'BUr');

-- 3. Berechnung:
-- Anspruch 2025 = 32 Tage (27 + 5)
-- Verbraucht 2025 = 35 Tage
-- Resturlaub 2025 = 32 - 35 = -3 Tage (negativ!)

-- 4. ABER: Locosoft zeigt 39 Tage für 2026
-- Das bedeutet: Standard 2026 (27?) + Resturlaub 2025 (12?) = 39
-- Oder: Standard 2026 (30?) + Resturlaub 2025 (9?) = 39

-- 5. Prüfe ob Edith einen individuellen Standard-Anspruch hat
-- (z.B. in employees_history oder einer anderen Tabelle)
-- Oder ob der Resturlaub aus 2024 übernommen wird

-- 6. Prüfe 2024 Daten
SELECT 
    'Locosoft 2024' as quelle,
    COUNT(*) as anzahl,
    SUM(day_contingent) as tage
FROM absence_calendar
WHERE employee_number = 4003
  AND EXTRACT(YEAR FROM date) = 2024
  AND reason IN ('Url', 'BUr');

-- 7. Mögliche Berechnung:
-- Standard 2024 = 27 Tage
-- Verbraucht 2024 = 27 Tage (aus Query 6)
-- Resturlaub 2024 = 27 - 27 = 0 Tage
-- 
-- Standard 2025 = 27 Tage
-- Resturlaub 2024 = 0 Tage
-- Anspruch 2025 = 27 + 0 = 27 Tage
-- ABER: Portal zeigt 32 Tage (27 + 5 added_manually)
-- 
-- Vielleicht: Standard 2026 = 27 Tage
-- Resturlaub 2025 = 12 Tage (wie kommt das?)
-- Gesamt = 39 Tage

