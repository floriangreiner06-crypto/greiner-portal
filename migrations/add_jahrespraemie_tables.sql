-- ============================================================================
-- JAHRESPRÄMIE MODUL - DATENBANK-SCHEMA
-- ============================================================================
-- Erstellt: 2025-12-01 (TAG 87)
-- Für: Greiner DRIVE
-- ============================================================================

-- Haupttabelle: Berechnungen
CREATE TABLE IF NOT EXISTS praemien_berechnungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Wirtschaftsjahr
    wirtschaftsjahr TEXT NOT NULL UNIQUE,  -- z.B. "2024/2025"
    wj_start DATE NOT NULL,                -- z.B. "2024-09-01"
    wj_ende DATE NOT NULL,                 -- z.B. "2025-08-31"
    
    -- Prämientopf
    praemientopf REAL NOT NULL,            -- Gesamtbetrag in EUR
    kulanz_volumen REAL DEFAULT 0,         -- Abzug für Kulanz
    bereinigter_topf REAL,                 -- praemientopf - kulanz_volumen
    
    -- Berechnungsparameter
    vz_tz_grenze REAL DEFAULT 30,          -- Stunden/Woche Grenze VZ/TZ
    hoechstes_festgehalt REAL,             -- Für Deckelung
    hoechstes_festgehalt_ma_id INTEGER,    -- Wer hat das höchste?
    berechnungsbasis REAL,                 -- Summe aller gekappten Gehälter
    
    -- Prämien-Töpfe (je 50%)
    praemie_I_topf REAL,                   -- Lohnanteil
    praemie_II_topf REAL,                  -- Pro-Kopf
    
    -- Pro-Kopf-Beträge
    prokopf_vollzeit REAL,
    prokopf_teilzeit REAL,
    prokopf_minijob REAL,
    prokopf_azubi_1 REAL DEFAULT 100,
    prokopf_azubi_2 REAL DEFAULT 125,
    prokopf_azubi_3 REAL DEFAULT 150,
    
    -- Mitarbeiter-Zählung
    anzahl_gesamt INTEGER DEFAULT 0,
    anzahl_vollzeit INTEGER DEFAULT 0,
    anzahl_teilzeit INTEGER DEFAULT 0,
    anzahl_minijob INTEGER DEFAULT 0,
    anzahl_azubi_1 INTEGER DEFAULT 0,
    anzahl_azubi_2 INTEGER DEFAULT 0,
    anzahl_azubi_3 INTEGER DEFAULT 0,
    
    -- Lohnjournal
    lohnjournal_datei TEXT,
    lohnjournal_hash TEXT,
    
    -- Status & Workflow
    status TEXT DEFAULT 'entwurf',         -- entwurf, berechnet, freigegeben, exportiert
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    geaendert_am DATETIME,
    freigegeben_am DATETIME,
    freigegeben_von TEXT,
    
    FOREIGN KEY (hoechstes_festgehalt_ma_id) REFERENCES praemien_mitarbeiter(id)
);

-- Mitarbeiter pro Berechnung
CREATE TABLE IF NOT EXISTS praemien_mitarbeiter (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    berechnung_id INTEGER NOT NULL,
    
    -- Personaldaten (aus Lohnjournal)
    personalnummer TEXT,
    vorname TEXT,
    nachname TEXT,
    eintritt DATE,
    austritt DATE,
    std_woche REAL,
    taetigkeit TEXT,
    ang_arb TEXT,                          -- Angestellter/Arbeiter/Azubi
    
    -- Berechnet
    kategorie TEXT,                        -- Vollzeit, Teilzeit, Minijob, Azubi_1/2/3
    ist_festgehalt INTEGER DEFAULT 1,      -- 1=Festgehalt, 0=Variable (Verkäufer)
    jahresbrutto REAL,
    jahresbrutto_gekappt REAL,             -- Gekappt auf höchstes Festgehalt
    
    -- Berechtigung
    ist_berechtigt INTEGER DEFAULT 0,
    berechtigung_grund TEXT,
    
    -- Kulanz
    ist_kulanz INTEGER DEFAULT 0,
    kulanz_betrag REAL,
    kulanz_grund TEXT,
    
    -- Prämien
    anteil_lohnsumme REAL,                 -- Anteil an Berechnungsbasis
    praemie_I REAL DEFAULT 0,              -- Lohnanteil
    praemie_II REAL DEFAULT 0,             -- Pro-Kopf
    praemie_gesamt REAL DEFAULT 0,
    praemie_gerundet INTEGER DEFAULT 0,    -- Kaufmännisch gerundet
    
    FOREIGN KEY (berechnung_id) REFERENCES praemien_berechnungen(id) ON DELETE CASCADE
);

-- Kulanz-Regeln (wiederverwendbar)
CREATE TABLE IF NOT EXISTS praemien_kulanz_regeln (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    berechnung_id INTEGER NOT NULL,
    
    regel_typ TEXT NOT NULL,               -- 'kategorie' oder 'individuell'
    kategorie TEXT,                        -- Bei Kategorie-Regel: Minijob, Teilzeit, etc.
    pauschal_betrag REAL,                  -- Fester Betrag
    
    mitarbeiter_id INTEGER,                -- Bei individueller Regel
    beschreibung TEXT,
    
    aktiv INTEGER DEFAULT 1,
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (berechnung_id) REFERENCES praemien_berechnungen(id) ON DELETE CASCADE,
    FOREIGN KEY (mitarbeiter_id) REFERENCES praemien_mitarbeiter(id)
);

-- Export-Historie
CREATE TABLE IF NOT EXISTS praemien_exporte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    berechnung_id INTEGER NOT NULL,
    
    export_typ TEXT NOT NULL,              -- pdf_einzeln, pdf_gesamt, excel, csv
    dateiname TEXT,
    dateipfad TEXT,
    
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    erstellt_von TEXT,
    
    FOREIGN KEY (berechnung_id) REFERENCES praemien_berechnungen(id) ON DELETE CASCADE
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_praemien_ma_berechnung ON praemien_mitarbeiter(berechnung_id);
CREATE INDEX IF NOT EXISTS idx_praemien_ma_kategorie ON praemien_mitarbeiter(kategorie);
CREATE INDEX IF NOT EXISTS idx_praemien_ma_berechtigt ON praemien_mitarbeiter(ist_berechtigt);
CREATE INDEX IF NOT EXISTS idx_praemien_kulanz_berechnung ON praemien_kulanz_regeln(berechnung_id);
CREATE INDEX IF NOT EXISTS idx_praemien_exporte_berechnung ON praemien_exporte(berechnung_id);

-- Views für Übersicht
CREATE VIEW IF NOT EXISTS v_praemien_uebersicht AS
SELECT 
    b.id,
    b.wirtschaftsjahr,
    b.praemientopf,
    b.bereinigter_topf,
    b.anzahl_gesamt,
    b.status,
    b.erstellt_am,
    COALESCE(SUM(m.praemie_gerundet), 0) as summe_praemien,
    COUNT(CASE WHEN m.ist_berechtigt = 1 THEN 1 END) as anzahl_berechtigt
FROM praemien_berechnungen b
LEFT JOIN praemien_mitarbeiter m ON b.id = m.berechnung_id
GROUP BY b.id;

CREATE VIEW IF NOT EXISTS v_praemien_mitarbeiter_detail AS
SELECT 
    m.*,
    b.wirtschaftsjahr,
    b.praemientopf,
    b.status as berechnung_status
FROM praemien_mitarbeiter m
JOIN praemien_berechnungen b ON m.berechnung_id = b.id;
