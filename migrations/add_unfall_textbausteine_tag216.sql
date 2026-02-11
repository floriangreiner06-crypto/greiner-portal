-- Migration: UE IWW Textbausteine für M4 Wissensdatenbank
-- Tabellen: unfall_textbausteine, unfall_textbausteine_positionen
-- Datum: 2026-02-11

BEGIN;

CREATE TABLE IF NOT EXISTS unfall_textbausteine (
    id SERIAL PRIMARY KEY,
    tb_nummer VARCHAR(50) DEFAULT NULL,
    titel VARCHAR(500) NOT NULL,
    beschreibung TEXT DEFAULT NULL,
    kategorie_hk VARCHAR(10) DEFAULT NULL,
    datum VARCHAR(20) DEFAULT NULL,
    typ VARCHAR(100) DEFAULT NULL,
    thema VARCHAR(200) DEFAULT NULL,
    rubrik VARCHAR(200) DEFAULT NULL,
    iww_url TEXT DEFAULT NULL,
    abruf_nummer VARCHAR(50) DEFAULT NULL,
    ist_anwaltsbaustein BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(iww_url)
);

CREATE INDEX IF NOT EXISTS idx_unfall_tb_nummer ON unfall_textbausteine(tb_nummer);
CREATE INDEX IF NOT EXISTS idx_unfall_tb_typ ON unfall_textbausteine(typ);
CREATE INDEX IF NOT EXISTS idx_unfall_tb_thema ON unfall_textbausteine(thema);

COMMENT ON TABLE unfall_textbausteine IS 'UE IWW Textbausteine (gescrapt von ue.iww.de) – M4';

CREATE TABLE IF NOT EXISTS unfall_textbausteine_positionen (
    id SERIAL PRIMARY KEY,
    textbaustein_id INTEGER NOT NULL REFERENCES unfall_textbausteine(id) ON DELETE CASCADE,
    checkliste_position_id INTEGER NOT NULL REFERENCES unfall_checkliste_positionen(id) ON DELETE CASCADE,
    relevanz VARCHAR(50) DEFAULT 'direkt',
    UNIQUE(textbaustein_id, checkliste_position_id)
);

CREATE INDEX IF NOT EXISTS idx_unfall_tb_pos_tb ON unfall_textbausteine_positionen(textbaustein_id);
CREATE INDEX IF NOT EXISTS idx_unfall_tb_pos_checkliste ON unfall_textbausteine_positionen(checkliste_position_id);

COMMENT ON TABLE unfall_textbausteine_positionen IS 'Verknüpfung Textbaustein ↔ Kürzungsposition (Checkliste)';

COMMIT;
