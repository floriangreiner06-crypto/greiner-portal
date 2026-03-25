-- Max. Abwesenheit pro Abteilung und Standort (Vertretung/Abwesenheit)
-- Default 50% (nur planbare Abwesenheit: Urlaub + Schulung; Krankheit nicht planbar)
-- Ausführung: PGPASSWORD=<PASSWORT> psql -h 127.0.0.1 -U drive_user -d drive_portal -f migrations/add_department_absence_limits.sql

BEGIN;

CREATE TABLE IF NOT EXISTS department_absence_limits (
    id SERIAL PRIMARY KEY,
    department_name TEXT NOT NULL,
    location TEXT NOT NULL,
    max_absence_percent INTEGER NOT NULL DEFAULT 50 CHECK (max_absence_percent >= 1 AND max_absence_percent <= 100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT,
    UNIQUE(department_name, location)
);

CREATE INDEX IF NOT EXISTS idx_department_absence_limits_lookup ON department_absence_limits(department_name, location);

COMMENT ON TABLE department_absence_limits IS 'Max. Abwesenheit in % pro Abteilung und Standort (nur Urlaub+Schulung; Krankheit nicht planbar). Default 50%.';

COMMIT;
