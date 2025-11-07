-- ============================================================================
-- MIGRATION 009: BANKGEBÜHREN
-- ============================================================================
-- Priorität: 🟢 NIEDRIG
-- Beschreibung: Separates Tracking von Bankgebühren
-- Datum: 2025-11-07
-- ============================================================================

CREATE TABLE IF NOT EXISTS bankgebuehren (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    konto_id INTEGER NOT NULL,
    datum DATE NOT NULL,
    gebuehrenart TEXT,
    betrag REAL NOT NULL,
    beschreibung TEXT,
    transaktion_id INTEGER,
    erfasst_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (konto_id) REFERENCES konten(id) ON DELETE CASCADE,
    FOREIGN KEY (transaktion_id) REFERENCES transaktionen(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_gebuehren_konto ON bankgebuehren(konto_id);
CREATE INDEX IF NOT EXISTS idx_gebuehren_datum ON bankgebuehren(datum);
CREATE INDEX IF NOT EXISTS idx_gebuehren_art ON bankgebuehren(gebuehrenart);

-- Validierung
SELECT 'Migration 009: bankgebuehren-Tabelle erstellt' as Status;
SELECT COUNT(*) as 'Tabelle existiert (1=ja)' FROM sqlite_master WHERE type='table' AND name='bankgebuehren';
