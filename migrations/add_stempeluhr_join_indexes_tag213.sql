-- Migration: Stempeluhr JOIN-Indizes - TAG 213
-- Datum: 2026-01-27
-- Zweck: Performance-Optimierung für JOINs in get_stempeluhr() Query
-- Datenbank: Locosoft PostgreSQL (10.80.80.8:5432/loco_auswertung_db)
-- 
-- HINWEIS: Diese Indizes können erstellt werden, wenn der User CREATE INDEX Rechte hat.
-- Falls nicht, muss ein DB-Admin diese Indizes erstellen.

-- ============================================================================
-- INDIZES FÜR JOIN-TABELLEN
-- ============================================================================
-- Diese Indizes optimieren die JOINs in get_stempeluhr() Query
-- Erwartete Verbesserung: 30-50% schneller (von 11s auf 5-7s)

-- 1. employees_history (JOIN für Mechaniker-Namen)
CREATE INDEX IF NOT EXISTS idx_employees_history_latest 
    ON employees_history(employee_number, is_latest_record) 
    WHERE is_latest_record = true;

-- 2. labours (LATERAL JOIN für vorgabe_aw)
CREATE INDEX IF NOT EXISTS idx_labours_order_time 
    ON labours(order_number, time_units) 
    WHERE time_units > 0;

-- 3. orders (JOIN für Auftrags-Daten)
CREATE INDEX IF NOT EXISTS idx_orders_number 
    ON orders(number);

-- 4. vehicles (JOIN für Fahrzeug-Daten)
CREATE INDEX IF NOT EXISTS idx_vehicles_internal_number 
    ON vehicles(internal_number);

-- ============================================================================
-- HINWEISE
-- ============================================================================
-- Diese Indizes werden auf der LOCOSOFT-DB erstellt (10.80.80.8:5432)
-- 
-- Ausführung (falls User Rechte hat):
-- PGPASSWORD=loco psql -h 10.80.80.8 -U loco_auswertung_benutzer -d loco_auswertung_db -f migrations/add_stempeluhr_join_indexes_tag213.sql
--
-- Oder manuell auf dem Locosoft-Server als DB-Admin ausführen.
--
-- Erwartete Verbesserung:
-- - Vorher: 11+ Sekunden
-- - Nachher: 5-7 Sekunden (30-50% schneller)
-- ============================================================================
