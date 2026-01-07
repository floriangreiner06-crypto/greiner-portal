-- ============================================================================
-- KST-PLANUNG PARAMETER TABELLE (TAG 165)
-- ============================================================================
-- Erstellt: TAG 165
-- Zweck: Bottom-Up Planungsparameter pro KST (Stunden, Stück, Preise)
-- ============================================================================

CREATE TABLE IF NOT EXISTS kst_planung_parameter (
    id SERIAL PRIMARY KEY,
    
    -- Zeitraum
    geschaeftsjahr TEXT NOT NULL,  -- z.B. '2025/26'
    bereich TEXT NOT NULL,          -- 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
    standort INTEGER DEFAULT 0,     -- 0=Alle, 1=DEG, 2=HYU, 3=LAN
    
    -- Werkstatt-Parameter
    stunden_pro_sb NUMERIC(10,2),   -- Produktive Stunden pro Serviceberater/Monat
    stundensatz NUMERIC(10,2),      -- Durchschnittlicher Stundensatz (EUR)
    auslastung_ziel NUMERIC(5,2),   -- Ziel-Auslastung (%)
    
    -- Verkauf-Parameter (NW/GW)
    stueck_pro_vk NUMERIC(10,2),   -- Stück pro Verkäufer/Monat
    durchschnittspreis NUMERIC(15,2), -- Durchschnittspreis pro Fahrzeug (EUR)
    marge_ziel NUMERIC(5,2),        -- Ziel-Marge (%)
    
    -- Teile/Sonstige-Parameter
    wachstumsfaktor NUMERIC(5,2),  -- Wachstumsfaktor (z.B. 1.05 = 5% Wachstum)
    
    -- Metadaten
    erstellt_von VARCHAR(100),
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    geaendert_von VARCHAR(100),
    geaendert_am TIMESTAMP,
    
    -- Constraints
    UNIQUE(geschaeftsjahr, bereich, standort),
    CHECK (bereich IN ('NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige')),
    CHECK (standort >= 0 AND standort <= 3)
);

-- Index für schnelle Abfragen
CREATE INDEX IF NOT EXISTS idx_kst_planung_parameter_gj_bereich ON kst_planung_parameter(geschaeftsjahr, bereich);
CREATE INDEX IF NOT EXISTS idx_kst_planung_parameter_standort ON kst_planung_parameter(standort);

-- Kommentare
COMMENT ON TABLE kst_planung_parameter IS 'Bottom-Up Planungsparameter pro KST (TAG 165)';
COMMENT ON COLUMN kst_planung_parameter.stunden_pro_sb IS 'Produktive Stunden pro Serviceberater/Monat (z.B. 120)';
COMMENT ON COLUMN kst_planung_parameter.stundensatz IS 'Durchschnittlicher Stundensatz in EUR (z.B. 150)';
COMMENT ON COLUMN kst_planung_parameter.stueck_pro_vk IS 'Stück pro Verkäufer/Monat (z.B. 5 für NW, 3 für GW)';
COMMENT ON COLUMN kst_planung_parameter.durchschnittspreis IS 'Durchschnittspreis pro Fahrzeug in EUR';
COMMENT ON COLUMN kst_planung_parameter.wachstumsfaktor IS 'Wachstumsfaktor (z.B. 1.05 = 5% Wachstum)';

-- Beispiel-Daten für GJ 2025/26
-- Deggendorf (Standort 1+2 kombiniert)
INSERT INTO kst_planung_parameter (geschaeftsjahr, bereich, standort, stunden_pro_sb, stundensatz, auslastung_ziel, erstellt_von)
VALUES 
    ('2025/26', 'Werkstatt', 1, 120, 150, 85, 'system')
ON CONFLICT (geschaeftsjahr, bereich, standort) DO NOTHING;

INSERT INTO kst_planung_parameter (geschaeftsjahr, bereich, standort, stueck_pro_vk, durchschnittspreis, marge_ziel, erstellt_von)
VALUES 
    ('2025/26', 'NW', 1, 5, 30000, 8.0, 'system'),
    ('2025/26', 'GW', 1, 3, 25000, 6.0, 'system')
ON CONFLICT (geschaeftsjahr, bereich, standort) DO NOTHING;

INSERT INTO kst_planung_parameter (geschaeftsjahr, bereich, standort, wachstumsfaktor, erstellt_von)
VALUES 
    ('2025/26', 'Teile', 1, 1.05, 'system'),
    ('2025/26', 'Sonstige', 1, 1.0, 'system')
ON CONFLICT (geschaeftsjahr, bereich, standort) DO NOTHING;

-- Landau (Standort 3)
INSERT INTO kst_planung_parameter (geschaeftsjahr, bereich, standort, stunden_pro_sb, stundensatz, auslastung_ziel, erstellt_von)
VALUES 
    ('2025/26', 'Werkstatt', 3, 120, 150, 85, 'system')
ON CONFLICT (geschaeftsjahr, bereich, standort) DO NOTHING;

INSERT INTO kst_planung_parameter (geschaeftsjahr, bereich, standort, stueck_pro_vk, durchschnittspreis, marge_ziel, erstellt_von)
VALUES 
    ('2025/26', 'NW', 3, 5, 30000, 8.0, 'system'),
    ('2025/26', 'GW', 3, 3, 25000, 6.0, 'system')
ON CONFLICT (geschaeftsjahr, bereich, standort) DO NOTHING;

INSERT INTO kst_planung_parameter (geschaeftsjahr, bereich, standort, wachstumsfaktor, erstellt_von)
VALUES 
    ('2025/26', 'Teile', 3, 1.05, 'system'),
    ('2025/26', 'Sonstige', 3, 1.0, 'system')
ON CONFLICT (geschaeftsjahr, bereich, standort) DO NOTHING;

-- ============================================================================

