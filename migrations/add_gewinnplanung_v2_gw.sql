-- Migration: Gewinnplanungstool V2 - KST 2 (GW) Schema
-- Erstellt: 2026-01-07
-- TAG 169

-- Haupttabelle für GW-Planung
CREATE TABLE IF NOT EXISTS gewinnplanung_v2_gw (
    id SERIAL PRIMARY KEY,
    geschaeftsjahr VARCHAR(7) NOT NULL,  -- '2025/26'
    standort INTEGER NOT NULL,          -- 1, 2, 3
    status VARCHAR(20) DEFAULT 'entwurf',  -- 'entwurf', 'eingereicht', 'freigegeben'
    
    -- Planungswerte (7 Fragen)
    plan_stueck NUMERIC(10,2),                    -- Frage 1: Stückzahl (Jahr)
    plan_bruttoertrag_pro_fzg NUMERIC(10,2),     -- Frage 2: Ø Bruttoertrag pro Fahrzeug
    plan_variable_kosten_pct NUMERIC(5,2),        -- Frage 3: Variable Kosten (%)
    plan_verkaufspreis NUMERIC(10,2),            -- Frage 4: Ø Verkaufspreis (auto-berechnet)
    plan_standzeit_tage INTEGER,                  -- Frage 5: Ø Standzeit (Tage) - WICHTIG!
    plan_ek_preis NUMERIC(10,2),                 -- Frage 6: Ø EK-Preis (für Zinskosten)
    plan_zinssatz_pct NUMERIC(5,2) DEFAULT 5.0,  -- Frage 7: Zinssatz (% p.a.) - optional, Default 5%
    
    -- Berechnete Werte
    umsatz_plan NUMERIC(12,2),
    einsatz_plan NUMERIC(12,2),
    bruttoertrag_plan NUMERIC(12,2),
    variable_kosten_plan NUMERIC(12,2),
    db1_plan NUMERIC(12,2),
    direkte_kosten_plan NUMERIC(12,2),
    lagerwert_plan NUMERIC(12,2),                -- Durchschnittlicher Lagerwert
    zinskosten_plan NUMERIC(12,2),               -- Zinskosten basierend auf Standzeit
    db2_plan NUMERIC(12,2),
    
    -- Vorjahreswerte (aus BWA - SSOT)
    vj_umsatz NUMERIC(12,2),
    vj_db1 NUMERIC(12,2),
    vj_db2 NUMERIC(12,2),
    vj_stueck NUMERIC(10,2),
    vj_standzeit NUMERIC(5,2),                    -- Vorjahr Standzeit (Tage)
    vj_zinskosten NUMERIC(12,2),                 -- Vorjahr Zinskosten
    
    -- Impact-Analyse
    impact_standzeit_ersparnis NUMERIC(12,2),    -- Ersparnis durch Standzeit-Reduktion
    impact_zinskosten_ersparnis NUMERIC(12,2),    -- Ersparnis durch Zinskosten-Reduktion
    impact_db1_mehr NUMERIC(12,2),                -- Mehr DB1 durch Verbesserungen
    impact_db2_mehr NUMERIC(12,2),                -- Mehr DB2 (inkl. Zinskosten-Ersparnis)
    
    -- Metadaten
    erstellt_von VARCHAR(100),
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    freigegeben_von VARCHAR(100),
    freigegeben_am TIMESTAMP,
    kommentar TEXT,
    
    -- Constraints
    UNIQUE(geschaeftsjahr, standort)
);

-- Indexes für Performance
CREATE INDEX IF NOT EXISTS idx_gewinnplanung_v2_gw_geschaeftsjahr ON gewinnplanung_v2_gw(geschaeftsjahr);
CREATE INDEX IF NOT EXISTS idx_gewinnplanung_v2_gw_standort ON gewinnplanung_v2_gw(standort);
CREATE INDEX IF NOT EXISTS idx_gewinnplanung_v2_gw_status ON gewinnplanung_v2_gw(status);

-- Kommentare
COMMENT ON TABLE gewinnplanung_v2_gw IS 'Gewinnplanungstool V2 - KST 2 (Gebrauchtwagen) mit Standzeit und Zinskosten';
COMMENT ON COLUMN gewinnplanung_v2_gw.plan_standzeit_tage IS 'Ø Standzeit in Tagen - WICHTIG: Impact auf Zinskosten';
COMMENT ON COLUMN gewinnplanung_v2_gw.plan_zinssatz_pct IS 'Zinssatz p.a. für Zinskosten-Berechnung (Default: 5%)';
COMMENT ON COLUMN gewinnplanung_v2_gw.zinskosten_plan IS 'Zinskosten = Lagerwert × Zinssatz × (Standzeit / 365)';
COMMENT ON COLUMN gewinnplanung_v2_gw.impact_standzeit_ersparnis IS 'Ersparnis durch Standzeit-Reduktion (vs. Vorjahr)';
COMMENT ON COLUMN gewinnplanung_v2_gw.impact_zinskosten_ersparnis IS 'Ersparnis durch Zinskosten-Reduktion';

