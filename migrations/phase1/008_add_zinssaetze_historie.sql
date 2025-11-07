-- ============================================================================
-- MIGRATION 008: ZINSSÄTZE-HISTORIE
-- ============================================================================
-- Priorität: 🟡 MITTEL
-- Beschreibung: Historisierung von Zinssätzen für Haben/Soll/Dispo
-- Datum: 2025-11-07
-- ============================================================================

CREATE TABLE IF NOT EXISTS zinssaetze_historie (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    konto_id INTEGER NOT NULL,
    zinssatz REAL NOT NULL,
    zinstyp TEXT CHECK(zinstyp IN ('Haben', 'Soll', 'Dispo')),
    gueltig_von DATE NOT NULL,
    gueltig_bis DATE,
    notizen TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (konto_id) REFERENCES konten(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_zinsen_konto ON zinssaetze_historie(konto_id);
CREATE INDEX IF NOT EXISTS idx_zinsen_typ ON zinssaetze_historie(zinstyp);
CREATE INDEX IF NOT EXISTS idx_zinsen_gueltig ON zinssaetze_historie(gueltig_von, gueltig_bis);

-- Validierung
SELECT 'Migration 008: zinssaetze_historie-Tabelle erstellt' as Status;
SELECT COUNT(*) as 'Tabelle existiert (1=ja)' FROM sqlite_master WHERE type='table' AND name='zinssaetze_historie';
