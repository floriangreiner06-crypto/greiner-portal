-- Migration: Freigabe-Prozess für Hilfe-Artikel
-- Erstellt: 2026-02-24 | Workstream: Hilfe
-- Nur freigegebene Artikel erscheinen in der öffentlichen Hilfe.

ALTER TABLE hilfe_artikel
    ADD COLUMN IF NOT EXISTS freigabe_status VARCHAR(20) DEFAULT 'entwurf',
    ADD COLUMN IF NOT EXISTS freigegeben_am TIMESTAMP,
    ADD COLUMN IF NOT EXISTS freigegeben_von VARCHAR(100);

-- Bestehende Artikel gelten als freigegeben
UPDATE hilfe_artikel SET freigabe_status = 'freigegeben', freigegeben_am = CURRENT_TIMESTAMP WHERE freigabe_status IS NULL OR freigabe_status = '';

-- Default für neue Zeilen
ALTER TABLE hilfe_artikel ALTER COLUMN freigabe_status SET DEFAULT 'entwurf';

COMMENT ON COLUMN hilfe_artikel.freigabe_status IS 'entwurf = nur im Admin sichtbar, freigegeben = in Hilfe sichtbar';
