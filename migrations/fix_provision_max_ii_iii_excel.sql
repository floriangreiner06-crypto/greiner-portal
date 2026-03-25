-- Max-Grenzen an Excel anpassen (Abrechnungen_0326 / Punzmann).
-- Excel: Vorführwagen-Block (II) = min 103, max 500; Gebrauchtwagen-Block (III) = min 103, max 300.
-- DRIVE hatte bisher II max 300, III max 500 (vertauscht).

UPDATE provision_config SET max_betrag = 500
WHERE kategorie = 'II_testwagen' AND (gueltig_bis IS NULL OR gueltig_bis >= '2024-01-01');

UPDATE provision_config SET max_betrag = 300
WHERE kategorie = 'III_gebrauchtwagen' AND (gueltig_bis IS NULL OR gueltig_bis >= '2024-01-01');
