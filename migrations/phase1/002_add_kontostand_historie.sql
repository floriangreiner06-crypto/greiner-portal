-- ============================================================================
-- MIGRATION 002: KONTOSTAND-HISTORIE
-- ============================================================================
-- Priorität: 🔴 KRITISCH
-- Beschreibung: Historisierung von Kontoständen für Zeitreihen und Charts
-- Datum: 2025-11-07
-- ============================================================================

CREATE TABLE IF NOT EXISTS kontostand_historie (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    konto_id INTEGER NOT NULL,
    datum DATE NOT NULL,
    saldo REAL NOT NULL,
    waehrung TEXT DEFAULT 'EUR',
    quelle TEXT CHECK(quelle IN ('PDF_Import', 'Manuelle_Eingabe', 'Berechnet', 'API')),
    erfasst_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (konto_id) REFERENCES konten(id) ON DELETE CASCADE,
    UNIQUE(konto_id, datum)
);

CREATE INDEX IF NOT EXISTS idx_kontostand_konto ON kontostand_historie(konto_id);
CREATE INDEX IF NOT EXISTS idx_kontostand_datum ON kontostand_historie(datum);

-- Validierung
SELECT 'Migration 002: kontostand_historie-Tabelle erstellt' as Status;
SELECT COUNT(*) as 'Tabelle existiert (1=ja)' FROM sqlite_master WHERE type='table' AND name='kontostand_historie';
