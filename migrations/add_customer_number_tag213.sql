-- Migration: customer_number Feld hinzufügen
-- TAG 213: Erweiterung für Locosoft-Sync mit Adressdaten
-- Datum: 2026-01-27

BEGIN;

-- customer_number Feld hinzufügen
ALTER TABLE employees 
ADD COLUMN IF NOT EXISTS customer_number INTEGER DEFAULT NULL;

-- Index für schnelle Lookups
CREATE INDEX IF NOT EXISTS idx_employees_customer_number ON employees(customer_number);

COMMENT ON COLUMN employees.customer_number IS 'Locosoft customer_number für Adressdaten-Sync';

COMMIT;
