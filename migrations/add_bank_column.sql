-- =====================================================
-- MIGRATION: Bank-Spalte für FIBU-Buchungen
-- Datum: 2025-11-14
-- Zweck: Automatische Bank-Kategorisierung
-- =====================================================

-- Neue Spalte hinzufügen
ALTER TABLE fibu_buchungen 
ADD COLUMN bank TEXT;

-- Index für Performance
CREATE INDEX IF NOT EXISTS idx_fibu_bank 
ON fibu_buchungen(bank);

-- =====================================================
-- VALIDIERUNG (nach Migration ausführen)
-- =====================================================

-- Prüfen ob Spalte existiert:
-- SELECT sql FROM sqlite_master WHERE name='fibu_buchungen';

-- =====================================================
-- INSTALLATION
-- =====================================================

-- Ausführen mit:
-- cd /opt/greiner-portal
-- sqlite3 data/greiner_controlling.db < migrations/add_bank_column.sql

-- =====================================================
-- ENDE MIGRATION
-- =====================================================
