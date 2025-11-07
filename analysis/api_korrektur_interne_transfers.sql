-- =====================================================
-- API-KORREKTUR: Interne Transfers filtern
-- Datum: 2025-11-07
-- =====================================================
-- Dieses Script zeigt die korrigierten Dashboard-Zahlen
-- und muss in die bankenspiegel_api.py integriert werden
-- =====================================================

.print ''
.print '========================================='
.print 'DASHBOARD-ZAHLEN KORREKTUR'
.print '========================================='
.print ''

.print '1. MIT INTERNEN TRANSFERS (AKTUELL - FALSCH):'
.print '---------------------------------------------'

SELECT 
    COUNT(*) as transaktionen,
    ROUND(SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END), 2) as einnahmen,
    ROUND(SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END), 2) as ausgaben,
    ROUND(SUM(betrag), 2) as saldo
FROM transaktionen
WHERE buchungsdatum >= DATE('now', '-30 days');

.print ''
.print '2. OHNE INTERNE TRANSFERS (KORRIGIERT - RICHTIG):'
.print '------------------------------------------------'

SELECT 
    COUNT(*) as transaktionen,
    ROUND(SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END), 2) as einnahmen,
    ROUND(SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END), 2) as ausgaben,
    ROUND(SUM(betrag), 2) as saldo
FROM transaktionen
WHERE buchungsdatum >= DATE('now', '-30 days')
  AND NOT (
    verwendungszweck LIKE '%Autohaus Greiner%Autohaus Greiner%'
    OR verwendungszweck LIKE '%Umbuchung%'
    OR verwendungszweck LIKE '%Einlage%'
    OR verwendungszweck LIKE '%Rückzahlung Einlage%'
    OR (verwendungszweck LIKE '%PN:801%' AND verwendungszweck LIKE '%Autohaus Greiner%')
  );

.print ''
.print '3. NUR INTERNE TRANSFERS (SEPARAT AUSWEISEN):'
.print '---------------------------------------------'

SELECT 
    COUNT(*) as transaktionen,
    ROUND(SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END), 2) as einnahmen,
    ROUND(SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END), 2) as ausgaben,
    ROUND(SUM(betrag), 2) as saldo
FROM transaktionen
WHERE buchungsdatum >= DATE('now', '-30 days')
  AND (
    verwendungszweck LIKE '%Autohaus Greiner%Autohaus Greiner%'
    OR verwendungszweck LIKE '%Umbuchung%'
    OR verwendungszweck LIKE '%Einlage%'
    OR verwendungszweck LIKE '%Rückzahlung Einlage%'
    OR (verwendungszweck LIKE '%PN:801%' AND verwendungszweck LIKE '%Autohaus Greiner%')
  );

.print ''
.print '========================================='
.print 'AKTUELLER MONAT (2025-11):'
.print '========================================='
.print ''

SELECT 
    'Mit Internen' as typ,
    COUNT(*) as transaktionen,
    ROUND(SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END), 2) as einnahmen,
    ROUND(SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END), 2) as ausgaben
FROM transaktionen
WHERE strftime('%Y-%m', buchungsdatum) = '2025-11';

SELECT 
    'Ohne Interne' as typ,
    COUNT(*) as transaktionen,
    ROUND(SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END), 2) as einnahmen,
    ROUND(SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END), 2) as ausgaben
FROM transaktionen
WHERE strftime('%Y-%m', buchungsdatum) = '2025-11'
  AND NOT (
    verwendungszweck LIKE '%Autohaus Greiner%Autohaus Greiner%'
    OR verwendungszweck LIKE '%Umbuchung%'
    OR verwendungszweck LIKE '%Einlage%'
    OR verwendungszweck LIKE '%Rückzahlung Einlage%'
    OR (verwendungszweck LIKE '%PN:801%' AND verwendungszweck LIKE '%Autohaus Greiner%')
  );

.print ''
.print '========================================='
.print 'FILTER-FUNKTION FÜR API:'
.print '========================================='
.print ''
.print 'Python-Funktion zum Filtern interner Transfers:'
.print ''
.print 'def is_internal_transfer(verwendungszweck):'
.print '    if not verwendungszweck:'
.print '        return False'
.print '    patterns = ['
.print '        "Autohaus Greiner" in verwendungszweck and verwendungszweck.count("Autohaus Greiner") > 1,'
.print '        "Umbuchung" in verwendungszweck,'
.print '        "Einlage" in verwendungszweck,'
.print '        "Rückzahlung Einlage" in verwendungszweck,'
.print '        ("PN:801" in verwendungszweck and "Autohaus Greiner" in verwendungszweck)'
.print '    ]'
.print '    return any(patterns)'
.print ''

.print '========================================='
.print 'SQL WHERE-CLAUSE FÜR API:'
.print '========================================='
.print ''
.print 'WHERE NOT ('
.print '  verwendungszweck LIKE "%Autohaus Greiner%Autohaus Greiner%"'
.print '  OR verwendungszweck LIKE "%Umbuchung%"'
.print '  OR verwendungszweck LIKE "%Einlage%"'
.print '  OR verwendungszweck LIKE "%Rückzahlung Einlage%"'
.print '  OR (verwendungszweck LIKE "%PN:801%" AND verwendungszweck LIKE "%Autohaus Greiner%")'
.print ')'
.print ''
