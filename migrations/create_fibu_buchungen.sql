-- =====================================================
-- MIGRATION: FIBU-Buchungen aus Locosoft
-- Datum: 2025-11-14
-- Zweck: Zinsen, Gebühren, FIBU-Auswertungen
-- =====================================================

-- =====================================================
-- TABELLE: fibu_buchungen
-- =====================================================

CREATE TABLE IF NOT EXISTS fibu_buchungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Locosoft-Referenzen (für Deduplizierung)
    locosoft_doc_number BIGINT NOT NULL,
    locosoft_position BIGINT NOT NULL,
    
    -- Buchungsdaten
    accounting_date DATE NOT NULL,
    nominal_account INTEGER NOT NULL,
    amount REAL NOT NULL,              -- Betrag in EURO (bereits konvertiert!)
    debit_credit TEXT,                 -- 'S' (Soll) oder 'H' (Haben)
    posting_text TEXT,
    
    -- Kategorisierung
    buchungstyp TEXT,                  -- 'zinsen', 'gebuehren', 'miete', 'sonstiges'
    
    -- Optional: Fahrzeug-Referenz
    vehicle_reference TEXT,
    
    -- Meta
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique-Constraint für Deduplizierung
    UNIQUE(locosoft_doc_number, locosoft_position)
);

-- =====================================================
-- INDIZES
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_fibu_date 
ON fibu_buchungen(accounting_date);

CREATE INDEX IF NOT EXISTS idx_fibu_account 
ON fibu_buchungen(nominal_account);

CREATE INDEX IF NOT EXISTS idx_fibu_typ 
ON fibu_buchungen(buchungstyp);

CREATE INDEX IF NOT EXISTS idx_fibu_debit_credit 
ON fibu_buchungen(debit_credit);

CREATE INDEX IF NOT EXISTS idx_fibu_synced 
ON fibu_buchungen(synced_at);

-- =====================================================
-- VIEW: v_zinsbuchungen (nur Zinsen mit Bank-Gruppierung)
-- =====================================================

CREATE VIEW IF NOT EXISTS v_zinsbuchungen AS
SELECT 
    id,
    accounting_date,
    nominal_account,
    amount,
    debit_credit,
    posting_text,
    vehicle_reference,
    -- Bank-Gruppierung basierend auf Sachkonto & Text
    CASE 
        WHEN nominal_account IN (230011, 230101, 230311) 
             OR LOWER(posting_text) LIKE '%stellantis%'
             OR LOWER(posting_text) LIKE '%santander%'
        THEN 'Stellantis/Santander'
        
        WHEN nominal_account = 233001 
             OR LOWER(posting_text) LIKE '%genobank%'
             OR LOWER(posting_text) LIKE '%geno bank%'
        THEN 'Genobank'
        
        WHEN LOWER(posting_text) LIKE '%sparkasse%'
        THEN 'Sparkasse'
        
        WHEN LOWER(posting_text) LIKE '%hypovereinsbank%'
             OR LOWER(posting_text) LIKE '%hvb%'
        THEN 'HypoVereinsbank'
        
        ELSE 'Sonstige'
    END as bank_gruppe,
    synced_at
FROM fibu_buchungen
WHERE buchungstyp = 'zinsen'
ORDER BY accounting_date DESC;

-- =====================================================
-- VIEW: v_zinsen_monatlich (Zinsen pro Monat aggregiert)
-- =====================================================

CREATE VIEW IF NOT EXISTS v_zinsen_monatlich AS
SELECT 
    strftime('%Y-%m', accounting_date) as monat,
    COUNT(*) as anzahl_buchungen,
    SUM(CASE WHEN debit_credit = 'S' THEN amount ELSE -amount END) as zinsen_soll,
    SUM(CASE WHEN debit_credit = 'H' THEN amount ELSE -amount END) as zinsen_haben,
    SUM(CASE WHEN debit_credit = 'S' THEN amount ELSE -amount END) as zinsen_netto,
    
    -- Nach Banken aufschlüsseln
    SUM(CASE 
        WHEN (nominal_account IN (230011, 230101, 230311) 
              OR LOWER(posting_text) LIKE '%stellantis%'
              OR LOWER(posting_text) LIKE '%santander%')
             AND debit_credit = 'S'
        THEN amount 
        ELSE 0 
    END) as stellantis_santander,
    
    SUM(CASE 
        WHEN (nominal_account = 233001 
              OR LOWER(posting_text) LIKE '%genobank%')
             AND debit_credit = 'S'
        THEN amount 
        ELSE 0 
    END) as genobank,
    
    SUM(CASE 
        WHEN LOWER(posting_text) LIKE '%sparkasse%'
             AND debit_credit = 'S'
        THEN amount 
        ELSE 0 
    END) as sparkasse,
    
    MAX(synced_at) as letzter_sync
FROM fibu_buchungen
WHERE buchungstyp = 'zinsen'
GROUP BY strftime('%Y-%m', accounting_date)
ORDER BY monat DESC;

-- =====================================================
-- STATISTIK-ABFRAGEN (für Validierung nach Import)
-- =====================================================

-- Diese Queries kannst du nach dem Import ausführen:

/*
-- Gesamt-Übersicht nach Buchungstyp:
SELECT 
    buchungstyp,
    COUNT(*) as anzahl,
    SUM(CASE WHEN debit_credit = 'S' THEN amount ELSE -amount END) as saldo_soll,
    MIN(accounting_date) as von,
    MAX(accounting_date) as bis
FROM fibu_buchungen
GROUP BY buchungstyp
ORDER BY anzahl DESC;

-- Zinsen pro Monat:
SELECT * FROM v_zinsen_monatlich LIMIT 12;

-- Letzte Zinsbuchungen:
SELECT * FROM v_zinsbuchungen ORDER BY accounting_date DESC LIMIT 10;

-- Buchungen nach Sachkonto (Top 10):
SELECT 
    nominal_account,
    COUNT(*) as anzahl,
    buchungstyp,
    SUM(amount) as summe
FROM fibu_buchungen
GROUP BY nominal_account, buchungstyp
ORDER BY anzahl DESC
LIMIT 10;
*/

-- =====================================================
-- INSTALLATION
-- =====================================================

-- Ausführen mit:
-- cd /opt/greiner-portal
-- sqlite3 data/greiner_controlling.db < migrations/create_fibu_buchungen.sql
--
-- Validieren:
-- sqlite3 data/greiner_controlling.db "SELECT COUNT(*) FROM fibu_buchungen;"
-- sqlite3 data/greiner_controlling.db "SELECT * FROM v_zinsen_monatlich LIMIT 5;"

-- =====================================================
-- ENDE MIGRATION
-- =====================================================
