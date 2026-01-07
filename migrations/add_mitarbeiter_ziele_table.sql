-- ============================================================================
-- MITARBEITER-ZIELE TABELLE
-- ============================================================================
-- Erstellt: TAG 164
-- Zweck: Manuelle Ziel-Anpassungen für Serviceberater (und später Verkäufer)
-- Basis: Automatisch aus 1%-Ziel abgeleitet, aber manuell anpassbar
-- ============================================================================

CREATE TABLE IF NOT EXISTS mitarbeiter_ziele (
    id SERIAL PRIMARY KEY,
    
    -- Mitarbeiter-Referenz
    employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    locosoft_ma_id INTEGER,  -- Locosoft MA-ID (z.B. 4000, 4005) für Serviceberater
    
    -- Zeitraum
    geschaeftsjahr TEXT NOT NULL,  -- z.B. '2025/26'
    monat INTEGER NOT NULL,  -- 1-12 (Kalendermonat: 1=Jan, 12=Dez)
    
    -- Serviceberater-Ziele
    umsatz_ziel NUMERIC(15,2),  -- Monatsumsatz-Ziel (EUR)
    db1_ziel NUMERIC(15,2),     -- DB1-Ziel (EUR)
    stunden_ziel NUMERIC(10,2), -- Stunden-Ziel (optional, später)
    auslastung_ziel NUMERIC(5,2), -- Auslastungs-Ziel % (optional, später)
    
    -- Verkauf-Ziele (später)
    stueck_ziel INTEGER,        -- Stückzahl-Ziel (optional)
    
    -- Metadaten
    ist_manuell BOOLEAN DEFAULT false,  -- true = manuell angepasst, false = automatisch
    kommentar TEXT,              -- Warum wurde angepasst?
    erstellt_von VARCHAR(100),   -- LDAP-Username
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    geaendert_von VARCHAR(100),
    geaendert_am TIMESTAMP,
    
    -- Constraints
    UNIQUE(employee_id, geschaeftsjahr, monat),
    UNIQUE(locosoft_ma_id, geschaeftsjahr, monat),
    CHECK (monat >= 1 AND monat <= 12)
);

-- Index für schnelle Abfragen
CREATE INDEX IF NOT EXISTS idx_mitarbeiter_ziele_employee ON mitarbeiter_ziele(employee_id);
CREATE INDEX IF NOT EXISTS idx_mitarbeiter_ziele_locosoft ON mitarbeiter_ziele(locosoft_ma_id);
CREATE INDEX IF NOT EXISTS idx_mitarbeiter_ziele_gj_monat ON mitarbeiter_ziele(geschaeftsjahr, monat);

-- Kommentare
COMMENT ON TABLE mitarbeiter_ziele IS 'Mitarbeiter-Ziele (Serviceberater, später Verkäufer) - Automatisch aus 1%-Ziel abgeleitet, manuell anpassbar';
COMMENT ON COLUMN mitarbeiter_ziele.locosoft_ma_id IS 'Locosoft MA-ID (z.B. 4000 für Serviceberater)';
COMMENT ON COLUMN mitarbeiter_ziele.ist_manuell IS 'true = manuell angepasst, false = automatisch aus 1%-Ziel berechnet';
COMMENT ON COLUMN mitarbeiter_ziele.monat IS 'Kalendermonat: 1=Januar, 12=Dezember';

-- ============================================================================

