-- Migration: Santander-Support für Fahrzeugfinanzierungen
-- Datum: 2025-11-08
-- Beschreibung: Erweitert fahrzeugfinanzierungen-Tabelle für mehrere Finanzinstitute

-- =======================================================
-- 1. Neue Spalten hinzufügen
-- =======================================================

-- Finanzinstitut (Stellantis oder Santander)
ALTER TABLE fahrzeugfinanzierungen 
ADD COLUMN finanzinstitut TEXT DEFAULT 'Stellantis';

-- Santander-spezifische Felder
ALTER TABLE fahrzeugfinanzierungen 
ADD COLUMN finanzierungsnummer TEXT;

ALTER TABLE fahrzeugfinanzierungen 
ADD COLUMN finanzierungsstatus TEXT;

ALTER TABLE fahrzeugfinanzierungen 
ADD COLUMN rechnungsnummer TEXT;

ALTER TABLE fahrzeugfinanzierungen 
ADD COLUMN rechnungsbetrag REAL;

ALTER TABLE fahrzeugfinanzierungen 
ADD COLUMN hsn TEXT;

ALTER TABLE fahrzeugfinanzierungen 
ADD COLUMN tsn TEXT;

ALTER TABLE fahrzeugfinanzierungen 
ADD COLUMN zinsen_letzte_periode REAL;

ALTER TABLE fahrzeugfinanzierungen 
ADD COLUMN zinsen_gesamt REAL;

ALTER TABLE fahrzeugfinanzierungen 
ADD COLUMN dokumentstatus TEXT;

-- =======================================================
-- 2. Bestehende Stellantis-Einträge updaten
-- =======================================================

UPDATE fahrzeugfinanzierungen 
SET finanzinstitut = 'Stellantis'
WHERE finanzinstitut IS NULL;

-- =======================================================
-- 3. Index erstellen für Performance
-- =======================================================

CREATE INDEX IF NOT EXISTS idx_finanzinstitut 
ON fahrzeugfinanzierungen(finanzinstitut);

CREATE INDEX IF NOT EXISTS idx_finanzierungsnummer 
ON fahrzeugfinanzierungen(finanzierungsnummer);

CREATE INDEX IF NOT EXISTS idx_status 
ON fahrzeugfinanzierungen(finanzierungsstatus);

-- =======================================================
-- 4. Validierung
-- =======================================================

-- Zeige Schema
.schema fahrzeugfinanzierungen

-- Zeige Statistik
SELECT 
    finanzinstitut,
    COUNT(*) as anzahl,
    SUM(aktueller_saldo) as gesamt_saldo
FROM fahrzeugfinanzierungen
GROUP BY finanzinstitut;

-- Erfolg
SELECT '✅ Migration erfolgreich abgeschlossen!' as status;
