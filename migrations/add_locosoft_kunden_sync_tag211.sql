-- ============================================================================
-- Migration: Locosoft-Kunden-Sync für bessere Suche (Adressbuch)
-- ============================================================================
-- Erstellt: TAG 211
-- Zweck: Kundendaten aus Locosoft in DRIVE PostgreSQL syncen,
--        Volltextsuche (tsvector) und Indizes für bessere Adressbuch-Suche.
-- ============================================================================

-- Tabelle: eine Zeile pro Kunde, Telefon/E-Mail zusammengefasst
CREATE TABLE IF NOT EXISTS locosoft_kunden_sync (
    id SERIAL PRIMARY KEY,
    customer_number INTEGER NOT NULL UNIQUE,
    subsidiary INTEGER,
    first_name VARCHAR(255),
    family_name VARCHAR(255),
    display_name VARCHAR(512) NOT NULL DEFAULT '',
    home_street VARCHAR(255),
    zip_code VARCHAR(20),
    home_city VARCHAR(255),
    country_code VARCHAR(10),
    phone VARCHAR(50),
    phone_mobile VARCHAR(50),
    email VARCHAR(255),
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_locosoft_kunden_sync_customer_number UNIQUE (customer_number)
);

-- Volltextsuche: Name + Kundennummer (deutsche Konfiguration)
ALTER TABLE locosoft_kunden_sync
ADD COLUMN IF NOT EXISTS search_vector tsvector
GENERATED ALWAYS AS (
    setweight(to_tsvector('german', COALESCE(display_name, '')), 'A')
    || setweight(to_tsvector('german', COALESCE(first_name, '')), 'A')
    || setweight(to_tsvector('german', COALESCE(family_name, '')), 'A')
    || setweight(to_tsvector('simple', COALESCE(customer_number::text, '')), 'B')
) STORED;

CREATE INDEX IF NOT EXISTS idx_locosoft_kunden_sync_search
ON locosoft_kunden_sync USING GIN (search_vector);

CREATE INDEX IF NOT EXISTS idx_locosoft_kunden_sync_subsidiary
ON locosoft_kunden_sync(subsidiary);

CREATE INDEX IF NOT EXISTS idx_locosoft_kunden_sync_synced_at
ON locosoft_kunden_sync(synced_at DESC);

-- Kommentar
COMMENT ON TABLE locosoft_kunden_sync IS 'Sync-Kopie der Locosoft-Kunden für Adressbuch/Volltextsuche (TAG 211)';
