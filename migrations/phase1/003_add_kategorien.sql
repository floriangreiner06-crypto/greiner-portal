-- ============================================================================
-- MIGRATION 003: KATEGORIEN
-- ============================================================================
-- Beschreibung: Kategorien-System für Transaktions-Klassifizierung
-- Priorität: WICHTIG (benötigt für Auswertungen und Reports)
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

-- ============================================================================
-- STANDARD-KATEGORIEN ANLEGEN
-- ============================================================================

INSERT OR IGNORE INTO kategorien (kategorie_name, beschreibung, steuerrelevant, aktiv) VALUES
('Gehalt', 'Monatliche Gehaltszahlungen', 1, 1),
('Miete', 'Miet- und Pachtzahlungen', 1, 1),
('Büromaterial', 'Bürobedarf und Material', 1, 1),
('Reisekosten', 'Geschäftsreisen und Fahrtkosten', 1, 1),
('Versicherung', 'Versicherungsbeiträge', 1, 1),
('Telefon/Internet', 'Telekommunikationskosten', 1, 1),
('Beratung', 'Beratungs- und Consultingleistungen', 1, 1),
('Strom/Gas', 'Energiekosten', 1, 1),
('KFZ-Kosten', 'Fahrzeugkosten und Kraftstoff', 1, 1),
('Marketing', 'Marketing und Werbung', 1, 1),
('Software', 'Software-Lizenzen und IT-Dienste', 1, 1),
('Bankgebühren', 'Kontoführungsgebühren', 1, 1),
('Zinsen', 'Zinseinnahmen/-ausgaben', 1, 1),
('Steuern', 'Steuerzahlungen', 1, 1),
('Sonstige Einnahmen', 'Diverse Einnahmen', 0, 1),
('Sonstige Ausgaben', 'Diverse Ausgaben', 0, 1);

-- ============================================================================
-- VALIDIERUNG
-- ============================================================================

SELECT 
    'Migration 003 erfolgreich!' as Status,
    (SELECT COUNT(*) FROM kategorien) as Einträge_kategorien;
