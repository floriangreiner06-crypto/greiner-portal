-- =====================================================
-- DUPLIKATE-ANALYSE BANKENSPIEGEL
-- Datum: 2025-11-07
-- =====================================================

.headers on
.mode column
.width 10 12 12 50 8 12

.print ''
.print '============================================='
.print '1. DUPLIKATE IN LETZTEN 30 TAGEN'
.print '============================================='
.print ''

SELECT 
    konto_id,
    buchungsdatum,
    betrag,
    SUBSTR(verwendungszweck, 1, 50) as verwendungszweck_kurz,
    COUNT(*) as anzahl,
    SUM(betrag) as summe
FROM transaktionen
WHERE buchungsdatum >= DATE('now', '-30 days')
GROUP BY konto_id, buchungsdatum, betrag, verwendungszweck
HAVING COUNT(*) > 1
ORDER BY anzahl DESC
LIMIT 20;

.print ''
.print '============================================='
.print '2. PDF-IMPORT-HÄUFIGKEIT'
.print '============================================='
.print ''

SELECT 
    SUBSTR(pdf_quelle, 1, 60) as pdf_quelle,
    COUNT(*) as anzahl_transaktionen,
    COUNT(DISTINCT buchungsdatum) as verschiedene_tage,
    MIN(buchungsdatum) as erste_buchung,
    MAX(buchungsdatum) as letzte_buchung
FROM transaktionen
WHERE pdf_quelle IS NOT NULL
GROUP BY pdf_quelle
HAVING anzahl_transaktionen > 50
ORDER BY anzahl_transaktionen DESC
LIMIT 20;

.print ''
.print '============================================='
.print '3. ZEITRAUM-LOGIK PRÜFEN'
.print '============================================='
.print ''

SELECT 
    DATE('now', '-30 days') as von_datum,
    DATE('now') as bis_datum,
    COUNT(*) as anzahl_transaktionen,
    ROUND(SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END), 2) as einnahmen,
    ROUND(SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END), 2) as ausgaben,
    ROUND(SUM(betrag), 2) as saldo
FROM transaktionen
WHERE buchungsdatum >= DATE('now', '-30 days')
  AND buchungsdatum <= DATE('now');

.print ''
.print '============================================='
.print '4. GESAMT-STATISTIK'
.print '============================================='
.print ''

SELECT 
    'Gesamt' as zeitraum,
    COUNT(*) as transaktionen,
    COUNT(DISTINCT konto_id) as konten,
    COUNT(DISTINCT pdf_quelle) as pdf_quellen,
    MIN(buchungsdatum) as aelteste,
    MAX(buchungsdatum) as neueste
FROM transaktionen;

.print ''
.print '============================================='
.print '5. DUPLIKATE GESAMT (NICHT NUR 30 TAGE)'
.print '============================================='
.print ''

SELECT 
    COUNT(*) as duplikat_gruppen,
    SUM(anzahl) as gesamt_duplikate,
    SUM(anzahl - 1) as zu_loeschende
FROM (
    SELECT 
        konto_id,
        buchungsdatum,
        betrag,
        verwendungszweck,
        COUNT(*) as anzahl
    FROM transaktionen
    GROUP BY konto_id, buchungsdatum, betrag, verwendungszweck
    HAVING COUNT(*) > 1
);

.print ''
.print '============================================='
.print 'ANALYSE KOMPLETT'
.print '============================================='
.print ''
