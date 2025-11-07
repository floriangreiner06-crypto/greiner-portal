-- ============================================================================
-- MIGRATION 005: KATEGORIEN
-- ============================================================================
-- Priorität: 🟡 MITTEL
-- Beschreibung: Kategorisierung von Transaktionen für Auswertungen
-- Datum: 2025-11-07
-- ============================================================================

CREATE TABLE IF NOT EXISTS kategorien (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kategorie_name TEXT NOT NULL UNIQUE,
    uebergeordnete_kategorie TEXT,
    beschreibung TEXT,
    steuerrelevant BOOLEAN DEFAULT 0,
    aktiv BOOLEAN DEFAULT 1,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kategorien_aktiv ON kategorien(aktiv);

-- Standard-Kategorien einfügen
INSERT OR IGNORE INTO kategorien (kategorie_name, beschreibung, steuerrelevant, aktiv) VALUES
('Gehalt', 'Monatliche Gehaltszahlungen', 1, 1),
('Miete', 'Miet- und Pachtzahlungen', 1, 1),
('Büromaterial', 'Bürobedarf und Material', 1, 1),
('Reisekosten', 'Geschäftsreisen und Fahrtkosten', 1, 1),
('Versicherung', 'Versicherungsbeiträge', 1, 1),
('Telefon/Internet', 'Telekommunikationskosten', 1, 1),
('Beratung', 'Beratungs- und Consultingleistungen', 1, 1),
('Strom/Gas', 'Energiekosten', 1, 1),
('Bankgebühren', 'Kontoführung und Gebühren', 1, 1),
('Fahrzeugkosten', 'KFZ-Kosten (Stellantis)', 1, 1),
('Sonstige Einnahmen', 'Diverse Einnahmen', 0, 1),
('Sonstige Ausgaben', 'Diverse Ausgaben', 0, 1);

-- Validierung
SELECT 'Migration 005: kategorien-Tabelle erstellt' as Status;
SELECT COUNT(*) as 'Kategorien angelegt' FROM kategorien;
