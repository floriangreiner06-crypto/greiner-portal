-- ============================================================================
-- MIGRATION 004: REPORTING-VIEWS
-- ============================================================================
-- Priorität: 🔴 HOCH
-- Beschreibung: Views für Dashboard, Charts und Reporting
-- Datum: 2025-11-07
-- ============================================================================

-- View 1: Aktuelle Kontostände
-- Zeigt den aktuellsten Kontostand pro Konto
CREATE VIEW IF NOT EXISTS v_aktuelle_kontostaende AS
SELECT 
    b.bank_name,
    k.kontoname,
    k.iban,
    k.kontotyp,
    k.waehrung,
    kh.saldo,
    kh.datum as stand_datum,
    k.aktiv
FROM konten k
JOIN banken b ON k.bank_id = b.id
LEFT JOIN kontostand_historie kh ON k.id = kh.konto_id
LEFT JOIN (
    SELECT konto_id, MAX(datum) as max_datum
    FROM kontostand_historie
    GROUP BY konto_id
) latest ON kh.konto_id = latest.konto_id AND kh.datum = latest.max_datum
WHERE k.aktiv = 1;

-- View 2: Transaktionsübersicht mit Bank- und Kontoinfos
CREATE VIEW IF NOT EXISTS v_transaktionen_uebersicht AS
SELECT 
    t.id,
    b.bank_name,
    k.kontoname,
    k.iban,
    t.buchungsdatum,
    t.valutadatum,
    t.buchungstext,
    t.verwendungszweck,
    t.betrag,
    t.waehrung,
    t.kategorie,
    t.steuerrelevant,
    t.pdf_quelle
FROM transaktionen t
JOIN konten k ON t.konto_id = k.id
JOIN banken b ON k.bank_id = b.id;

-- View 3: Monatliche Umsätze (für Charts)
CREATE VIEW IF NOT EXISTS v_monatliche_umsaetze AS
SELECT 
    b.bank_name,
    k.kontoname,
    strftime('%Y-%m', t.buchungsdatum) as monat,
    SUM(CASE WHEN t.betrag > 0 THEN t.betrag ELSE 0 END) as einnahmen,
    SUM(CASE WHEN t.betrag < 0 THEN ABS(t.betrag) ELSE 0 END) as ausgaben,
    SUM(t.betrag) as saldo,
    COUNT(*) as anzahl_transaktionen
FROM transaktionen t
JOIN konten k ON t.konto_id = k.id
JOIN banken b ON k.bank_id = b.id
GROUP BY b.bank_name, k.kontoname, strftime('%Y-%m', t.buchungsdatum);

-- View 4: Kategorieauswertung
CREATE VIEW IF NOT EXISTS v_kategorie_auswertung AS
SELECT 
    t.kategorie,
    COUNT(*) as anzahl,
    SUM(t.betrag) as summe,
    AVG(t.betrag) as durchschnitt,
    MIN(t.buchungsdatum) as erste_buchung,
    MAX(t.buchungsdatum) as letzte_buchung
FROM transaktionen t
WHERE t.kategorie IS NOT NULL
GROUP BY t.kategorie;

-- Validierung
SELECT 'Migration 004: Reporting-Views erstellt' as Status;
SELECT COUNT(*) as 'Views erstellt' FROM sqlite_master 
WHERE type='view' AND name IN (
    'v_aktuelle_kontostaende',
    'v_transaktionen_uebersicht', 
    'v_monatliche_umsaetze',
    'v_kategorie_auswertung'
);
