-- ============================================================================
-- MIGRATION 010: AUDIT-LOG
-- ============================================================================
-- Priorität: 🟢 NIEDRIG (aber wichtig für Compliance)
-- Beschreibung: Protokollierung aller Datenänderungen
-- Datum: 2025-11-07
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tabelle TEXT NOT NULL,
    datensatz_id INTEGER,
    aktion TEXT CHECK(aktion IN ('INSERT', 'UPDATE', 'DELETE', 'IMPORT')),
    benutzer TEXT,
    zeitpunkt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    alte_werte TEXT,
    neue_werte TEXT,
    bemerkung TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_tabelle ON audit_log(tabelle);
CREATE INDEX IF NOT EXISTS idx_audit_zeitpunkt ON audit_log(zeitpunkt);
CREATE INDEX IF NOT EXISTS idx_audit_aktion ON audit_log(aktion);

-- Validierung
SELECT 'Migration 010: audit_log-Tabelle erstellt' as Status;
SELECT COUNT(*) as 'Tabelle existiert (1=ja)' FROM sqlite_master WHERE type='table' AND name='audit_log';
