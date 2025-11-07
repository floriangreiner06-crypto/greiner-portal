-- =====================================================
-- DUPLIKATE BEREINIGUNG - BANKENSPIEGEL
-- Datum: 2025-11-07
-- =====================================================
-- WICHTIG: Backup erstellen BEVOR dieses Script läuft!
-- Befehl: cp data/greiner_controlling.db data/greiner_controlling.db.backup_vor_bereinigung_$(date +%Y%m%d_%H%M%S)
-- =====================================================

.print ''
.print '========================================='
.print 'DUPLIKATE-BEREINIGUNG STARTET'
.print '========================================='
.print ''

.print '========================================='
.print 'SCHRITT 1: Vorher-Status'
.print '========================================='
.print ''

SELECT 
    COUNT(*) as transaktionen_gesamt,
    COUNT(DISTINCT konto_id || buchungsdatum || betrag || COALESCE(verwendungszweck,'')) as eindeutige_buchungen
FROM transaktionen;

.print ''
.print '========================================='
.print 'SCHRITT 2: Duplikate identifizieren'
.print '========================================='
.print ''

-- Temporäre Tabelle mit IDs zum BEHALTEN (jeweils die ERSTE Transaktion)
CREATE TEMP TABLE keep_ids AS
SELECT MIN(id) as id
FROM transaktionen
GROUP BY konto_id, buchungsdatum, betrag, verwendungszweck;

-- Statistik: Was wird passieren?
SELECT 
    (SELECT COUNT(*) FROM transaktionen) as vor_loeschung,
    (SELECT COUNT(*) FROM keep_ids) as bleiben,
    (SELECT COUNT(*) FROM transaktionen) - (SELECT COUNT(*) FROM keep_ids) as werden_geloescht;

.print ''
.print 'Warte 3 Sekunden vor Löschung...'
.print ''

.print '========================================='
.print 'SCHRITT 3: LÖSCHE Duplikate'
.print '========================================='
.print ''

-- TATSÄCHLICH LÖSCHEN - Behält MIN(id) jeder Gruppe
DELETE FROM transaktionen WHERE id NOT IN (SELECT id FROM keep_ids);

.print ''
SELECT 'Gelöschte Transaktionen: ' || changes() as ergebnis;
.print ''

.print '========================================='
.print 'SCHRITT 4: Nachher-Status'
.print '========================================='
.print ''

SELECT 
    COUNT(*) as transaktionen_gesamt,
    COUNT(DISTINCT konto_id || buchungsdatum || betrag || COALESCE(verwendungszweck,'')) as eindeutige_buchungen
FROM transaktionen;

.print ''
.print '========================================='
.print 'SCHRITT 5: Duplikate-Check (sollte 0 sein)'
.print '========================================='
.print ''

SELECT 
    COUNT(*) as verbleibende_duplikat_gruppen,
    COALESCE(SUM(anzahl - 1), 0) as sollte_null_sein
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
.print '========================================='
.print 'SCHRITT 6: Neue Dashboard-Zahlen (letzte 30 Tage)'
.print '========================================='
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

-- Temp-Tabelle aufräumen
DROP TABLE keep_ids;

.print ''
.print '========================================='
.print 'BEREINIGUNG KOMPLETT! ✅'
.print '========================================='
.print ''
.print 'Nächste Schritte:'
.print '1. Prüfe die neuen Dashboard-Zahlen'
.print '2. Teste die API: curl http://localhost:5000/api/bankenspiegel/dashboard'
.print '3. Falls alles OK: Altes Backup kann behalten werden'
.print ''
