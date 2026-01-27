-- Migration: Stempeluhr Performance-Indizes - TAG 213
-- Datum: 2026-01-27
-- Zweck: Performance-Optimierung für get_stempeluhr() Query (von 11s auf 3-5s)
-- Datenbank: Locosoft PostgreSQL (10.80.80.8:5432/loco_auswertung_db)

-- WICHTIG: Diese Indizes werden auf der LOCOSOFT-DB erstellt!
-- Ausführen auf: 10.80.80.8:5432/loco_auswertung_db

-- ============================================================================
-- 1. INDEX FÜR AKTUELLE STEMPELUNGEN (end_time IS NULL)
-- ============================================================================
-- Wird verwendet in: get_stempeluhr() - produktiv_query CTE
-- Filter: WHERE end_time IS NULL AND type = 2 AND DATE(start_time) = CURRENT_DATE
CREATE INDEX IF NOT EXISTS idx_times_active 
    ON times(employee_number, order_number, start_time, type) 
    WHERE end_time IS NULL AND type = 2;

-- ============================================================================
-- 2. INDEX FÜR DATUM-FILTER
-- ============================================================================
-- Wird verwendet in: get_stempeluhr() - Filter nach DATE(start_time)
-- Filter: WHERE type = 2 AND DATE(start_time) = CURRENT_DATE
CREATE INDEX IF NOT EXISTS idx_times_date_type 
    ON times(DATE(start_time), type) 
    WHERE type = 2;

-- ============================================================================
-- 3. INDEX FÜR ABGESCHLOSSENE STEMPELUNGEN
-- ============================================================================
-- Wird verwendet in: get_stempeluhr() - Subqueries für heute_abgeschlossen_min und laufzeit_min
-- Filter: WHERE end_time IS NOT NULL AND type = 2 AND DATE(start_time) = CURRENT_DATE
-- DISTINCT ON (employee_number, order_number, start_time, end_time)
CREATE INDEX IF NOT EXISTS idx_times_completed 
    ON times(employee_number, order_number, start_time, end_time, type) 
    WHERE end_time IS NOT NULL AND type = 2;

-- ============================================================================
-- 4. INDEX FÜR employees_history (häufig verwendet in JOINs)
-- ============================================================================
-- Wird verwendet in: get_stempeluhr() - JOIN employees_history ON employee_number AND is_latest_record = true
-- Filter: WHERE is_latest_record = true
CREATE INDEX IF NOT EXISTS idx_employees_history_latest 
    ON employees_history(employee_number, is_latest_record) 
    WHERE is_latest_record = true;

-- ============================================================================
-- 5. INDEX FÜR labours (LATERAL JOIN in get_stempeluhr)
-- ============================================================================
-- Wird verwendet in: get_stempeluhr() - LATERAL JOIN für vorgabe_aw
-- Filter: WHERE order_number = X AND time_units > 0
CREATE INDEX IF NOT EXISTS idx_labours_order_time 
    ON labours(order_number, time_units) 
    WHERE time_units > 0;

-- ============================================================================
-- 6. INDEX FÜR orders (JOIN in get_stempeluhr)
-- ============================================================================
-- Wird verwendet in: get_stempeluhr() - JOIN orders ON number
-- Filter: WHERE number = X
CREATE INDEX IF NOT EXISTS idx_orders_number 
    ON orders(number);

-- ============================================================================
-- 7. INDEX FÜR vehicles (JOIN in get_stempeluhr)
-- ============================================================================
-- Wird verwendet in: get_stempeluhr() - JOIN vehicles ON internal_number
-- Filter: WHERE internal_number = X
CREATE INDEX IF NOT EXISTS idx_vehicles_internal_number 
    ON vehicles(internal_number);

-- ============================================================================
-- HINWEISE
-- ============================================================================
-- Diese Indizes werden auf der LOCOSOFT-DB erstellt (10.80.80.8:5432)
-- 
-- Ausführung:
-- PGPASSWORD=loco psql -h 10.80.80.8 -U loco_auswertung_benutzer -d loco_auswertung_db -f migrations/add_stempeluhr_performance_indexes_tag213.sql
--
-- Oder manuell auf dem Locosoft-Server ausführen.
--
-- Erwartete Verbesserung:
-- - Vorher: 11+ Sekunden
-- - Nachher: 3-5 Sekunden (50-70% schneller)
-- ============================================================================
