-- ============================================================================
-- FIX: v_vacation_balance_* Views - Freie Tage berücksichtigen
-- ============================================================================
-- TAG 209: Freie Tage mit affects_vacation_entitlement = true 
--          sollen vom Urlaubsanspruch abgezogen werden
-- ============================================================================

-- Aktualisiere die Funktion create_vacation_balance_view
CREATE OR REPLACE FUNCTION create_vacation_balance_view(year_val INTEGER)
RETURNS void AS $$
BEGIN
    EXECUTE format('
        CREATE OR REPLACE VIEW v_vacation_balance_%s AS
        SELECT 
            e.id as employee_id,
            e.first_name || '' '' || e.last_name as name,
            e.email,
            COALESCE(e.department_name, ''Unbekannt'') as department,
            e.location,
            
            -- Urlaubsanspruch (total_days + carried_over + added_manually) - freie Tage
            COALESCE(SUM(ve.total_days + COALESCE(ve.carried_over, 0) + COALESCE(ve.added_manually, 0)), 0) - 
            COALESCE((
                SELECT COUNT(*)
                FROM free_days fd
                WHERE EXTRACT(YEAR FROM fd.free_date) = %s
                  AND fd.affects_vacation_entitlement = true
            ), 0) as anspruch,
            
            -- Verbrauchte Tage (approved) - NUR URLAUB (type_id = 1)
            COALESCE((
                SELECT 
                    SUM(CASE WHEN vb.day_part = ''full'' THEN 1.0 ELSE 0.5 END)
                FROM vacation_bookings vb
                WHERE vb.employee_id = e.id
                  AND EXTRACT(YEAR FROM vb.booking_date) = %s
                  AND vb.status = ''approved''
                  AND vb.vacation_type_id = 1  -- TAG 198: Nur Urlaub zählen!
            ), 0) as verbraucht,
            
            -- Geplante Tage (pending) - NUR URLAUB (type_id = 1)
            COALESCE((
                SELECT 
                    SUM(CASE WHEN vb.day_part = ''full'' THEN 1.0 ELSE 0.5 END)
                FROM vacation_bookings vb
                WHERE vb.employee_id = e.id
                  AND EXTRACT(YEAR FROM vb.booking_date) = %s
                  AND vb.status = ''pending''
                  AND vb.vacation_type_id = 1  -- TAG 198: Nur Urlaub zählen!
            ), 0) as geplant,
            
            -- Resturlaub (Anspruch - verbraucht - geplant) - NUR URLAUB (type_id = 1)
            (COALESCE(SUM(ve.total_days + COALESCE(ve.carried_over, 0) + COALESCE(ve.added_manually, 0)), 0) - 
            COALESCE((
                SELECT COUNT(*)
                FROM free_days fd
                WHERE EXTRACT(YEAR FROM fd.free_date) = %s
                  AND fd.affects_vacation_entitlement = true
            ), 0)) - 
            COALESCE((
                SELECT 
                    SUM(CASE WHEN vb.day_part = ''full'' THEN 1.0 ELSE 0.5 END)
                FROM vacation_bookings vb
                WHERE vb.employee_id = e.id
                  AND EXTRACT(YEAR FROM vb.booking_date) = %s
                  AND vb.status IN (''approved'', ''pending'')
                  AND vb.vacation_type_id = 1  -- TAG 198: Nur Urlaub zählen!
            ), 0) as resturlaub
            
        FROM employees e
        LEFT JOIN vacation_entitlements ve ON e.id = ve.employee_id AND ve.year = %s
        WHERE e.aktiv = 1
        GROUP BY e.id, e.first_name, e.last_name, e.email, e.department_name, e.location;
    ', year_val, year_val, year_val, year_val, year_val, year_val, year_val, year_val);
    
    EXECUTE format('
        COMMENT ON VIEW v_vacation_balance_%s IS ''Urlaubssalden %s - PostgreSQL-Version (TAG 198: Nur Urlaub zählen, TAG 209: Freie Tage berücksichtigen)'';
    ', year_val, year_val);
END;
$$ LANGUAGE plpgsql;

-- Fixe alle existierenden Views
SELECT create_vacation_balance_view(2025);
SELECT create_vacation_balance_view(2026);
SELECT create_vacation_balance_view(2027);

-- Test: Prüfe ob Fix funktioniert
SELECT 
    employee_id, 
    name, 
    anspruch, 
    verbraucht, 
    geplant, 
    resturlaub
FROM v_vacation_balance_2026 
WHERE name ILIKE '%Bianca%' OR name ILIKE '%Herbert%' OR name ILIKE '%Vanessa%'
ORDER BY name;
