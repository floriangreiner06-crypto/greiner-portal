-- ============================================================================
-- VERKAUF API - DEDUPLIZIERUNG FIX
-- ============================================================================
-- Zweck: Verhindere Doppelzählungen wenn Fahrzeuge von N → T/V umgesetzt werden
-- Regel: Wenn T oder V existiert, ignoriere N für dieselbe VIN am gleichen Datum
-- Datum: 11.11.2025
-- ============================================================================

-- BEISPIEL: Das Problem (VORHER)
-- ============================================================================
-- VIN S4176742, Datum 2025-11-06:
--   - ID 4841: Typ 'N' (Neuwagen) 
--   - ID 4858: Typ 'T' (Test/Vorführ)
-- → Wird 2x gezählt in der Zusammenfassung!

-- DIE LÖSUNG: Subquery mit NOT EXISTS
-- ============================================================================
-- Logik:
-- 1. Wähle einen Eintrag aus sales
-- 2. ABER NUR WENN:
--    - Es KEIN anderer Eintrag mit gleicher VIN + gleichem Datum gibt
--    - der Typ T oder V ist
--    - und der aktuelle Eintrag Typ N ist

-- ============================================================================
-- VERWENDUNG IN API-QUERIES
-- ============================================================================

-- Pattern für /api/verkauf/auftragseingang/summary:
-- ============================================================================
SELECT 
    CASE 
        WHEN dealer_vehicle_type = 'N' THEN 'Neuwagen'
        WHEN dealer_vehicle_type IN ('T', 'V') THEN 'Test/Vorführ'
        WHEN dealer_vehicle_type IN ('G', 'D') THEN 'Gebraucht'
    END as kategorie,
    COUNT(*) as anzahl,
    SUM(out_sale_price) as umsatz
FROM sales s
WHERE strftime('%Y', out_sales_contract_date) = '2025'
    AND strftime('%m', out_sales_contract_date) = '11'
    
    -- ⭐ DEDUP-FILTER: Ignoriere N wenn T/V existiert
    AND NOT EXISTS (
        SELECT 1 
        FROM sales s2 
        WHERE s2.vin = s.vin 
            AND s2.out_sales_contract_date = s.out_sales_contract_date
            AND s2.dealer_vehicle_type IN ('T', 'V')
            AND s.dealer_vehicle_type = 'N'
    )
    
GROUP BY kategorie;


-- Pattern für /api/verkauf/auftragseingang/detail:
-- ============================================================================
SELECT 
    s.salesman_number,
    e.first_name || ' ' || e.last_name as verkaufer_name,
    CASE 
        WHEN s.dealer_vehicle_type = 'N' THEN 'Neuwagen'
        WHEN s.dealer_vehicle_type IN ('T', 'V') THEN 'Test/Vorführ'
        WHEN s.dealer_vehicle_type IN ('G', 'D') THEN 'Gebraucht'
    END as kategorie,
    s.model_description,
    COUNT(*) as anzahl,
    SUM(s.out_sale_price) as umsatz
FROM sales s
LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
WHERE strftime('%Y', s.out_sales_contract_date) = '2025'
    AND strftime('%m', s.out_sales_contract_date) = '11'
    
    -- ⭐ DEDUP-FILTER: Ignoriere N wenn T/V existiert
    AND NOT EXISTS (
        SELECT 1 
        FROM sales s2 
        WHERE s2.vin = s.vin 
            AND s2.out_sales_contract_date = s.out_sales_contract_date
            AND s2.dealer_vehicle_type IN ('T', 'V')
            AND s.dealer_vehicle_type = 'N'
    )
    
GROUP BY s.salesman_number, kategorie, s.model_description
ORDER BY s.salesman_number, kategorie;


-- TEST-QUERY: Prüfe Deduplizierung
-- ============================================================================
-- Zeige VOR und NACH der Deduplizierung

-- VORHER (mit Duplikaten):
SELECT 
    'VORHER' as status,
    COUNT(*) as anzahl_eintraege,
    COUNT(DISTINCT vin) as anzahl_fahrzeuge
FROM sales
WHERE salesman_number = 2000
    AND strftime('%Y-%m', out_sales_contract_date) = '2025-11';

-- NACHHER (ohne Duplikate):
SELECT 
    'NACHHER' as status,
    COUNT(*) as anzahl_eintraege,
    COUNT(DISTINCT vin) as anzahl_fahrzeuge
FROM sales s
WHERE salesman_number = 2000
    AND strftime('%Y-%m', out_sales_contract_date) = '2025-11'
    AND NOT EXISTS (
        SELECT 1 
        FROM sales s2 
        WHERE s2.vin = s.vin 
            AND s2.out_sales_contract_date = s.out_sales_contract_date
            AND s2.dealer_vehicle_type IN ('T', 'V')
            AND s.dealer_vehicle_type = 'N'
    );

-- Zeige welche Einträge gefiltert werden:
SELECT 
    s.id,
    s.dealer_vehicle_type,
    SUBSTR(s.vin, -8) as vin,
    s.model_description,
    s.out_sales_contract_date,
    'WIRD IGNORIERT (N -> T/V)' as status
FROM sales s
WHERE EXISTS (
    SELECT 1 
    FROM sales s2 
    WHERE s2.vin = s.vin 
        AND s2.out_sales_contract_date = s.out_sales_contract_date
        AND s2.dealer_vehicle_type IN ('T', 'V')
        AND s.dealer_vehicle_type = 'N'
)
ORDER BY s.out_sales_contract_date, s.vin;


-- ============================================================================
-- WICHTIGE HINWEISE
-- ============================================================================
-- 1. Der Filter muss in ALLEN Verkaufs-API-Endpoints eingebaut werden
-- 2. Gilt für: /auftragseingang/summary, /auftragseingang/detail
-- 3. Gilt für: /auslieferung/summary, /auslieferung/detail  
-- 4. Performance: NOT EXISTS ist effizienter als LEFT JOIN mit NULL-Check
-- 5. VIN + Datum sind die Schlüsselfelder (nicht nur VIN!)
