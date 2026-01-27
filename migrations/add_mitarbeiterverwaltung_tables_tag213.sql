-- Migration: Mitarbeiterverwaltung nach Muster "Digitale Personalakte"
-- TAG 213: Umfassende Mitarbeiterverwaltung mit Teilzeit, Sonderurlaub, etc.
-- Datum: 2026-01-27

BEGIN;

-- ============================================================================
-- 1. ERWEITERUNG employees TABELLE
-- ============================================================================

-- Geschlecht, Titel, Anrede
ALTER TABLE employees 
ADD COLUMN IF NOT EXISTS gender VARCHAR(20) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS title VARCHAR(50) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS salutation TEXT DEFAULT NULL;

-- Kontaktdaten (privat)
ALTER TABLE employees 
ADD COLUMN IF NOT EXISTS private_street TEXT DEFAULT NULL,
ADD COLUMN IF NOT EXISTS private_city TEXT DEFAULT NULL,
ADD COLUMN IF NOT EXISTS private_postal_code VARCHAR(10) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS private_country VARCHAR(100) DEFAULT 'Deutschland',
ADD COLUMN IF NOT EXISTS private_phone VARCHAR(50) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS private_mobile VARCHAR(50) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS private_fax VARCHAR(50) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS private_email TEXT DEFAULT NULL;

-- Kontaktdaten (Firma)
ALTER TABLE employees 
ADD COLUMN IF NOT EXISTS company_phone VARCHAR(50) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS company_mobile VARCHAR(50) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS company_fax VARCHAR(50) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS company_email TEXT DEFAULT NULL,
ADD COLUMN IF NOT EXISTS personal_nr_1 VARCHAR(50) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS personal_nr_2 VARCHAR(50) DEFAULT NULL;

-- Vertragsdaten
ALTER TABLE employees 
ADD COLUMN IF NOT EXISTS company VARCHAR(100) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS hired_as VARCHAR(100) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS activity VARCHAR(100) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS probation_end DATE DEFAULT NULL,
ADD COLUMN IF NOT EXISTS limited_until DATE DEFAULT NULL,
ADD COLUMN IF NOT EXISTS notice_period_employer VARCHAR(50) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS notice_period_employee VARCHAR(50) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS country VARCHAR(100) DEFAULT 'Deutschland',
ADD COLUMN IF NOT EXISTS federal_state VARCHAR(100) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS deactivate_after_exit BOOLEAN DEFAULT false;

-- ============================================================================
-- 2. ARBEITSZEITMODELLE (Teilzeit, Vollzeit, etc.)
-- ============================================================================

CREATE TABLE IF NOT EXISTS employee_working_time_models (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE DEFAULT NULL,  -- NULL = aktuell gültig
    hours_per_week DECIMAL(5,2) NOT NULL,
    working_days_per_week INTEGER DEFAULT 5,
    weekly_hours DECIMAL(5,2) DEFAULT NULL,  -- Alternative: Stunden pro Woche als Text
    hourly_wage DECIMAL(10,2) DEFAULT NULL,
    gross_wage DECIMAL(10,2) DEFAULT NULL,
    description TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_dates CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE INDEX IF NOT EXISTS idx_working_time_models_employee ON employee_working_time_models(employee_id);
CREATE INDEX IF NOT EXISTS idx_working_time_models_dates ON employee_working_time_models(start_date, end_date);

-- ============================================================================
-- 3. AUSNAHMEN DER ARBEITSZEITMODELLE (Sonderurlaub, etc.)
-- ============================================================================

CREATE TABLE IF NOT EXISTS employee_working_time_exceptions (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    from_date DATE NOT NULL,
    to_date DATE NOT NULL,
    exception_type VARCHAR(50) NOT NULL,  -- 'sonderurlaub', 'elternzeit', 'sabbatical', etc.
    description TEXT DEFAULT NULL,
    affects_vacation_entitlement BOOLEAN DEFAULT false,  -- Beeinflusst Urlaubsanspruch?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_exception_dates CHECK (to_date >= from_date)
);

CREATE INDEX IF NOT EXISTS idx_working_time_exceptions_employee ON employee_working_time_exceptions(employee_id);
CREATE INDEX IF NOT EXISTS idx_working_time_exceptions_dates ON employee_working_time_exceptions(from_date, to_date);

-- ============================================================================
-- 4. URLAUBSPLANER-EINSTELLUNGEN PRO MITARBEITER
-- ============================================================================

CREATE TABLE IF NOT EXISTS employee_vacation_settings (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL UNIQUE REFERENCES employees(id) ON DELETE CASCADE,
    show_in_planner BOOLEAN DEFAULT true,
    show_birthday BOOLEAN DEFAULT true,
    vacation_expires BOOLEAN DEFAULT false,  -- Urlaub verfällt nicht
    max_carry_over DECIMAL(5,1) DEFAULT 999.0,
    weekend_limit INTEGER DEFAULT 0,  -- Url. WE. Grenze
    max_vacation_length INTEGER DEFAULT 14,  -- Max. Urlaubslänge
    max_vacation_exit DECIMAL(5,1) DEFAULT 0.0,  -- Max. Urlaub (Austritt)
    calculation_method VARCHAR(50) DEFAULT 'standard',  -- 'standard', 'workdays', etc.
    valuation_lock DATE DEFAULT NULL,  -- Wertungssperre
    entry_from DATE DEFAULT NULL,  -- Eintragen von
    entry_until DATE DEFAULT NULL,  -- Eintragen bis
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vacation_settings_employee ON employee_vacation_settings(employee_id);

-- ============================================================================
-- 5. ZEITEN OHNE URLAUBSANSPRUCH
-- ============================================================================

CREATE TABLE IF NOT EXISTS employee_periods_without_vacation (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    from_date DATE NOT NULL,
    to_date DATE NOT NULL,
    period_type VARCHAR(50) NOT NULL,  -- 'elternzeit', 'unbezahlt', 'sabbatical', etc.
    description TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_period_dates CHECK (to_date >= from_date)
);

CREATE INDEX IF NOT EXISTS idx_periods_no_vacation_employee ON employee_periods_without_vacation(employee_id);
CREATE INDEX IF NOT EXISTS idx_periods_no_vacation_dates ON employee_periods_without_vacation(from_date, to_date);

-- ============================================================================
-- 6. TERMINKONTEN (Appointment Accounts)
-- ============================================================================

CREATE TABLE IF NOT EXISTS employee_appointment_accounts (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    appointment_type VARCHAR(100) NOT NULL,  -- Art des Terminkontos
    per_year DECIMAL(5,1) DEFAULT 0.0,  -- Pro Jahr
    account_balance DECIMAL(5,1) DEFAULT 0.0,  -- Konto
    max_per_week DECIMAL(5,1) DEFAULT NULL,  -- Max. Woche
    max_per_month DECIMAL(5,1) DEFAULT NULL,  -- Max. Monat
    description TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_appointment_accounts_employee ON employee_appointment_accounts(employee_id);

-- ============================================================================
-- 7. WORKFLOW-EINSTELLUNGEN (optional, für spätere Erweiterung)
-- ============================================================================

CREATE TABLE IF NOT EXISTS employee_vacation_workflows (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    workflow_type VARCHAR(50) NOT NULL,  -- 'urlaubstage', 'ausgleichstage'
    workflow_name VARCHAR(100) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vacation_workflows_employee ON employee_vacation_workflows(employee_id);

-- ============================================================================
-- 8. TRIGGER FÜR updated_at
-- ============================================================================

-- Trigger-Funktion
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger für employee_working_time_models
DROP TRIGGER IF EXISTS update_working_time_models_updated_at ON employee_working_time_models;
CREATE TRIGGER update_working_time_models_updated_at
    BEFORE UPDATE ON employee_working_time_models
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger für employee_working_time_exceptions
DROP TRIGGER IF EXISTS update_working_time_exceptions_updated_at ON employee_working_time_exceptions;
CREATE TRIGGER update_working_time_exceptions_updated_at
    BEFORE UPDATE ON employee_working_time_exceptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger für employee_vacation_settings
DROP TRIGGER IF EXISTS update_vacation_settings_updated_at ON employee_vacation_settings;
CREATE TRIGGER update_vacation_settings_updated_at
    BEFORE UPDATE ON employee_vacation_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger für employee_periods_without_vacation
DROP TRIGGER IF EXISTS update_periods_no_vacation_updated_at ON employee_periods_without_vacation;
CREATE TRIGGER update_periods_no_vacation_updated_at
    BEFORE UPDATE ON employee_periods_without_vacation
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger für employee_appointment_accounts
DROP TRIGGER IF EXISTS update_appointment_accounts_updated_at ON employee_appointment_accounts;
CREATE TRIGGER update_appointment_accounts_updated_at
    BEFORE UPDATE ON employee_appointment_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 9. KOMMENTARE FÜR DOKUMENTATION
-- ============================================================================

COMMENT ON TABLE employee_working_time_models IS 'Arbeitszeitmodelle pro Mitarbeiter (Teilzeit, Vollzeit, etc.)';
COMMENT ON TABLE employee_working_time_exceptions IS 'Ausnahmen der Arbeitszeitmodelle (Sonderurlaub, etc.)';
COMMENT ON TABLE employee_vacation_settings IS 'Urlaubsplaner-Einstellungen pro Mitarbeiter';
COMMENT ON TABLE employee_periods_without_vacation IS 'Zeiten ohne Urlaubsanspruch';
COMMENT ON TABLE employee_appointment_accounts IS 'Terminkonten (Appointment Accounts)';
COMMENT ON TABLE employee_vacation_workflows IS 'Workflow-Einstellungen für Urlaub';

COMMIT;

-- ============================================================================
-- MIGRATION ABGESCHLOSSEN
-- ============================================================================
