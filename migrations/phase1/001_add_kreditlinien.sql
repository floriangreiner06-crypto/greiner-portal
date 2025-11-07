-- ============================================================================
-- MIGRATION 001: KREDITLINIEN-TABELLE
-- ============================================================================
-- Priorität: 🔴 KRITISCH
-- Beschreibung: Tracking von Kreditlinien und Limits für Konten
-- Datum: 2025-11-07
-- ============================================================================

CREATE TABLE IF NOT EXISTS kreditlinien (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    konto_id INTEGER NOT NULL,
    kreditlimit REAL NOT NULL,
    zinssatz REAL,
    gueltig_von DATE NOT NULL,
    gueltig_bis DATE,
    notizen TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (konto_id) REFERENCES konten(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_kredit_konto ON kreditlinien(konto_id);
CREATE INDEX IF NOT EXISTS idx_kredit_gueltig ON kreditlinien(gueltig_von, gueltig_bis);

-- Validierung
SELECT 'Migration 001: kreditlinien-Tabelle erstellt' as Status;
SELECT COUNT(*) as 'Tabelle existiert (1=ja)' FROM sqlite_master WHERE type='table' AND name='kreditlinien';
