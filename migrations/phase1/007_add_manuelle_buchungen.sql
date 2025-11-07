-- ============================================================================
-- MIGRATION 007: MANUELLE BUCHUNGEN
-- ============================================================================
-- Priorität: 🟡 MITTEL
-- Beschreibung: Erfassung manueller Korrekturbuchungen
-- Datum: 2025-11-07
-- ============================================================================

CREATE TABLE IF NOT EXISTS manuelle_buchungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    konto_id INTEGER NOT NULL,
    datum DATE NOT NULL,
    beschreibung TEXT NOT NULL,
    betrag REAL NOT NULL,
    kategorie TEXT,
    steuerrelevant BOOLEAN DEFAULT 0,
    erfasser TEXT,
    erfasst_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notizen TEXT,
    FOREIGN KEY (konto_id) REFERENCES konten(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_manuell_konto ON manuelle_buchungen(konto_id);
CREATE INDEX IF NOT EXISTS idx_manuell_datum ON manuelle_buchungen(datum);

-- Validierung
SELECT 'Migration 007: manuelle_buchungen-Tabelle erstellt' as Status;
SELECT COUNT(*) as 'Tabelle existiert (1=ja)' FROM sqlite_master WHERE type='table' AND name='manuelle_buchungen';
