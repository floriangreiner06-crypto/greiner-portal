-- Migration: employees.provision_aktiv (Vergütung/Provision)
-- Zweck: Steuerung, wer in der Provisionsabrechnung berücksichtigt wird (false = z.B. VKL, GF).
-- Default true = Rückwärtskompatibilität.

ALTER TABLE employees ADD COLUMN IF NOT EXISTS provision_aktiv BOOLEAN DEFAULT true;
COMMENT ON COLUMN employees.provision_aktiv IS 'false = von Provisionsabrechnung ausgenommen (z.B. VKL, GF)';
