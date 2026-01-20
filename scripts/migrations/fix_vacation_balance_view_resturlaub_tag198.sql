-- ============================================================================
-- FIX: v_vacation_balance_2026 - Resturlaub zählt nur URLAUB, nicht alle Typen
-- ============================================================================
-- TAG 198: Bug-Fix - View zählte alle Buchungen (Krankheit, ZA, Schulung)
--          statt nur Urlaub (vacation_type_id = 1)
-- ============================================================================

-- View für 2026 korrigieren
CREATE OR REPLACE VIEW v_vacation_balance_2026 AS
SELECT 
    e.id as employee_id,
    e.first_name || ' ' || e.last_name as name,
    e.email,
    COALESCE(e.department_name, 'Unbekannt') as department,
    e.location,
    
    -- Urlaubsanspruch (total_days + carried_over + added_manually)
    COALESCE(SUM(ve.total_days + COALESCE(ve.carried_over, 0) + COALESCE(ve.added_manually, 0)), 0) as anspruch,
    
    -- Verbrauchte Tage (approved) - NUR URLAUB (type_id = 1)
    COALESCE((
        SELECT 
            SUM(CASE WHEN vb.day_part = 'full' THEN 1.0 ELSE 0.5 END)
        FROM vacation_bookings vb
        WHERE vb.employee_id = e.id
          AND EXTRACT(YEAR FROM vb.booking_date) = 2026
          AND vb.status = 'approved'
          AND vb.vacation_type_id = 1  -- TAG 198: Nur Urlaub zählen!
    ), 0) as verbraucht,
    
    -- Geplante Tage (pending) - NUR URLAUB (type_id = 1)
    COALESCE((
        SELECT 
            SUM(CASE WHEN vb.day_part = 'full' THEN 1.0 ELSE 0.5 END)
        FROM vacation_bookings vb
        WHERE vb.employee_id = e.id
          AND EXTRACT(YEAR FROM vb.booking_date) = 2026
          AND vb.status = 'pending'
          AND vb.vacation_type_id = 1  -- TAG 198: Nur Urlaub zählen!
    ), 0) as geplant,
    
    -- Resturlaub (Anspruch - verbraucht - geplant) - NUR URLAUB (type_id = 1)
    COALESCE(SUM(ve.total_days + COALESCE(ve.carried_over, 0) + COALESCE(ve.added_manually, 0)), 0) - 
    COALESCE((
        SELECT 
            SUM(CASE WHEN vb.day_part = 'full' THEN 1.0 ELSE 0.5 END)
        FROM vacation_bookings vb
        WHERE vb.employee_id = e.id
          AND EXTRACT(YEAR FROM vb.booking_date) = 2026
          AND vb.status IN ('approved', 'pending')
          AND vb.vacation_type_id = 1  -- TAG 198: Nur Urlaub zählen!
    ), 0) as resturlaub
    
FROM employees e
LEFT JOIN vacation_entitlements ve ON e.id = ve.employee_id AND ve.year = 2026
WHERE e.aktiv = true
GROUP BY e.id, e.first_name, e.last_name, e.email, e.department_name, e.location;

-- Kommentar aktualisieren
COMMENT ON VIEW v_vacation_balance_2026 IS 'Urlaubssalden 2026 - PostgreSQL-Version (TAG 167, Fix TAG 198: Nur Urlaub zählen)';

-- Test: Prüfe ob Fix funktioniert
SELECT 
    employee_id, 
    name, 
    anspruch, 
    verbraucht, 
    geplant, 
    resturlaub,
    anspruch - verbraucht - geplant as resturlaub_manuell
FROM v_vacation_balance_2026 
WHERE name ILIKE '%Bianca%' OR name ILIKE '%Herbert%' OR name ILIKE '%Vanessa%'
ORDER BY name;
