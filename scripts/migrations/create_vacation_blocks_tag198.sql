-- ============================================================================
-- CREATE: vacation_blocks Tabelle für Urlaubssperren (TAG 198)
-- ============================================================================
-- Erstellt Tabelle für Urlaubssperren pro Abteilung/Datum
-- ============================================================================

CREATE TABLE IF NOT EXISTS vacation_blocks (
    id SERIAL PRIMARY KEY,
    department_name VARCHAR(255) NOT NULL,
    block_date DATE NOT NULL,
    reason TEXT,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(department_name, block_date)
);

-- Index für schnelle Abfragen
CREATE INDEX IF NOT EXISTS idx_vacation_blocks_date ON vacation_blocks(block_date);
CREATE INDEX IF NOT EXISTS idx_vacation_blocks_dept ON vacation_blocks(department_name);

-- Kommentare
COMMENT ON TABLE vacation_blocks IS 'Urlaubssperren pro Abteilung - verhindert Urlaubsbuchungen an bestimmten Tagen';
COMMENT ON COLUMN vacation_blocks.department_name IS 'Abteilung für die die Sperre gilt';
COMMENT ON COLUMN vacation_blocks.block_date IS 'Datum an dem Urlaub gesperrt ist';
COMMENT ON COLUMN vacation_blocks.reason IS 'Grund für die Sperre (optional)';

-- Test-Daten (optional)
-- INSERT INTO vacation_blocks (department_name, block_date, reason) VALUES
-- ('Service', '2026-12-24', 'Weihnachtsgeschäft'),
-- ('Service', '2026-12-31', 'Jahresende');
