-- ============================================================================
-- VERKAEUFER_ZIELE – gespeicherte Jahresziele (NW/GW) pro Verkäufer
-- ============================================================================
-- Workflow: Planungsgespräch → Anpassung → Speichern → Ziele wirksam
-- (Auftragseingang Zielerfüllung + Monatsziele nutzen diese Tabelle)
-- ============================================================================

CREATE TABLE IF NOT EXISTS verkaeufer_ziele (
    kalenderjahr INTEGER NOT NULL,
    mitarbeiter_nr INTEGER NOT NULL,
    ziel_nw INTEGER NOT NULL DEFAULT 0,
    ziel_gw INTEGER NOT NULL DEFAULT 0,
    planungsgespraech_am DATE,
    planungsgespraech_notiz TEXT,
    gespeichert_von VARCHAR(100),
    gespeichert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (kalenderjahr, mitarbeiter_nr),
    CHECK (kalenderjahr >= 2020 AND kalenderjahr <= 2100),
    CHECK (ziel_nw >= 0 AND ziel_gw >= 0)
);

CREATE INDEX IF NOT EXISTS idx_verkaeufer_ziele_jahr ON verkaeufer_ziele(kalenderjahr);

COMMENT ON TABLE verkaeufer_ziele IS 'Gespeicherte Verkäufer-Jahresziele (NW/GW) aus Zielplanung; wirksam für Monatsziele und Auftragseingang Zielerfüllung';
