-- ============================================================================
-- MIGRATION 002: KREDITLINIEN / LIMITS
-- ============================================================================
-- Beschreibung: Verwaltung von Kreditlinien und Kontolimits
-- Priorität: KRITISCH (benötigt für Liquiditätsmonitoring)
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

-- ============================================================================
-- BEISPIEL-DATEN (können später angepasst werden)
-- ============================================================================

-- Beispiel: Hauptkonto mit 10.000 EUR Kreditlinie
-- INSERT OR IGNORE INTO kreditlinien (konto_id, kreditlimit, zinssatz, gueltig_von) 
-- SELECT id, 10000.00, 8.5, DATE('now') FROM konten WHERE kontoname = 'Hauptkonto' LIMIT 1;

-- ============================================================================
-- VALIDIERUNG
-- ============================================================================

SELECT 
    'Migration 002 erfolgreich!' as Status,
    (SELECT COUNT(*) FROM kreditlinien) as Einträge_kreditlinien;
