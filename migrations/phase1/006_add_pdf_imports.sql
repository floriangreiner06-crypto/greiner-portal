-- ============================================================================
-- MIGRATION 006: PDF-IMPORT PROTOKOLL
-- ============================================================================
-- Priorität: 🟡 MITTEL
-- Beschreibung: Tracking von PDF-Importen für Nachvollziehbarkeit
-- Datum: 2025-11-07
-- ============================================================================

CREATE TABLE IF NOT EXISTS pdf_imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dateiname TEXT NOT NULL,
    dateipfad TEXT,
    bank_id INTEGER,
    konto_id INTEGER,
    import_datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    anzahl_transaktionen INTEGER DEFAULT 0,
    zeitraum_von DATE,
    zeitraum_bis DATE,
    status TEXT CHECK(status IN ('Erfolgreich', 'Teilweise', 'Fehler', 'Duplikat')),
    fehlermeldung TEXT,
    verarbeitet_von TEXT,
    FOREIGN KEY (bank_id) REFERENCES banken(id),
    FOREIGN KEY (konto_id) REFERENCES konten(id)
);

CREATE INDEX IF NOT EXISTS idx_pdf_imports_datum ON pdf_imports(import_datum);
CREATE INDEX IF NOT EXISTS idx_pdf_imports_status ON pdf_imports(status);
CREATE INDEX IF NOT EXISTS idx_pdf_imports_bank ON pdf_imports(bank_id);

-- Validierung
SELECT 'Migration 006: pdf_imports-Tabelle erstellt' as Status;
SELECT COUNT(*) as 'Tabelle existiert (1=ja)' FROM sqlite_master WHERE type='table' AND name='pdf_imports';
