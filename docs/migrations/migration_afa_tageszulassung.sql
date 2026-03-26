-- Migration: AfA Tageszulassung (nicht AfA-pflichtig)
-- Datum: 2026-02-17
-- Datenbank: drive_portal (PostgreSQL)

ALTER TABLE afa_anlagevermoegen
ADD COLUMN IF NOT EXISTS tageszulassung BOOLEAN DEFAULT false;

COMMENT ON COLUMN afa_anlagevermoegen.tageszulassung IS 'Tageszulassung: nicht gefahren, unterliegt nicht der AfA; Buchhaltung setzt in UI';
