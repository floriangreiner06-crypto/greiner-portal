-- Urlaubssperren: optionale Mitarbeiter-spezifische Sperren (statt nur Abteilung)
-- Führt zu: department_name NULL erlaubt, employee_ids Komma-getrennt (z.B. "1,2,3")

ALTER TABLE vacation_blocks ADD COLUMN IF NOT EXISTS employee_ids TEXT;
ALTER TABLE vacation_blocks ALTER COLUMN department_name DROP NOT NULL;
COMMENT ON COLUMN vacation_blocks.employee_ids IS 'Komma-getrennte employee_ids wenn Sperre nur für bestimmte MA gilt; dann department_name NULL';
