-- ============================================================================
-- MIGRATION 005: REPORTING VIEWS
-- ============================================================================
-- Beschreibung: Wichtigste Views für Dashboard und Reporting
-- Priorität: KRITISCH (benötigt für API und Frontend)
-- ============================================================================

-- ============================================================================
-- VIEW 1: Aktuelle Kontostände
-- ============================================================================

DROP VIEW IF EXISTS v_aktuelle_kontostaende;

CREATE VIEW v_aktuelle_kontostaende AS
SELECT 
    b.bank_name,
    k.id as konto_id,
    k.kontoname,
    k.iban,
    k.kontotyp,
    k.waehrung,
    COALESCE(kh.saldo, 0.0) as saldo,
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

-- ============================================================================
-- VIEW 2: Monatliche Umsätze
-- ============================================================================

DROP VIEW IF EXISTS v_monatliche_umsaetze;

CREATE VIEW v_monatliche_umsaetze AS
SELECT 
    b.bank_name,
    k.id as konto_id,
    k.kontoname,
    strftime('%Y-%m', t.buchungsdatum) as monat,
    SUM(CASE WHEN t.betrag > 0 THEN t.betrag ELSE 0 END) as einnahmen,
    SUM(CASE WHEN t.betrag < 0 THEN ABS(t.betrag) ELSE 0 END) as ausgaben,
    SUM(t.betrag) as saldo,
    COUNT(*) as anzahl_transaktionen
FROM transaktionen t
JOIN konten k ON t.konto_id = k.id
JOIN banken b ON k.bank_id = b.id
GROUP BY b.bank_name, k.id, k.kontoname, strftime('%Y-%m', t.buchungsdatum);

-- ============================================================================
-- VIEW 3: Transaktionsübersicht (erweitert)
-- ============================================================================

DROP VIEW IF EXISTS v_transaktionen_uebersicht;

CREATE VIEW v_transaktionen_uebersicht AS
SELECT 
    t.id,
    b.bank_name,
    k.id as konto_id,
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
    t.pdf_quelle,
    t.saldo_nach_buchung
FROM transaktionen t
JOIN konten k ON t.konto_id = k.id
JOIN banken b ON k.bank_id = b.id;

-- ============================================================================
-- VIEW 4: Kategorieauswertung
-- ============================================================================

DROP VIEW IF EXISTS v_kategorie_auswertung;

CREATE VIEW v_kategorie_auswertung AS
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

-- ============================================================================
-- VALIDIERUNG
-- ============================================================================

SELECT 
    'Migration 005 erfolgreich!' as Status,
    (SELECT COUNT(*) FROM v_aktuelle_kontostaende) as Konten_mit_Saldo,
    (SELECT COUNT(DISTINCT monat) FROM v_monatliche_umsaetze) as Monate_mit_Umsaetzen,
    (SELECT COUNT(*) FROM v_transaktionen_uebersicht) as Transaktionen_in_View,
    (SELECT COUNT(*) FROM v_kategorie_auswertung) as Kategorien_in_Nutzung;
