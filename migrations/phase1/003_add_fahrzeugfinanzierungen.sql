-- ============================================================================
-- MIGRATION 003: FAHRZEUGFINANZIERUNGEN (STELLANTIS)
-- ============================================================================
-- Priorität: 🔴 KRITISCH
-- Beschreibung: Tracking aller finanzierten Fahrzeuge (Stellantis Bank)
-- Datum: 2025-11-07
-- ============================================================================

CREATE TABLE IF NOT EXISTS fahrzeugfinanzierungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Fahrzeugdaten
    rrdi TEXT,                           -- RRDI-Nummer (Identifikator)
    vin TEXT,                            -- Fahrzeug-Identifizierungsnummer
    modell TEXT,                         -- Fahrzeugmodell
    marke TEXT,                          -- Hersteller (z.B. Fiat, Opel, Peugeot)
    erstzulassung DATE,                  -- Datum der Erstzulassung
    
    -- Finanzierungsdaten
    finanzierungsbetrag_original REAL,   -- Original-Finanzierungsbetrag
    aktueller_saldo REAL,                -- Aktueller Restsaldo
    abbezahlt REAL,                      -- Bereits abbezahlter Betrag
    zinssatz REAL,                       -- Zinssatz in Prozent
    zinsfreiheit_bis DATE,               -- Datum bis Zinsfreiheit gilt
    finanzierung_beginn DATE,            -- Finanzierungsbeginn
    finanzierung_ende DATE,              -- Geplantes Finanzierungsende
    
    -- Statusdaten
    status TEXT CHECK(status IN ('Aktiv', 'Abbezahlt', 'Storniert', 'Rückabgewickelt')) DEFAULT 'Aktiv',
    im_bestand BOOLEAN DEFAULT 1,        -- Ist Fahrzeug noch im Bestand?
    verkauft_am DATE,                    -- Verkaufsdatum (wenn verkauft)
    
    -- LocoSoft-Integration
    locosoft_fahrzeug_id INTEGER,        -- Verknüpfung zu LocoSoft-Bestand
    letzter_abgleich_am TIMESTAMP,       -- Letzter Bestandsabgleich mit LocoSoft
    
    -- Metadaten
    notizen TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(rrdi)
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_fzgfin_rrdi ON fahrzeugfinanzierungen(rrdi);
CREATE INDEX IF NOT EXISTS idx_fzgfin_vin ON fahrzeugfinanzierungen(vin);
CREATE INDEX IF NOT EXISTS idx_fzgfin_status ON fahrzeugfinanzierungen(status);
CREATE INDEX IF NOT EXISTS idx_fzgfin_zinsfreiheit ON fahrzeugfinanzierungen(zinsfreiheit_bis);
CREATE INDEX IF NOT EXISTS idx_fzgfin_bestand ON fahrzeugfinanzierungen(im_bestand);

-- Trigger für automatische Aktualisierung
CREATE TRIGGER IF NOT EXISTS update_fahrzeugfin_timestamp 
AFTER UPDATE ON fahrzeugfinanzierungen
FOR EACH ROW
BEGIN
    UPDATE fahrzeugfinanzierungen SET aktualisiert_am = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Validierung
SELECT 'Migration 003: fahrzeugfinanzierungen-Tabelle erstellt' as Status;
SELECT COUNT(*) as 'Tabelle existiert (1=ja)' FROM sqlite_master WHERE type='table' AND name='fahrzeugfinanzierungen';
