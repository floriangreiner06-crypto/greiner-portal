-- ============================================================================
-- MIGRATION 004: PDF-IMPORT PROTOKOLL
-- ============================================================================
-- Beschreibung: Tracking aller PDF-Importe für Audit und Fehleranalyse
-- Priorität: WICHTIG (benötigt für Import-Monitoring)
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

-- ============================================================================
-- HISTORISCHE IMPORTS RÜCKWIRKEND ERFASSEN (falls vorhanden)
-- ============================================================================

-- Für jede eindeutige PDF-Quelle in transaktionen einen Eintrag anlegen
INSERT OR IGNORE INTO pdf_imports (dateiname, konto_id, import_datum, anzahl_transaktionen, zeitraum_von, zeitraum_bis, status)
SELECT 
    pdf_quelle as dateiname,
    konto_id,
    MIN(importiert_am) as import_datum,
    COUNT(*) as anzahl_transaktionen,
    MIN(buchungsdatum) as zeitraum_von,
    MAX(buchungsdatum) as zeitraum_bis,
    'Erfolgreich' as status
FROM transaktionen
WHERE pdf_quelle IS NOT NULL
GROUP BY pdf_quelle, konto_id;

-- ============================================================================
-- VALIDIERUNG
-- ============================================================================

SELECT 
    'Migration 004 erfolgreich!' as Status,
    (SELECT COUNT(*) FROM pdf_imports) as Einträge_pdf_imports;
