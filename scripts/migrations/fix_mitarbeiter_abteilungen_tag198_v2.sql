-- TAG 198: Mitarbeiter-Abteilungs-Zuordnungen korrigieren (Verbesserung Urlaubsplaner2.docx)
-- Datum: 2026-01-19
-- 
-- Prüfung zeigt: Alle Abteilungen sind bereits korrekt zugeordnet!
-- 
-- Erwartete Zuordnungen:
-- - Silvia Eiglmaier → Disposition (bereits korrekt)
-- - Sandra Schimmer → Fahrzeuge (bereits korrekt)
-- - Stephan Wittmann → Fahrzeuge (bereits korrekt)
-- - Götz Klein → Fahrzeuge (bereits korrekt)
-- - Daniel Thammer → Werkstatt (bereits korrekt)
-- - Edith Egner → Service (bereits korrekt)
--
-- Status: ✅ Alle Zuordnungen sind bereits korrekt - keine Änderung nötig

-- Prüfung der aktuellen Zuordnungen:
SELECT 
    id,
    first_name || ' ' || last_name as name,
    department_name as aktuelle_abteilung,
    CASE 
        WHEN first_name ILIKE 'Silvia' AND last_name ILIKE 'Eiglmaier' THEN 'Disposition'
        WHEN first_name ILIKE 'Sandra' AND last_name ILIKE 'Schimmer' THEN 'Fahrzeuge'
        WHEN first_name ILIKE 'Stephan' AND last_name ILIKE 'Wittmann' THEN 'Fahrzeuge'
        WHEN first_name ILIKE 'Götz' AND last_name ILIKE 'Klein' THEN 'Fahrzeuge'
        WHEN first_name ILIKE 'Daniel' AND last_name ILIKE 'Thammer' THEN 'Werkstatt'
        WHEN first_name ILIKE 'Edith' AND last_name ILIKE 'Egner' THEN 'Service'
        ELSE 'N/A'
    END as erwartete_abteilung
FROM employees
WHERE (first_name ILIKE 'Silvia' AND last_name ILIKE 'Eiglmaier')
   OR (first_name ILIKE 'Sandra' AND last_name ILIKE 'Schimmer')
   OR (first_name ILIKE 'Stephan' AND last_name ILIKE 'Wittmann')
   OR (first_name ILIKE 'Götz' AND last_name ILIKE 'Klein')
   OR (first_name ILIKE 'Daniel' AND last_name ILIKE 'Thammer')
   OR (first_name ILIKE 'Edith' AND last_name ILIKE 'Egner')
ORDER BY last_name;

-- Falls doch Korrekturen nötig sind, können folgende UPDATEs verwendet werden:
-- (Aktuell nicht nötig, da alle Zuordnungen korrekt sind)

-- UPDATE employees SET department_name = 'Disposition' WHERE first_name ILIKE 'Silvia' AND last_name ILIKE 'Eiglmaier';
-- UPDATE employees SET department_name = 'Fahrzeuge' WHERE first_name ILIKE 'Sandra' AND last_name ILIKE 'Schimmer';
-- UPDATE employees SET department_name = 'Fahrzeuge' WHERE first_name ILIKE 'Stephan' AND last_name ILIKE 'Wittmann';
-- UPDATE employees SET department_name = 'Fahrzeuge' WHERE first_name ILIKE 'Götz' AND last_name ILIKE 'Klein';
-- UPDATE employees SET department_name = 'Werkstatt' WHERE first_name ILIKE 'Daniel' AND last_name ILIKE 'Thammer';
-- UPDATE employees SET department_name = 'Service' WHERE first_name ILIKE 'Edith' AND last_name ILIKE 'Egner';
