-- Fahrzeuganlage: Scan-Archiv (PostgreSQL drive_portal)
-- Phase 1 MVP: Fahrzeugschein-OCR via AWS Bedrock, Speicherung in Portal-DB

CREATE TABLE IF NOT EXISTS fahrzeugschein_scans (
    id SERIAL PRIMARY KEY,
    scan_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    scanned_by TEXT,
    image_path TEXT,
    kennzeichen TEXT,
    fin TEXT,
    erstzulassung TEXT,
    marke TEXT,
    handelsbezeichnung TEXT,
    typ_variante_version TEXT,
    hsn TEXT,
    tsn TEXT,
    hubraum_ccm INTEGER,
    leistung_kw INTEGER,
    kraftstoff TEXT,
    farbe TEXT,
    naechste_hu TEXT,
    halter_name TEXT,
    halter_vorname TEXT,
    halter_strasse TEXT,
    halter_plz TEXT,
    halter_ort TEXT,
    status TEXT DEFAULT 'scanned',
    locosoft_exists INTEGER DEFAULT 0,
    locosoft_kunden_nr TEXT,
    locosoft_fahrzeug_nr TEXT,
    ocr_confidence REAL,
    raw_ocr_response TEXT,
    processing_region TEXT DEFAULT 'eu-central-1',
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_fahrzeugschein_scans_fin ON fahrzeugschein_scans(fin);
CREATE INDEX IF NOT EXISTS idx_fahrzeugschein_scans_kennzeichen ON fahrzeugschein_scans(kennzeichen);
CREATE INDEX IF NOT EXISTS idx_fahrzeugschein_scans_scan_date ON fahrzeugschein_scans(scan_date);
