-- ============================================================================
-- GREINER PORTAL - BANKENSPIEGEL V2 - DB SCHEMA
-- ============================================================================
-- Version: 2.0
-- Datum: 2025-11-19
-- Beschreibung: Neues Schema optimiert für:
--   - MT940-Import (Hausbanken)
--   - Fahrzeugfinanzierungen (Santander, Hyundai, Stellantis)
--   - Kreditlinien-Tracking
-- ============================================================================

-- ============================================================================
-- 1. STAMMDATEN
-- ============================================================================

-- -----------------------------------------------------------------------------
-- 1.1 Banken (Hausbanken für MT940)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS banken (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_name TEXT NOT NULL UNIQUE,
    bank_typ TEXT CHECK(bank_typ IN ('Sparkasse', 'Volksbank', 'Genossenschaftsbank', 'Sonstige')),
    bic TEXT,
    blz TEXT,
    aktiv BOOLEAN DEFAULT 1,
    notizen TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_banken_aktiv ON banken(aktiv);
CREATE INDEX idx_banken_typ ON banken(bank_typ);

-- -----------------------------------------------------------------------------
-- 1.2 Konten (Bankkonten für MT940-Transaktionen)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS konten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_id INTEGER NOT NULL,
    kontonummer TEXT NOT NULL,
    iban TEXT,
    bic TEXT,
    kontoname TEXT NOT NULL,
    kontotyp TEXT CHECK(kontotyp IN (
        'Girokonto', 
        'Kontokorrent', 
        'Festgeld', 
        'Darlehen',
        'Sonstiges'
    )) DEFAULT 'Girokonto',
    waehrung TEXT DEFAULT 'EUR',
    inhaber TEXT,
    kreditlinie REAL DEFAULT 0,
    aktiv BOOLEAN DEFAULT 1,
    eroeffnet_am DATE,
    geschlossen_am DATE,
    notizen TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bank_id) REFERENCES banken(id) ON DELETE CASCADE,
    UNIQUE(bank_id, kontonummer)
);

CREATE INDEX idx_konten_bank ON konten(bank_id);
CREATE INDEX idx_konten_aktiv ON konten(aktiv);
CREATE INDEX idx_konten_iban ON konten(iban);
CREATE INDEX idx_konten_kontonummer ON konten(kontonummer);

-- -----------------------------------------------------------------------------
-- 1.3 Finanzierungsbanken (Santander, Hyundai, Stellantis)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS finanzierungsbanken (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_name TEXT NOT NULL UNIQUE,
    bank_typ TEXT CHECK(bank_typ IN ('Santander', 'Hyundai', 'Stellantis')) NOT NULL,
    import_format TEXT CHECK(import_format IN ('CSV', 'Excel')) NOT NULL,
    aktiv BOOLEAN DEFAULT 1,
    notizen TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_finanzbanken_typ ON finanzierungsbanken(bank_typ);
CREATE INDEX idx_finanzbanken_aktiv ON finanzierungsbanken(aktiv);

-- ============================================================================
-- 2. TRANSAKTIONSDATEN (MT940)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- 2.1 Transaktionen (aus MT940)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transaktionen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    konto_id INTEGER NOT NULL,
    
    -- Buchhaltungs-Daten
    buchungsdatum DATE NOT NULL,
    valutadatum DATE,
    betrag REAL NOT NULL,
    waehrung TEXT DEFAULT 'EUR',
    saldo_nach_buchung REAL,
    
    -- Transaktions-Details
    buchungstext TEXT,
    verwendungszweck TEXT,
    auftraggeber_empfaenger TEXT,
    gegenkonto_iban TEXT,
    gegenkonto_bic TEXT,
    gegenkonto_name TEXT,
    
    -- Kategorisierung
    kategorie TEXT,
    unterkategorie TEXT,
    steuerrelevant BOOLEAN DEFAULT 0,
    
    -- Import-Tracking
    import_quelle TEXT CHECK(import_quelle IN ('MT940')) DEFAULT 'MT940',
    import_datei TEXT NOT NULL,
    import_datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rohdaten TEXT, -- Original MT940-Zeile als JSON
    
    -- Verarbeitung
    verarbeitet BOOLEAN DEFAULT 0,
    notizen TEXT,
    
    FOREIGN KEY (konto_id) REFERENCES konten(id) ON DELETE CASCADE
);

CREATE INDEX idx_trans_konto ON transaktionen(konto_id);
CREATE INDEX idx_trans_buchungsdatum ON transaktionen(buchungsdatum);
CREATE INDEX idx_trans_betrag ON transaktionen(betrag);
CREATE INDEX idx_trans_kategorie ON transaktionen(kategorie);
CREATE INDEX idx_trans_verarbeitet ON transaktionen(verarbeitet);
CREATE INDEX idx_trans_import ON transaktionen(import_datei, import_datum);

-- Unique constraint für Duplikat-Erkennung
CREATE UNIQUE INDEX idx_trans_unique ON transaktionen(
    konto_id, 
    buchungsdatum, 
    betrag, 
    verwendungszweck
);

-- -----------------------------------------------------------------------------
-- 2.2 Salden (Tägliche Kontosalden aus MT940)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS salden (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    konto_id INTEGER NOT NULL,
    datum DATE NOT NULL,
    saldo REAL NOT NULL,
    waehrung TEXT DEFAULT 'EUR',
    
    -- Import-Tracking
    quelle TEXT CHECK(quelle IN ('MT940')) DEFAULT 'MT940',
    import_datei TEXT,
    import_datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (konto_id) REFERENCES konten(id) ON DELETE CASCADE,
    UNIQUE(konto_id, datum)
);

CREATE INDEX idx_salden_konto ON salden(konto_id);
CREATE INDEX idx_salden_datum ON salden(datum);
CREATE INDEX idx_salden_konto_datum ON salden(konto_id, datum);

-- ============================================================================
-- 3. FAHRZEUGFINANZIERUNGEN
-- ============================================================================

-- -----------------------------------------------------------------------------
-- 3.1 Fahrzeugfinanzierungen (Santander, Hyundai, Stellantis)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fahrzeugfinanzierungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Bank-Zuordnung
    finanzbank_id INTEGER NOT NULL,
    
    -- Fahrzeug-Identifikation
    vin TEXT NOT NULL,
    vin_kurz TEXT, -- Letzte 8 Stellen (Stellantis)
    finanzierungsnummer TEXT,
    
    -- Fahrzeug-Details
    hersteller TEXT,
    modell TEXT,
    farbe TEXT,
    
    -- Finanzierungs-Details
    finanzierungsstatus TEXT, -- Aktiv, Abgelöst, Finanziert, etc.
    dokumentstatus TEXT,
    produktfamilie TEXT, -- Neuwagen, Vorführwagen, Gebrauchtwagen, etc.
    produkt TEXT,
    
    -- Beträge
    finanzierungsbetrag REAL NOT NULL,
    aktueller_saldo REAL NOT NULL,
    waehrung TEXT DEFAULT 'EUR',
    
    -- Zinsen
    zinsen_gesamt REAL DEFAULT 0,
    zinsen_letzte_periode REAL DEFAULT 0,
    zinsgutschriften_gesamt REAL DEFAULT 0,
    
    -- Gebühren
    gebuehren_gesamt REAL DEFAULT 0,
    gebuehren_letzte_periode REAL DEFAULT 0,
    
    -- Daten
    vertragsbeginn DATE,
    zinsbeginn DATE,
    finanzierungsende DATE,
    endfaelligkeit DATE,
    lieferdatum DATE,
    aktivierungsdatum DATE,
    anlagedatum DATE,
    
    -- Sonstige
    rechnungsnummer TEXT,
    rechnungsdatum DATE,
    rechnungsbetrag REAL,
    alter_finanzierung_tage INTEGER,
    zinsfreiheit_tage INTEGER,
    
    -- Import-Tracking
    import_quelle TEXT CHECK(import_quelle IN ('CSV_SANTANDER', 'CSV_HYUNDAI', 'EXCEL_STELLANTIS')) NOT NULL,
    import_datei TEXT NOT NULL,
    import_datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rohdaten TEXT, -- Original-Zeile als JSON
    
    -- Metadaten
    aktiv BOOLEAN DEFAULT 1,
    notizen TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (finanzbank_id) REFERENCES finanzierungsbanken(id) ON DELETE CASCADE
);

CREATE INDEX idx_fahrzeugfin_bank ON fahrzeugfinanzierungen(finanzbank_id);
CREATE INDEX idx_fahrzeugfin_vin ON fahrzeugfinanzierungen(vin);
CREATE INDEX idx_fahrzeugfin_status ON fahrzeugfinanzierungen(finanzierungsstatus);
CREATE INDEX idx_fahrzeugfin_aktiv ON fahrzeugfinanzierungen(aktiv);
CREATE INDEX idx_fahrzeugfin_import ON fahrzeugfinanzierungen(import_quelle, import_datum);

-- Unique constraint für Duplikat-Erkennung
CREATE UNIQUE INDEX idx_fahrzeugfin_unique ON fahrzeugfinanzierungen(
    finanzbank_id,
    vin,
    finanzierungsnummer
);

-- -----------------------------------------------------------------------------
-- 3.2 Finanzierung Snapshots (Historische Daten)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS finanzierung_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fahrzeugfin_id INTEGER NOT NULL,
    
    -- Snapshot-Datum
    snapshot_datum DATE NOT NULL,
    
    -- Werte zum Snapshot-Zeitpunkt
    saldo REAL NOT NULL,
    finanzierungsstatus TEXT,
    zinsen_gesamt REAL,
    zinsen_periode REAL,
    
    -- Import-Info
    import_datei TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (fahrzeugfin_id) REFERENCES fahrzeugfinanzierungen(id) ON DELETE CASCADE,
    UNIQUE(fahrzeugfin_id, snapshot_datum)
);

CREATE INDEX idx_fin_snapshots_fahrzeug ON finanzierung_snapshots(fahrzeugfin_id);
CREATE INDEX idx_fin_snapshots_datum ON finanzierung_snapshots(snapshot_datum);

-- ============================================================================
-- 4. KREDITLINIEN (STELLANTIS)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- 4.1 Kreditlinien (Aggregierte Daten aus Stellantis Sheet 1)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kreditlinien (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Identifikation
    rrdi TEXT NOT NULL,
    marke TEXT,
    gruppe TEXT,
    haendlername TEXT,
    steuernummer TEXT,
    
    -- Kreditlinien pro Produkttyp (in TEUR)
    kl_neuwagen REAL DEFAULT 0,
    kl_vorfuehrwagen REAL DEFAULT 0,
    kl_gebrauchtwagen REAL DEFAULT 0,
    kl_leasingruecklaeufer REAL DEFAULT 0,
    kl_remarketing REAL DEFAULT 0,
    kl_anschlussfinanzierung REAL DEFAULT 0,
    kl_ersatzteile REAL DEFAULT 0,
    kl_direktkonto REAL DEFAULT 0,
    kl_vorauszahlung REAL DEFAULT 0,
    
    -- Kreditlinie TOTAL
    kreditlinie_total REAL NOT NULL,
    
    -- Aktueller Saldo
    saldo_total REAL NOT NULL,
    
    -- Salden pro Produkttyp (in TEUR)
    saldo_neuwagen REAL DEFAULT 0,
    saldo_vorfuehrwagen REAL DEFAULT 0,
    saldo_gebrauchtwagen REAL DEFAULT 0,
    saldo_leasingruecklaeufer REAL DEFAULT 0,
    saldo_remarketing REAL DEFAULT 0,
    saldo_anschlussfinanzierung REAL DEFAULT 0,
    saldo_ersatzteile REAL DEFAULT 0,
    saldo_direktkonto REAL DEFAULT 0,
    saldo_vorauszahlung REAL DEFAULT 0,
    
    -- Import-Tracking
    import_datei TEXT NOT NULL,
    import_datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadaten
    aktiv BOOLEAN DEFAULT 1,
    notizen TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(rrdi, marke)
);

CREATE INDEX idx_kreditlinien_rrdi ON kreditlinien(rrdi);
CREATE INDEX idx_kreditlinien_marke ON kreditlinien(marke);
CREATE INDEX idx_kreditlinien_aktiv ON kreditlinien(aktiv);

-- -----------------------------------------------------------------------------
-- 4.2 Kreditlinien Snapshots (Historische Daten)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kreditlinien_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kreditlinie_id INTEGER NOT NULL,
    
    -- Snapshot-Datum
    snapshot_datum DATE NOT NULL,
    
    -- Werte zum Snapshot-Zeitpunkt
    kreditlinie_total REAL NOT NULL,
    saldo_total REAL NOT NULL,
    
    -- Import-Info
    import_datei TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (kreditlinie_id) REFERENCES kreditlinien(id) ON DELETE CASCADE,
    UNIQUE(kreditlinie_id, snapshot_datum)
);

CREATE INDEX idx_kl_snapshots_kreditlinie ON kreditlinien_snapshots(kreditlinie_id);
CREATE INDEX idx_kl_snapshots_datum ON kreditlinien_snapshots(snapshot_datum);

-- ============================================================================
-- 5. IMPORT-TRACKING
-- ============================================================================

-- -----------------------------------------------------------------------------
-- 5.1 Import Log (Alle Imports tracken)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS import_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Import-Details
    import_typ TEXT CHECK(import_typ IN (
        'MT940',
        'CSV_SANTANDER',
        'CSV_HYUNDAI',
        'EXCEL_STELLANTIS'
    )) NOT NULL,
    dateiname TEXT NOT NULL,
    dateipfad TEXT,
    
    -- Ergebnis
    status TEXT CHECK(status IN ('Erfolg', 'Fehler', 'Teilweise')) NOT NULL,
    anzahl_zeilen_gelesen INTEGER DEFAULT 0,
    anzahl_zeilen_importiert INTEGER DEFAULT 0,
    anzahl_duplikate INTEGER DEFAULT 0,
    anzahl_fehler INTEGER DEFAULT 0,
    
    -- Timing
    import_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    import_ende TIMESTAMP,
    dauer_sekunden REAL,
    
    -- Details
    fehlermeldungen TEXT,
    notizen TEXT
);

CREATE INDEX idx_import_log_typ ON import_log(import_typ);
CREATE INDEX idx_import_log_datum ON import_log(import_start);
CREATE INDEX idx_import_log_status ON import_log(status);
CREATE INDEX idx_import_log_datei ON import_log(dateiname);

-- ============================================================================
-- 6. VIEWS FÜR REPORTING
-- ============================================================================

-- -----------------------------------------------------------------------------
-- 6.1 Aktueller Kontostand pro Konto
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_aktuelle_kontosalden AS
SELECT 
    k.id AS konto_id,
    k.kontoname,
    k.kontonummer,
    k.iban,
    b.bank_name,
    s.datum AS saldo_datum,
    s.saldo,
    s.waehrung,
    k.kreditlinie,
    (k.kreditlinie + s.saldo) AS verfuegbar
FROM konten k
JOIN banken b ON k.bank_id = b.id
LEFT JOIN salden s ON k.id = s.konto_id
WHERE k.aktiv = 1
AND s.datum = (
    SELECT MAX(datum) 
    FROM salden 
    WHERE konto_id = k.id
);

-- -----------------------------------------------------------------------------
-- 6.2 Fahrzeugfinanzierungen - Aktueller Stand
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_fahrzeugfinanzierungen_aktuell AS
SELECT 
    f.id,
    fb.bank_name,
    fb.bank_typ,
    f.vin,
    f.finanzierungsnummer,
    f.hersteller,
    f.modell,
    f.finanzierungsstatus,
    f.produktfamilie,
    f.finanzierungsbetrag,
    f.aktueller_saldo,
    f.zinsen_gesamt,
    f.zinsen_letzte_periode,
    f.vertragsbeginn,
    f.finanzierungsende,
    JULIANDAY(f.finanzierungsende) - JULIANDAY('now') AS tage_bis_ende,
    f.import_datum
FROM fahrzeugfinanzierungen f
JOIN finanzierungsbanken fb ON f.finanzbank_id = fb.id
WHERE f.aktiv = 1
ORDER BY f.aktueller_saldo DESC;

-- -----------------------------------------------------------------------------
-- 6.3 Kreditlinien - Aktueller Stand
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_kreditlinien_aktuell AS
SELECT 
    id,
    rrdi,
    marke,
    haendlername,
    kreditlinie_total,
    saldo_total,
    (kreditlinie_total - saldo_total) AS verfuegbar,
    ROUND((saldo_total * 100.0 / kreditlinie_total), 2) AS auslastung_prozent,
    import_datum
FROM kreditlinien
WHERE aktiv = 1
ORDER BY saldo_total DESC;

-- ============================================================================
-- 7. TRIGGERS
-- ============================================================================

-- -----------------------------------------------------------------------------
-- 7.1 Auto-Update Timestamps
-- -----------------------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS update_konten_timestamp
AFTER UPDATE ON konten
FOR EACH ROW
BEGIN
    UPDATE konten SET aktualisiert_am = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_banken_timestamp
AFTER UPDATE ON banken
FOR EACH ROW
BEGIN
    UPDATE banken SET aktualisiert_am = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_finanzbanken_timestamp
AFTER UPDATE ON finanzierungsbanken
FOR EACH ROW
BEGIN
    UPDATE finanzierungsbanken SET aktualisiert_am = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_fahrzeugfin_timestamp
AFTER UPDATE ON fahrzeugfinanzierungen
FOR EACH ROW
BEGIN
    UPDATE fahrzeugfinanzierungen SET aktualisiert_am = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_kreditlinien_timestamp
AFTER UPDATE ON kreditlinien
FOR EACH ROW
BEGIN
    UPDATE kreditlinien SET aktualisiert_am = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================================================
-- ENDE DES SCHEMAS
-- ============================================================================
