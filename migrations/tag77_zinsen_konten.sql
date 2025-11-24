-- TAG 77: Zinssätze und Umbuchungs-Feature
-- Datum: 2025-11-24

-- Konten-Tabelle erweitern
ALTER TABLE konten ADD COLUMN sollzins REAL;
ALTER TABLE konten ADD COLUMN habenzins REAL DEFAULT 0;
ALTER TABLE konten ADD COLUMN kreditlimit REAL DEFAULT 0;
ALTER TABLE konten ADD COLUMN mindest_saldo REAL DEFAULT 0;
ALTER TABLE konten ADD COLUMN umbuchung_moeglich BOOLEAN DEFAULT 1;

-- Zinssätze aus Kontoaufstellung.xlsx
UPDATE konten SET sollzins = 6.30, kreditlimit = 200000 WHERE id = 9;  -- HVB KK
UPDATE konten SET sollzins = 7.75, kreditlimit = 100000 WHERE id = 1;  -- Sparkasse KK
UPDATE konten SET sollzins = 6.73, kreditlimit = 500000 WHERE id = 5;  -- VR 57908 KK
UPDATE konten SET sollzins = 6.73, kreditlimit = 250000 WHERE id = 15; -- VR 1501500 HYU KK
UPDATE konten SET sollzins = 11.75, kreditlimit = 0 WHERE id = 14;     -- VR Landau KK
UPDATE konten SET sollzins = 6.73, kreditlimit = 0 WHERE id = 6;       -- VR 22225 Immo

-- EK-Finanzierung Konditionen
CREATE TABLE IF NOT EXISTS ek_finanzierung_konditionen (
    id INTEGER PRIMARY KEY,
    finanzinstitut TEXT UNIQUE,
    gesamt_limit REAL,
    zinssatz REAL,
    zinsfreie_tage INTEGER DEFAULT 0,
    gueltig_ab DATE,
    notizen TEXT
);

INSERT OR REPLACE INTO ek_finanzierung_konditionen 
(finanzinstitut, gesamt_limit, zinssatz, zinsfreie_tage, gueltig_ab, notizen)
VALUES 
('Stellantis', 5380000, 9.03, 0, '2025-01-01', 'Zinsfrei lt. Vertrag, dann 9.03%'),
('Santander', 1500000, NULL, 0, '2025-01-01', 'Variabler Zinssatz 4-5.5%'),
('Hyundai Finance', 4300000, 4.68, 0, '2025-01-01', 'Günstigster Zinssatz');
