-- ============================================================================
-- CREATE: free_days Tabelle für manuelle freie Tage (TAG 198)
-- ============================================================================
-- Erstellt Tabelle für freie Tage (z.B. Betriebsferien)
-- Diese Tage werden im Planer ausgegraut und vom Urlaubsanspruch abgezogen
-- ============================================================================

CREATE TABLE IF NOT EXISTS free_days (
    id SERIAL PRIMARY KEY,
    free_date DATE NOT NULL UNIQUE,
    description TEXT,
    affects_vacation_entitlement BOOLEAN DEFAULT true,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index für schnelle Abfragen
CREATE INDEX IF NOT EXISTS idx_free_days_date ON free_days(free_date);

-- Kommentare
COMMENT ON TABLE free_days IS 'Manuelle freie Tage (z.B. Betriebsferien) - werden im Planer ausgegraut';
COMMENT ON COLUMN free_days.free_date IS 'Datum des freien Tages';
COMMENT ON COLUMN free_days.description IS 'Beschreibung (z.B. Betriebsferien)';
COMMENT ON COLUMN free_days.affects_vacation_entitlement IS 'Ob dieser Tag vom Urlaubsanspruch abgezogen werden soll';

-- Test-Daten (optional)
-- INSERT INTO free_days (free_date, description, affects_vacation_entitlement) VALUES
-- ('2026-12-24', 'Betriebsferien', true),
-- ('2026-12-31', 'Betriebsferien', true);
