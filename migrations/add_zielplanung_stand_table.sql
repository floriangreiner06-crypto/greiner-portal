-- ============================================================================
-- ZIELPLANUNG_STAND – Planungsstand pro Zieljahr (Parameter + Status)
-- ============================================================================
-- Speicherkonzept Verkäufer-Zielplanung: Parameter persistent, Status entwurf/freigegeben.
-- Monatsziele/Auftragseingang nutzen verkaeufer_ziele nur bei status = 'freigegeben'.
-- ============================================================================

CREATE TABLE IF NOT EXISTS zielplanung_stand (
    kalenderjahr INTEGER NOT NULL PRIMARY KEY,
    referenz_jahr INTEGER NOT NULL,
    konzernziel_nw INTEGER NOT NULL DEFAULT 0,
    konzernziel_gw INTEGER NOT NULL DEFAULT 0,
    ziel_nw_hyundai INTEGER,
    ziel_nw_opel INTEGER,
    ziel_nw_leapmotor INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'entwurf' CHECK (status IN ('entwurf', 'freigegeben')),
    zuletzt_gespeichert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    zuletzt_gespeichert_von VARCHAR(100),
    freigegeben_am TIMESTAMP,
    freigegeben_von VARCHAR(100),
    CHECK (kalenderjahr >= 2020 AND kalenderjahr <= 2100),
    CHECK (referenz_jahr >= 2020 AND referenz_jahr <= 2100),
    CHECK (konzernziel_nw >= 0 AND konzernziel_gw >= 0)
);

CREATE INDEX IF NOT EXISTS idx_zielplanung_stand_status ON zielplanung_stand(status);

COMMENT ON TABLE zielplanung_stand IS 'Planungsstand Verkäufer-Zielplanung pro Jahr: Parameter + Status (entwurf/freigegeben). Wirksam für Monatsziele nur bei freigegeben.';
