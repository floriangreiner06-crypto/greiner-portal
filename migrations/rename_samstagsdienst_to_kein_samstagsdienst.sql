-- Umbenennung: "Samstagsdienst (Info)" → "kein Samstagsdienst (Info)" (nur Anzeigename, keine Logik-Änderung)
-- Urlaubstage werden weiterhin nicht abgezogen (deduct_from_contingent = 0).
UPDATE vacation_types
SET name = 'kein Samstagsdienst'
WHERE id = 13;
