-- Migration: Gesellschaft-Spalte für Ertragsvorschau (Multi-Company)
-- Erstellt: 2026-03-30
-- Werte: 'autohaus' (Opel/Leapmotor), 'auto' (Hyundai), 'gruppe' (konsolidiert)

-- 1. fibu_guv_monatswerte: Spalte hinzufügen
ALTER TABLE fibu_guv_monatswerte ADD COLUMN IF NOT EXISTS gesellschaft VARCHAR(20) NOT NULL DEFAULT 'autohaus';

-- Unique-Constraint anpassen (jetzt inkl. gesellschaft)
ALTER TABLE fibu_guv_monatswerte DROP CONSTRAINT IF EXISTS fibu_guv_monatswerte_geschaeftsjahr_monat_bereich_key;
ALTER TABLE fibu_guv_monatswerte ADD CONSTRAINT fibu_guv_monatswerte_gj_monat_bereich_ges_key
    UNIQUE(geschaeftsjahr, monat, bereich, gesellschaft);

-- 2. jahresabschluss_daten: Spalte hinzufügen
ALTER TABLE jahresabschluss_daten ADD COLUMN IF NOT EXISTS gesellschaft VARCHAR(20) NOT NULL DEFAULT 'autohaus';

-- Unique-Constraint anpassen (jetzt inkl. gesellschaft)
ALTER TABLE jahresabschluss_daten DROP CONSTRAINT IF EXISTS jahresabschluss_daten_geschaeftsjahr_key;
ALTER TABLE jahresabschluss_daten ADD CONSTRAINT jahresabschluss_daten_gj_ges_key
    UNIQUE(geschaeftsjahr, gesellschaft);

-- 3. Index für gesellschaft-Filter
CREATE INDEX IF NOT EXISTS idx_fibu_guv_ges ON fibu_guv_monatswerte(gesellschaft);
CREATE INDEX IF NOT EXISTS idx_ja_ges ON jahresabschluss_daten(gesellschaft);
