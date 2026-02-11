-- Migration: Gutachten für M1 Ebene 1 (Gutachten ↔ Rechnung)
-- Tabellen: unfall_gutachten, unfall_gutachten_positionen
-- Datum: 2026-02-11

BEGIN;

-- ============================================================================
-- 1. UNFALL_GUTACHTEN (Kopf pro hochgeladenem PDF)
-- ============================================================================

CREATE TABLE IF NOT EXISTS unfall_gutachten (
    id SERIAL PRIMARY KEY,
    auftrag_nummer INTEGER NOT NULL,
    upload_datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pdf_path VARCHAR(500) DEFAULT NULL,
    gutachten_nummer VARCHAR(100) DEFAULT NULL,
    sachverstaendiger VARCHAR(200) DEFAULT NULL,
    gutachten_summe_netto DECIMAL(12,2) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_unfall_gutachten_auftrag ON unfall_gutachten(auftrag_nummer);

COMMENT ON TABLE unfall_gutachten IS 'Sachverständigengutachten (PDF) pro Versicherungsauftrag – M1 Ebene 1';

-- ============================================================================
-- 2. UNFALL_GUTACHTEN_POSITIONEN (vom Gutachten extrahierte Positionen)
-- ============================================================================

CREATE TABLE IF NOT EXISTS unfall_gutachten_positionen (
    id SERIAL PRIMARY KEY,
    gutachten_id INTEGER NOT NULL REFERENCES unfall_gutachten(id) ON DELETE CASCADE,
    position_typ VARCHAR(50) NOT NULL,   -- arbeitsposition, ersatzteil, lackierung, nebenkosten
    beschreibung TEXT DEFAULT NULL,
    arbeitswerte DECIMAL(10,2) DEFAULT NULL,
    betrag_netto DECIMAL(12,2) DEFAULT NULL,
    teilenummer VARCHAR(100) DEFAULT NULL,  -- bei ersatzteil
    in_rechnung_gefunden BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_unfall_gutachten_pos_gutachten ON unfall_gutachten_positionen(gutachten_id);
CREATE INDEX IF NOT EXISTS idx_unfall_gutachten_pos_typ ON unfall_gutachten_positionen(position_typ);

COMMENT ON TABLE unfall_gutachten_positionen IS 'Einzelpositionen aus Gutachten (AI-extrahiert) – Abgleich mit loco_labours';

COMMIT;
