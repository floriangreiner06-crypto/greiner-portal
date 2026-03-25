-- Migration: Kreditverträge und Ausführungsbestimmungen (Modalitäten-DB)
-- Erstellt: 2026-03 | Workstream: Fahrzeugfinanzierungen
-- Referenz: docs/workstreams/fahrzeugfinanzierungen/ANALYSE_PLAN_DB_KREDITVERTRAEGE_AUSFUEHRUNGSBESTIMMUNGEN.md

-- =============================================================================
-- A) Anbieter
-- =============================================================================
CREATE TABLE IF NOT EXISTS kredit_anbieter (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    kuerzel VARCHAR(50),
    aktiv BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kredit_anbieter_aktiv ON kredit_anbieter(aktiv);
COMMENT ON TABLE kredit_anbieter IS 'Anbieter EK-Finanzierung (Santander, Stellantis, Hyundai Finance, Genobank)';

-- =============================================================================
-- B) Vertragsarten (Produkt pro Anbieter)
-- =============================================================================
CREATE TABLE IF NOT EXISTS kredit_vertragsart (
    id SERIAL PRIMARY KEY,
    anbieter_id INTEGER NOT NULL REFERENCES kredit_anbieter(id) ON DELETE CASCADE,
    bezeichnung VARCHAR(300) NOT NULL,
    produkt_code VARCHAR(100),
    gueltig_von DATE,
    gueltig_bis DATE,
    aktiv BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kredit_vertragsart_anbieter ON kredit_vertragsart(anbieter_id);
CREATE INDEX IF NOT EXISTS idx_kredit_vertragsart_aktiv ON kredit_vertragsart(aktiv);
COMMENT ON TABLE kredit_vertragsart IS 'Vertragsart/Produkt pro Anbieter (z.B. EK-Finanzierung NW/GW)';

-- =============================================================================
-- C) Dokumente (Quelle der Regeln)
-- =============================================================================
CREATE TABLE IF NOT EXISTS kredit_dokumente (
    id SERIAL PRIMARY KEY,
    anbieter_id INTEGER REFERENCES kredit_anbieter(id) ON DELETE SET NULL,
    titel VARCHAR(500) NOT NULL,
    dokument_typ VARCHAR(100) DEFAULT 'Ausführungsbestimmung',
    dateipfad VARCHAR(500),
    url VARCHAR(500),
    eingang_am DATE DEFAULT CURRENT_DATE,
    bemerkung TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kredit_dokumente_anbieter ON kredit_dokumente(anbieter_id);
COMMENT ON TABLE kredit_dokumente IS 'Quelldokumente für Modalitäten (PDF, Links)';

-- =============================================================================
-- D) Ausführungsbestimmungen / Modalitäten (strukturierte Regeln + Volltext)
-- =============================================================================
CREATE TABLE IF NOT EXISTS kredit_ausfuehrungsbestimmungen (
    id SERIAL PRIMARY KEY,
    vertragsart_id INTEGER NOT NULL REFERENCES kredit_vertragsart(id) ON DELETE CASCADE,
    dokument_id INTEGER REFERENCES kredit_dokumente(id) ON DELETE SET NULL,
    regel_typ VARCHAR(100) NOT NULL,
    regel_key VARCHAR(100) NOT NULL,
    regel_wert TEXT NOT NULL,
    einheit VARCHAR(50),
    bedingung VARCHAR(300),
    volltext TEXT,
    gueltig_von DATE,
    gueltig_bis DATE,
    sortierung INTEGER DEFAULT 0,
    aktiv BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kredit_ab_vertragsart ON kredit_ausfuehrungsbestimmungen(vertragsart_id);
CREATE INDEX IF NOT EXISTS idx_kredit_ab_dokument ON kredit_ausfuehrungsbestimmungen(dokument_id);
CREATE INDEX IF NOT EXISTS idx_kredit_ab_regel_key ON kredit_ausfuehrungsbestimmungen(regel_key);
CREATE INDEX IF NOT EXISTS idx_kredit_ab_aktiv ON kredit_ausfuehrungsbestimmungen(aktiv);

-- Volltextsuche (PostgreSQL tsvector)
ALTER TABLE kredit_ausfuehrungsbestimmungen
    ADD COLUMN IF NOT EXISTS tsv tsvector
    GENERATED ALWAYS AS (
        setweight(to_tsvector('german', coalesce(regel_typ, '')), 'A') ||
        setweight(to_tsvector('german', coalesce(regel_key, '')), 'A') ||
        setweight(to_tsvector('german', coalesce(regel_wert, '')), 'A') ||
        setweight(to_tsvector('german', coalesce(bedingung, '')), 'B') ||
        setweight(to_tsvector('german', coalesce(volltext, '')), 'C')
    ) STORED;

CREATE INDEX IF NOT EXISTS idx_kredit_ab_tsv ON kredit_ausfuehrungsbestimmungen USING GIN(tsv);

COMMENT ON TABLE kredit_ausfuehrungsbestimmungen IS 'Strukturierte Modalitäten/Regeln pro Vertragsart; Volltextsuche über tsv';
