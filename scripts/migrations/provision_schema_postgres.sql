-- Provisionsmodul – PostgreSQL-Schema (DRIVE drive_portal)
-- Phase 1: provision_config (SSOT für Sätze/Grenzen)
-- Phase 2+: provision_laeufe, provision_positionen, provision_zusatzleistungen, provision_audit_log
-- Keine Redundanz: Berechnungen nutzen nur diese Config + sales-Tabelle (Rohdaten)

-- =============================================================================
-- 1. provision_config – einzige Quelle für Sätze, Min/Max, J60/J61 (SSOT)
-- =============================================================================
CREATE TABLE IF NOT EXISTS provision_config (
    id SERIAL PRIMARY KEY,
    kategorie TEXT NOT NULL,
    bezeichnung TEXT NOT NULL,
    bemessungsgrundlage TEXT NOT NULL,
    prozentsatz REAL NOT NULL,
    min_betrag REAL,
    max_betrag REAL,
    stueck_praemie REAL,
    stueck_max INTEGER,
    param_j60 REAL,
    param_j61 REAL,
    gueltig_ab DATE NOT NULL,
    gueltig_bis DATE,
    erstellt_von TEXT NOT NULL,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(kategorie, gueltig_ab)
);

COMMENT ON TABLE provision_config IS 'SSOT Provisionssätze; Berechnungslogik liest nur hier + sales';

-- Default-Daten (VFW max 300€ wie PROVISIONSLOGIK_AUS_EXCEL J54)
INSERT INTO provision_config (kategorie, bezeichnung, bemessungsgrundlage, prozentsatz, min_betrag, max_betrag, stueck_praemie, stueck_max, param_j60, param_j61, gueltig_ab, erstellt_von) VALUES
('I_neuwagen', 'Neuwagen', 'db', 0.12, NULL, NULL, 50.0, 15, NULL, NULL, '2024-01-01', 'system'),
('II_testwagen', 'Testwagen/VFW', 'rg_netto', 0.01, 103.0, 300.0, NULL, NULL, NULL, NULL, '2024-01-01', 'system'),
('III_gebrauchtwagen', 'Gebrauchtwagen', 'rg_netto', 0.01, 103.0, 500.0, NULL, NULL, NULL, NULL, '2024-01-01', 'system'),
('IV_gw_bestand', 'GW aus Bestand', 'db', 0.12, NULL, NULL, NULL, NULL, NULL, NULL, '2024-01-01', 'system'),
('V_finanzierung', 'Finanzierungsprovision', 'manuell', 30.0, NULL, NULL, NULL, NULL, NULL, NULL, '2024-01-01', 'system'),
('V_versicherung', 'Versicherungsprovision', 'manuell', 25.0, NULL, NULL, NULL, NULL, NULL, NULL, '2024-01-01', 'system'),
('V_garantie', 'Garantieverlängerung', 'manuell', 100.0, NULL, NULL, NULL, NULL, NULL, NULL, '2024-01-01', 'system'),
('V_leasing', 'Leasingprovision', 'manuell', 30.0, NULL, NULL, NULL, NULL, NULL, NULL, '2024-01-01', 'system'),
('V_sonstiges', 'Sonstiges', 'manuell', 100.0, NULL, NULL, NULL, NULL, NULL, NULL, '2024-01-01', 'system')
ON CONFLICT (kategorie, gueltig_ab) DO NOTHING;

-- =============================================================================
-- 2. provision_laeufe (Phase 2 – für Vorlauf/Endlauf)
-- =============================================================================
CREATE TABLE IF NOT EXISTS provision_laeufe (
    id SERIAL PRIMARY KEY,
    verkaufer_id INTEGER NOT NULL,
    verkaufer_name TEXT NOT NULL,
    abrechnungsmonat TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ENTWURF',
    summe_kat_i REAL DEFAULT 0,
    summe_kat_ii REAL DEFAULT 0,
    summe_kat_iii REAL DEFAULT 0,
    summe_kat_iv REAL DEFAULT 0,
    summe_kat_v REAL DEFAULT 0,
    summe_stueckpraemie REAL DEFAULT 0,
    summe_gesamt REAL DEFAULT 0,
    vorlauf_am TIMESTAMP,
    vorlauf_von TEXT,
    pruefung_am TIMESTAMP,
    endlauf_am TIMESTAMP,
    endlauf_von TEXT,
    lohnbuchhaltung_am TIMESTAMP,
    pdf_vorlauf TEXT,
    pdf_endlauf TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    bemerkung TEXT,
    UNIQUE(verkaufer_id, abrechnungsmonat)
);

-- =============================================================================
-- 3. provision_positionen (Phase 2)
-- =============================================================================
CREATE TABLE IF NOT EXISTS provision_positionen (
    id SERIAL PRIMARY KEY,
    lauf_id INTEGER NOT NULL REFERENCES provision_laeufe(id) ON DELETE CASCADE,
    kategorie TEXT NOT NULL,
    vin TEXT,
    marke TEXT,
    modell TEXT,
    fahrzeugart TEXT,
    kaeufer_name TEXT,
    rg_netto REAL,
    deckungsbeitrag REAL,
    bemessungsgrundlage REAL NOT NULL,
    kosten_abzug REAL,
    provisionssatz REAL NOT NULL,
    provision_berechnet REAL NOT NULL,
    provision_final REAL NOT NULL,
    locosoft_rg_nr TEXT,
    rg_datum DATE,
    auslieferung_datum DATE,
    einspruch_flag BOOLEAN DEFAULT FALSE,
    einspruch_text TEXT,
    einspruch_am TIMESTAMP,
    einspruch_bearbeitet BOOLEAN DEFAULT FALSE,
    einspruch_antwort TEXT,
    einspruch_bearbeitet_von TEXT,
    einspruch_bearbeitet_am TIMESTAMP,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 4. provision_zusatzleistungen (Phase 3)
-- =============================================================================
CREATE TABLE IF NOT EXISTS provision_zusatzleistungen (
    id SERIAL PRIMARY KEY,
    vin TEXT NOT NULL,
    verkaufer_id INTEGER NOT NULL,
    typ TEXT NOT NULL,
    bezeichnung TEXT,
    betrag_gesamt REAL NOT NULL,
    anteil_prozent REAL NOT NULL,
    provision_verkaufer REAL NOT NULL,
    beleg_datum DATE,
    beleg_referenz TEXT,
    abrechnungsmonat TEXT NOT NULL,
    lauf_id INTEGER REFERENCES provision_laeufe(id) ON DELETE SET NULL,
    erfasst_von TEXT NOT NULL,
    erfasst_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    geaendert_von TEXT,
    geaendert_am TIMESTAMP
);

-- =============================================================================
-- 5. provision_audit_log (Phase 2+)
-- =============================================================================
CREATE TABLE IF NOT EXISTS provision_audit_log (
    id SERIAL PRIMARY KEY,
    aktion TEXT NOT NULL,
    lauf_id INTEGER,
    position_id INTEGER,
    zusatzleistung_id INTEGER,
    benutzer TEXT NOT NULL,
    details TEXT,
    zeitstempel TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_provision_config_gueltig ON provision_config(gueltig_ab, gueltig_bis);
CREATE INDEX IF NOT EXISTS idx_provision_laeufe_monat ON provision_laeufe(abrechnungsmonat);
CREATE INDEX IF NOT EXISTS idx_provision_positionen_lauf ON provision_positionen(lauf_id);
CREATE INDEX IF NOT EXISTS idx_provision_zusatz_monat ON provision_zusatzleistungen(abrechnungsmonat);
