-- Migration: Hilfe-Modul Tabellen (PostgreSQL)
-- Erstellt: 2026-02-24 | Workstream: Hilfe
-- Datenbank: drive_portal

-- Kategorien (= Portal-Module)
CREATE TABLE IF NOT EXISTS hilfe_kategorien (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    beschreibung TEXT,
    icon VARCHAR(50) DEFAULT 'bi-question-circle',
    sort_order INTEGER DEFAULT 0,
    modul_route VARCHAR(255),
    aktiv BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE hilfe_kategorien IS 'Hilfe-Kategorien (Portal-Module) für Hilfe-Modul';

-- Artikel
CREATE TABLE IF NOT EXISTS hilfe_artikel (
    id SERIAL PRIMARY KEY,
    kategorie_id INTEGER NOT NULL REFERENCES hilfe_kategorien(id) ON DELETE CASCADE,
    titel VARCHAR(500) NOT NULL,
    slug VARCHAR(200) NOT NULL,
    inhalt TEXT NOT NULL,
    inhalt_format VARCHAR(20) DEFAULT 'markdown',
    tags TEXT,
    sort_order INTEGER DEFAULT 0,
    sichtbar_fuer_rollen VARCHAR(200),
    aufrufe INTEGER DEFAULT 0,
    hilfreich_ja INTEGER DEFAULT 0,
    hilfreich_nein INTEGER DEFAULT 0,
    aktiv BOOLEAN DEFAULT true,
    erstellt_von VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(kategorie_id, slug)
);

-- Volltextsuche: tsvector-Spalte (PostgreSQL)
ALTER TABLE hilfe_artikel
    ADD COLUMN IF NOT EXISTS tsv tsvector
    GENERATED ALWAYS AS (
        setweight(to_tsvector('german', coalesce(titel, '')), 'A') ||
        setweight(to_tsvector('german', coalesce(inhalt, '')), 'B') ||
        setweight(to_tsvector('german', coalesce(tags, '')), 'A')
    ) STORED;

CREATE INDEX IF NOT EXISTS idx_hilfe_artikel_tsv ON hilfe_artikel USING GIN(tsv);
CREATE INDEX IF NOT EXISTS idx_hilfe_artikel_kategorie ON hilfe_artikel(kategorie_id);
CREATE INDEX IF NOT EXISTS idx_hilfe_artikel_aktiv ON hilfe_artikel(aktiv);

COMMENT ON TABLE hilfe_artikel IS 'Hilfe-Artikel mit Volltextsuche (tsvector)';

-- Feedback
CREATE TABLE IF NOT EXISTS hilfe_feedback (
    id SERIAL PRIMARY KEY,
    artikel_id INTEGER REFERENCES hilfe_artikel(id) ON DELETE SET NULL,
    user_id VARCHAR(100),
    hilfreich BOOLEAN NOT NULL,
    kommentar TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_hilfe_feedback_artikel ON hilfe_feedback(artikel_id);

-- Optional: Chat-Verlauf für spätere KI-Integration
CREATE TABLE IF NOT EXISTS hilfe_chat_verlauf (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(100),
    nachricht TEXT NOT NULL,
    rolle VARCHAR(20) NOT NULL,
    kontext_modul VARCHAR(100),
    kontext_seite VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE hilfe_chat_verlauf IS 'Chat-Verlauf für spätere KI/RAG-Integration';
