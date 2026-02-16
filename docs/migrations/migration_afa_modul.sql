-- Migration: AfA-Modul Vorführwagen/Mietwagen (Controlling)
-- Datum: 2026-02-16
-- Datenbank: drive_portal (PostgreSQL)

-- Tabelle: Anlagevermögen (VFW + Mietwagen) mit AfA-Stammdaten
CREATE TABLE IF NOT EXISTS afa_anlagevermoegen (
    id SERIAL PRIMARY KEY,

    -- Fahrzeug-Identifikation
    vin VARCHAR(20),
    kennzeichen VARCHAR(15),
    fahrzeug_bezeichnung VARCHAR(100),
    marke VARCHAR(50),
    modell VARCHAR(50),

    -- Klassifikation
    fahrzeugart VARCHAR(20) NOT NULL,
    betriebsnr INTEGER DEFAULT 1,
    firma VARCHAR(50),

    -- AfA-Basisdaten
    anschaffungsdatum DATE NOT NULL,
    anschaffungskosten_netto NUMERIC(12,2) NOT NULL,
    nutzungsdauer_monate INTEGER DEFAULT 72,
    afa_methode VARCHAR(20) DEFAULT 'linear',
    afa_monatlich NUMERIC(10,2),

    -- Status & Abgang
    status VARCHAR(20) DEFAULT 'aktiv',
    abgangsdatum DATE,
    abgangsgrund VARCHAR(50),
    verkaufspreis_netto NUMERIC(12,2),
    restbuchwert_abgang NUMERIC(12,2),
    buchgewinn_verlust NUMERIC(12,2),

    -- Referenzen
    locosoft_fahrzeug_id INTEGER,
    finanzierung_id INTEGER,

    -- Metadaten
    erstellt_am TIMESTAMP DEFAULT NOW(),
    erstellt_von VARCHAR(50),
    aktualisiert_am TIMESTAMP DEFAULT NOW(),
    notizen TEXT
);

CREATE INDEX IF NOT EXISTS idx_afa_status ON afa_anlagevermoegen(status);
CREATE INDEX IF NOT EXISTS idx_afa_fahrzeugart ON afa_anlagevermoegen(fahrzeugart);
CREATE INDEX IF NOT EXISTS idx_afa_betriebsnr ON afa_anlagevermoegen(betriebsnr);
CREATE INDEX IF NOT EXISTS idx_afa_vin ON afa_anlagevermoegen(vin);

COMMENT ON TABLE afa_anlagevermoegen IS 'Vorführwagen und Mietwagen im Anlagevermögen mit AfA-Berechnung';

-- Tabelle: Monatliche AfA-Buchungen (Historie)
CREATE TABLE IF NOT EXISTS afa_buchungen (
    id SERIAL PRIMARY KEY,
    anlage_id INTEGER REFERENCES afa_anlagevermoegen(id),
    buchungsmonat DATE NOT NULL,
    afa_betrag NUMERIC(10,2) NOT NULL,
    restbuchwert NUMERIC(12,2) NOT NULL,
    kumuliert NUMERIC(12,2) NOT NULL,
    ist_anteilig BOOLEAN DEFAULT false,
    erstellt_am TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_afa_buchungen_monat ON afa_buchungen(buchungsmonat);
CREATE INDEX IF NOT EXISTS idx_afa_buchungen_anlage ON afa_buchungen(anlage_id);

COMMENT ON TABLE afa_buchungen IS 'Monatliche AfA-Buchungen (Historie) für VFW und Mietwagen';
