-- ============================================================================
-- STELLANTIS BESTELLUNGEN - DATENBANK SCHEMA
-- ============================================================================
-- Erstellt: TAG 72
-- Zweck: Import von Stellantis ServiceBox Bestellungen
-- Quelle: servicebox_bestellungen_details_complete.json
-- ============================================================================

-- Haupttabelle: Bestellungen
CREATE TABLE IF NOT EXISTS stellantis_bestellungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Identifikation
    bestellnummer TEXT UNIQUE NOT NULL,
    bestelldatum DATETIME,
    
    -- Absender (BTZ Bayerische Teilezentrum)
    absender_code TEXT,
    absender_name TEXT,
    
    -- Empfänger (Autohaus Greiner)
    empfaenger_code TEXT,
    
    -- Kommentare
    lokale_nr TEXT,  -- Interne Bestellnummer (z.B. A38553, Lager, OV13)
    
    -- Meta
    url TEXT,  -- ServiceBox Detail-URL
    import_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    import_datei TEXT,  -- Quell-JSON-Datei
    
    -- Constraints
    CONSTRAINT unique_bestellnummer UNIQUE (bestellnummer)
);

-- Positionen-Tabelle
CREATE TABLE IF NOT EXISTS stellantis_positionen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bestellung_id INTEGER NOT NULL,
    
    -- Position Details
    teilenummer TEXT NOT NULL,
    beschreibung TEXT,
    
    -- Mengen
    menge REAL,  -- Bestellte Menge
    menge_in_lieferung REAL,  -- Bereits geliefert
    menge_in_bestellung REAL,  -- Noch in Bestellung
    
    -- Preise (als Text aus JSON)
    preis_ohne_mwst_text TEXT,
    preis_mit_mwst_text TEXT,
    summe_inkl_mwst_text TEXT,
    
    -- Preise (numerisch geparst)
    preis_ohne_mwst REAL,
    preis_mit_mwst REAL,
    summe_inkl_mwst REAL,
    
    -- Meta
    import_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key
    FOREIGN KEY (bestellung_id) REFERENCES stellantis_bestellungen(id) ON DELETE CASCADE
);

-- ============================================================================
-- INDIZES FÜR PERFORMANCE
-- ============================================================================

-- Bestellungen
CREATE INDEX IF NOT EXISTS idx_stellantis_bestellungen_datum 
    ON stellantis_bestellungen(bestelldatum);

CREATE INDEX IF NOT EXISTS idx_stellantis_bestellungen_absender 
    ON stellantis_bestellungen(absender_code);

CREATE INDEX IF NOT EXISTS idx_stellantis_bestellungen_empfaenger 
    ON stellantis_bestellungen(empfaenger_code);

CREATE INDEX IF NOT EXISTS idx_stellantis_bestellungen_lokale_nr 
    ON stellantis_bestellungen(lokale_nr);

CREATE INDEX IF NOT EXISTS idx_stellantis_bestellungen_import 
    ON stellantis_bestellungen(import_timestamp);

-- Positionen
CREATE INDEX IF NOT EXISTS idx_stellantis_positionen_bestellung 
    ON stellantis_positionen(bestellung_id);

CREATE INDEX IF NOT EXISTS idx_stellantis_positionen_teilenummer 
    ON stellantis_positionen(teilenummer);

CREATE INDEX IF NOT EXISTS idx_stellantis_positionen_beschreibung 
    ON stellantis_positionen(beschreibung);

-- ============================================================================
-- VIEWS FÜR EINFACHE QUERIES
-- ============================================================================

-- View: Bestellungen mit Anzahl Positionen
CREATE VIEW IF NOT EXISTS v_stellantis_bestellungen_overview AS
SELECT 
    b.id,
    b.bestellnummer,
    b.bestelldatum,
    b.absender_code,
    b.absender_name,
    b.empfaenger_code,
    b.lokale_nr,
    COUNT(p.id) as anzahl_positionen,
    SUM(p.summe_inkl_mwst) as gesamt_betrag,
    b.import_timestamp
FROM stellantis_bestellungen b
LEFT JOIN stellantis_positionen p ON b.id = p.bestellung_id
GROUP BY b.id;

-- View: Top Teile nach Häufigkeit
CREATE VIEW IF NOT EXISTS v_stellantis_top_teile AS
SELECT 
    p.teilenummer,
    p.beschreibung,
    COUNT(*) as anzahl_bestellungen,
    SUM(p.menge) as gesamt_menge,
    AVG(p.preis_mit_mwst) as durchschnittspreis,
    SUM(p.summe_inkl_mwst) as gesamt_umsatz
FROM stellantis_positionen p
GROUP BY p.teilenummer, p.beschreibung
ORDER BY anzahl_bestellungen DESC;

-- View: Bestellungen pro Tag
CREATE VIEW IF NOT EXISTS v_stellantis_bestellungen_pro_tag AS
SELECT 
    DATE(bestelldatum) as datum,
    COUNT(*) as anzahl_bestellungen,
    SUM((SELECT SUM(summe_inkl_mwst) FROM stellantis_positionen WHERE bestellung_id = b.id)) as gesamt_betrag
FROM stellantis_bestellungen b
WHERE bestelldatum IS NOT NULL
GROUP BY DATE(bestelldatum)
ORDER BY datum DESC;

-- ============================================================================
-- HILFSFUNKTIONEN / TRIGGER (OPTIONAL)
-- ============================================================================

-- Trigger: Aktualisiere import_timestamp bei Änderung
CREATE TRIGGER IF NOT EXISTS trg_stellantis_bestellungen_update
AFTER UPDATE ON stellantis_bestellungen
FOR EACH ROW
BEGIN
    UPDATE stellantis_bestellungen 
    SET import_timestamp = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- ============================================================================
-- ENDE SCHEMA
-- ============================================================================
