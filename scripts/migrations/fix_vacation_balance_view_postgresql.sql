-- ============================================================================
-- FIX: v_vacation_balance_2025 für PostgreSQL
-- ============================================================================
-- Problem: View verwendet SQLite-Syntax (strftime) statt PostgreSQL (EXTRACT)
-- Datum: 2026-01-05 (TAG 167)
-- ============================================================================

-- Alte View löschen
DROP VIEW IF EXISTS v_vacation_balance_2025;

-- Neue View mit PostgreSQL-Syntax erstellen
CREATE OR REPLACE VIEW v_vacation_balance_2025 AS
SELECT 
    e.id as employee_id,
    e.first_name || ' ' || e.last_name as name,
    e.email,
    COALESCE(e.department_name, 'Unbekannt') as department,
    e.location,
    
    -- Urlaubsanspruch (total_days + carried_over + added_manually)
    COALESCE(SUM(ve.total_days + COALESCE(ve.carried_over, 0) + COALESCE(ve.added_manually, 0)), 0) as anspruch,
    
    -- Verbrauchte Tage (approved)
    COALESCE((
        SELECT 
            SUM(CASE WHEN vb.day_part = 'full' THEN 1.0 ELSE 0.5 END)
        FROM vacation_bookings vb
        WHERE vb.employee_id = e.id
          AND EXTRACT(YEAR FROM vb.booking_date) = 2025
          AND vb.status = 'approved'
    ), 0) as verbraucht,
    
    -- Geplante Tage (pending)
    COALESCE((
        SELECT 
            SUM(CASE WHEN vb.day_part = 'full' THEN 1.0 ELSE 0.5 END)
        FROM vacation_bookings vb
        WHERE vb.employee_id = e.id
          AND EXTRACT(YEAR FROM vb.booking_date) = 2025
          AND vb.status = 'pending'
    ), 0) as geplant,
    
    -- Resturlaub (Anspruch - verbraucht - geplant)
    COALESCE(SUM(ve.total_days + COALESCE(ve.carried_over, 0) + COALESCE(ve.added_manually, 0)), 0) - 
    COALESCE((
        SELECT 
            SUM(CASE WHEN vb.day_part = 'full' THEN 1.0 ELSE 0.5 END)
        FROM vacation_bookings vb
        WHERE vb.employee_id = e.id
          AND EXTRACT(YEAR FROM vb.booking_date) = 2025
          AND vb.status IN ('approved', 'pending')
    ), 0) as resturlaub
    
FROM employees e
LEFT JOIN vacation_entitlements ve ON e.id = ve.employee_id AND ve.year = 2025
WHERE e.aktiv = true
GROUP BY e.id, e.first_name, e.last_name, e.email, e.department_name, e.location;

-- Kommentar hinzufügen
COMMENT ON VIEW v_vacation_balance_2025 IS 'Urlaubssalden 2025 - PostgreSQL-Version (TAG 167)';

-- Test: View abfragen
SELECT COUNT(*) as anzahl_mitarbeiter FROM v_vacation_balance_2025;
SELECT employee_id, name, anspruch, verbraucht, geplant, resturlaub 
FROM v_vacation_balance_2025 
WHERE anspruch = 0 
LIMIT 10;

