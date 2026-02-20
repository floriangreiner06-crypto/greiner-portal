-- Vertretungsregeln (Organigramm) – PostgreSQL
-- Wer vertritt wen; für Urlaubsgenehmigung und Abwesenheiten.
-- Ausführung: PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -f migrations/add_substitution_rules.sql

BEGIN;

CREATE TABLE IF NOT EXISTS substitution_rules (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    substitute_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 1,
    valid_from DATE DEFAULT NULL,
    valid_to DATE DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT NULL,
    CONSTRAINT chk_substitute_not_self CHECK (employee_id != substitute_id)
);

CREATE INDEX IF NOT EXISTS idx_substitution_rules_employee ON substitution_rules(employee_id);
CREATE INDEX IF NOT EXISTS idx_substitution_rules_substitute ON substitution_rules(substitute_id);

COMMENT ON TABLE substitution_rules IS 'Vertretungsregeln: Wer vertritt wen (Priorität, optional Zeitraum)';

COMMIT;
