-- ============================================================================
-- MIGRATION: ERWEITERTE KATEGORISIERUNG FÜR FIBU-BUCHUNGEN
-- ============================================================================
-- Datum: 2025-11-14
-- Tag: 45
-- Zweck: Erweiterte Kategorisierung für Liquiditäts-Management
--
-- ÄNDERUNGEN:
-- 1. Neue Spalte: kategorie_erweitert (detaillierte Kategorien)
-- 2. Neue Spalte: wirtschaftsjahr (für WJ-Auswertungen)
-- 3. Neue View: v_cashflow_kategorien (Umsatz/Kosten nach Kategorie)
-- ============================================================================

BEGIN TRANSACTION;

-- ============================================================================
-- 1. NEUE SPALTEN HINZUFÜGEN
-- ============================================================================

-- Erweiterte Kategorisierung (nur für Bereiche 70-89)
ALTER TABLE fibu_buchungen 
ADD COLUMN kategorie_erweitert TEXT;

-- Wirtschaftsjahr (Format: "2024/2025")
ALTER TABLE fibu_buchungen 
ADD COLUMN wirtschaftsjahr TEXT;

-- ============================================================================
-- 2. INDEX FÜR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_fibu_kategorie_erweitert 
ON fibu_buchungen(kategorie_erweitert);

CREATE INDEX IF NOT EXISTS idx_fibu_wirtschaftsjahr 
ON fibu_buchungen(wirtschaftsjahr);

-- ============================================================================
-- 3. VIEW: CASHFLOW NACH KATEGORIEN
-- ============================================================================

DROP VIEW IF EXISTS v_cashflow_kategorien;

CREATE VIEW v_cashflow_kategorien AS
SELECT 
    wirtschaftsjahr,
    strftime('%Y-%m', accounting_date) as monat,
    kategorie_erweitert,
    COUNT(*) as anzahl_buchungen,
    
    -- Kosten (Soll)
    ROUND(SUM(CASE WHEN debit_credit = 'S' THEN amount ELSE 0 END), 2) as kosten,
    
    -- Umsätze (Haben)
    ROUND(SUM(CASE WHEN debit_credit = 'H' THEN amount ELSE 0 END), 2) as umsatz,
    
    -- Netto (Umsatz - Kosten)
    ROUND(SUM(CASE 
        WHEN debit_credit = 'H' THEN amount 
        WHEN debit_credit = 'S' THEN -amount 
        ELSE 0 
    END), 2) as netto
    
FROM fibu_buchungen
WHERE kategorie_erweitert IS NOT NULL 
  AND kategorie_erweitert != 'bilanz'
GROUP BY wirtschaftsjahr, monat, kategorie_erweitert
ORDER BY wirtschaftsjahr DESC, monat DESC, kategorie_erweitert;

-- ============================================================================
-- 4. VIEW: JAHRES-ÜBERSICHT NACH KATEGORIEN
-- ============================================================================

DROP VIEW IF EXISTS v_cashflow_jahresuebersicht;

CREATE VIEW v_cashflow_jahresuebersicht AS
SELECT 
    wirtschaftsjahr,
    kategorie_erweitert,
    COUNT(*) as anzahl_buchungen,
    ROUND(SUM(CASE WHEN debit_credit = 'S' THEN amount ELSE 0 END), 2) as kosten,
    ROUND(SUM(CASE WHEN debit_credit = 'H' THEN amount ELSE 0 END), 2) as umsatz,
    ROUND(SUM(CASE 
        WHEN debit_credit = 'H' THEN amount 
        WHEN debit_credit = 'S' THEN -amount 
        ELSE 0 
    END), 2) as netto
FROM fibu_buchungen
WHERE kategorie_erweitert IS NOT NULL 
  AND kategorie_erweitert != 'bilanz'
GROUP BY wirtschaftsjahr, kategorie_erweitert
ORDER BY wirtschaftsjahr DESC, kategorie_erweitert;

-- ============================================================================
-- 5. VIEW: AKTUELLE SITUATION (Aktuelles WJ)
-- ============================================================================

DROP VIEW IF EXISTS v_cashflow_aktuell;

CREATE VIEW v_cashflow_aktuell AS
SELECT 
    strftime('%Y-%m', accounting_date) as monat,
    kategorie_erweitert,
    COUNT(*) as buchungen,
    ROUND(SUM(CASE WHEN debit_credit = 'S' THEN amount ELSE 0 END), 2) as kosten,
    ROUND(SUM(CASE WHEN debit_credit = 'H' THEN amount ELSE 0 END), 2) as umsatz,
    ROUND(SUM(CASE 
        WHEN debit_credit = 'H' THEN amount 
        WHEN debit_credit = 'S' THEN -amount 
        ELSE 0 
    END), 2) as netto
FROM fibu_buchungen
WHERE kategorie_erweitert IS NOT NULL 
  AND kategorie_erweitert != 'bilanz'
  -- Aktuelles Wirtschaftsjahr (ab 01.09.2025)
  AND accounting_date >= DATE('2025-09-01')
GROUP BY monat, kategorie_erweitert
ORDER BY monat DESC, kategorie_erweitert;

COMMIT;

-- ============================================================================
-- VALIDIERUNG
-- ============================================================================

-- Prüfen ob Spalten existieren
SELECT 
    'kategorie_erweitert' as spalte,
    COUNT(*) as vorhanden
FROM pragma_table_info('fibu_buchungen')
WHERE name = 'kategorie_erweitert'

UNION ALL

SELECT 
    'wirtschaftsjahr' as spalte,
    COUNT(*) as vorhanden
FROM pragma_table_info('fibu_buchungen')
WHERE name = 'wirtschaftsjahr';

-- Erwartete Ausgabe: 2 Zeilen mit vorhanden = 1

-- ============================================================================
-- ERFOLGSMELDUNG
-- ============================================================================

SELECT '✅ Migration erfolgreich abgeschlossen!' as status;

-- NÄCHSTE SCHRITTE:
-- 1. Script sync_fibu_buchungen.py v2.1 ausführen
-- 2. Alle Buchungen werden kategorisiert
-- 3. Views liefern sofort Ergebnisse
