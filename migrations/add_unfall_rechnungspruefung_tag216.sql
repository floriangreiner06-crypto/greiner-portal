-- Migration: Versicherungs-Rechnungsprüfung Unfallschäden
-- Modul: DB-Schema für M1–M4 (Vollständigkeitscheck, Kürzungs-Abwehr, Tracking, Wissensdatenbank)
-- Datum: 2026-02-11

BEGIN;

-- ============================================================================
-- 1. CHECKLISTE-POSITIONEN (Stammdaten M4 – typische Kürzungspositionen)
-- ============================================================================

CREATE TABLE IF NOT EXISTS unfall_checkliste_positionen (
    id SERIAL PRIMARY KEY,
    bezeichnung VARCHAR(200) NOT NULL,
    haeufigkeit VARCHAR(50) DEFAULT NULL,   -- 'Sehr häufig', 'Häufig', 'Mittel', 'Selten'
    rechtslage TEXT DEFAULT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_unfall_checkliste_sort ON unfall_checkliste_positionen(sort_order);

COMMENT ON TABLE unfall_checkliste_positionen IS 'Typische Kürzungspositionen der Versicherungen – Checkliste für M1/M2';

-- ============================================================================
-- 2. URTEILE (Wissensdatenbank M4)
-- ============================================================================

CREATE TABLE IF NOT EXISTS unfall_urteile (
    id SERIAL PRIMARY KEY,
    aktenzeichen VARCHAR(100) NOT NULL,
    gericht VARCHAR(150) NOT NULL,
    urteil_datum DATE DEFAULT NULL,
    position_kategorie VARCHAR(200) DEFAULT NULL,  -- Zuordnung zu Checklisten-Position(en), kommagetrennt
    kurzfassung TEXT NOT NULL,
    volltext_link TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_unfall_urteile_aktenzeichen ON unfall_urteile(aktenzeichen);
CREATE INDEX IF NOT EXISTS idx_unfall_urteile_datum ON unfall_urteile(urteil_datum);
CREATE INDEX IF NOT EXISTS idx_unfall_urteile_position ON unfall_urteile(position_kategorie);

COMMENT ON TABLE unfall_urteile IS 'Rechtsprechung für Kürzungs-Abwehr (M2/M4)';

-- ============================================================================
-- 3. URTEIL ↔ CHECKLISTE (n:n – welches Urteil passt zu welcher Position)
-- ============================================================================

CREATE TABLE IF NOT EXISTS unfall_urteile_checkliste (
    id SERIAL PRIMARY KEY,
    urteil_id INTEGER NOT NULL REFERENCES unfall_urteile(id) ON DELETE CASCADE,
    checkliste_position_id INTEGER NOT NULL REFERENCES unfall_checkliste_positionen(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(urteil_id, checkliste_position_id)
);

CREATE INDEX IF NOT EXISTS idx_unfall_uc_urteil ON unfall_urteile_checkliste(urteil_id);
CREATE INDEX IF NOT EXISTS idx_unfall_uc_checkliste ON unfall_urteile_checkliste(checkliste_position_id);

-- ============================================================================
-- 4. VERSICHERUNGEN (Stammdaten, Kürzungsstatistik in M3)
-- ============================================================================

CREATE TABLE IF NOT EXISTS unfall_versicherungen (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    pruefdienstleister VARCHAR(150) DEFAULT NULL,  -- ControlExpert, CarExpert, DEKRA, …
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_unfall_versicherungen_name ON unfall_versicherungen(name);

-- ============================================================================
-- 5. UNFALL-RECHNUNGEN (Kopf pro Auftrag/Gutachten)
-- ============================================================================

CREATE TABLE IF NOT EXISTS unfall_rechnungen (
    id SERIAL PRIMARY KEY,
    auftragsnummer VARCHAR(100) DEFAULT NULL,      -- Locosoft Auftragsnummer
    versicherung_id INTEGER DEFAULT NULL REFERENCES unfall_versicherungen(id) ON DELETE SET NULL,
    gutachten_nr VARCHAR(100) DEFAULT NULL,
    rechnungsbetrag DECIMAL(12,2) DEFAULT NULL,
    status VARCHAR(50) DEFAULT 'offen',           -- offen, versendet, gekuerzt, bezahlt, widerspruch, …
    rechnungsdatum DATE DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_unfall_rechnungen_auftrag ON unfall_rechnungen(auftragsnummer);
CREATE INDEX IF NOT EXISTS idx_unfall_rechnungen_versicherung ON unfall_rechnungen(versicherung_id);
CREATE INDEX IF NOT EXISTS idx_unfall_rechnungen_status ON unfall_rechnungen(status);

-- ============================================================================
-- 6. POSITIONEN PRO RECHNUNG (Einzelposten)
-- ============================================================================

CREATE TABLE IF NOT EXISTS unfall_positionen (
    id SERIAL PRIMARY KEY,
    rechnung_id INTEGER NOT NULL REFERENCES unfall_rechnungen(id) ON DELETE CASCADE,
    bezeichnung VARCHAR(300) DEFAULT NULL,
    betrag DECIMAL(12,2) DEFAULT NULL,
    checkliste_position_id INTEGER DEFAULT NULL REFERENCES unfall_checkliste_positionen(id) ON DELETE SET NULL,
    in_rechnung BOOLEAN DEFAULT true,   -- in Rechnung enthalten
    gekuerzt BOOLEAN DEFAULT false,    -- von Versicherung gekürzt
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_unfall_positionen_rechnung ON unfall_positionen(rechnung_id);
CREATE INDEX IF NOT EXISTS idx_unfall_positionen_checkliste ON unfall_positionen(checkliste_position_id);

-- ============================================================================
-- 7. KÜRZUNGEN (Pro Prüfbericht/Rechnung – gekürzte Beträge)
-- ============================================================================

CREATE TABLE IF NOT EXISTS unfall_kuerzungen (
    id SERIAL PRIMARY KEY,
    rechnung_id INTEGER NOT NULL REFERENCES unfall_rechnungen(id) ON DELETE CASCADE,
    unfall_position_id INTEGER DEFAULT NULL REFERENCES unfall_positionen(id) ON DELETE SET NULL,
    checkliste_position_id INTEGER DEFAULT NULL REFERENCES unfall_checkliste_positionen(id) ON DELETE SET NULL,
    kuerzungsbetrag DECIMAL(12,2) NOT NULL,
    begruendung_versicherung TEXT DEFAULT NULL,
    widerspruch_status VARCHAR(50) DEFAULT 'offen',  -- offen, eingereicht, anerkannt, abgelehnt, klage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_unfall_kuerzungen_rechnung ON unfall_kuerzungen(rechnung_id);
CREATE INDEX IF NOT EXISTS idx_unfall_kuerzungen_status ON unfall_kuerzungen(widerspruch_status);

COMMIT;
