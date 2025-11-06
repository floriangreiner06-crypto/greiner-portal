#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vacation Views Setup für Greiner Portal
========================================
Erstellt alle wichtigen Views für den Urlaubsplaner
"""

import sqlite3
from datetime import datetime

# View-Definitionen
VIEWS = {
    'v_vacation_balance_2025': """
        CREATE VIEW IF NOT EXISTS v_vacation_balance_2025 AS
        SELECT 
            e.id as employee_id,
            e.first_name || ' ' || e.last_name as name,
            e.email,
            e.department,
            e.location,
            
            -- Urlaubsanspruch
            COALESCE(SUM(ve.days_total), 0) as anspruch,
            
            -- Verbrauchte Tage (approved)
            COALESCE((
                SELECT 
                    SUM(CASE WHEN vb.day_part = 'full' THEN 1.0 ELSE 0.5 END)
                FROM vacation_bookings vb
                WHERE vb.employee_id = e.id
                  AND strftime('%Y', vb.booking_date) = '2025'
                  AND vb.status = 'approved'
            ), 0) as verbraucht,
            
            -- Geplante Tage (pending)
            COALESCE((
                SELECT 
                    SUM(CASE WHEN vb.day_part = 'full' THEN 1.0 ELSE 0.5 END)
                FROM vacation_bookings vb
                WHERE vb.employee_id = e.id
                  AND strftime('%Y', vb.booking_date) = '2025'
                  AND vb.status = 'pending'
            ), 0) as geplant,
            
            -- Resturlaub
            COALESCE(SUM(ve.days_total), 0) - 
            COALESCE((
                SELECT 
                    SUM(CASE WHEN vb.day_part = 'full' THEN 1.0 ELSE 0.5 END)
                FROM vacation_bookings vb
                WHERE vb.employee_id = e.id
                  AND strftime('%Y', vb.booking_date) = '2025'
                  AND vb.status IN ('approved', 'pending')
            ), 0) as resturlaub
            
        FROM employees e
        LEFT JOIN vacation_entitlements ve ON e.id = ve.employee_id AND ve.year = 2025
        WHERE e.aktiv = 1
        GROUP BY e.id
    """,
    
    'v_pending_approvals': """
        CREATE VIEW IF NOT EXISTS v_pending_approvals AS
        SELECT 
            vb.id,
            vb.employee_id,
            e.first_name || ' ' || e.last_name as employee_name,
            e.email,
            e.department,
            vb.booking_date,
            vb.day_part,
            vt.name as vacation_type,
            vb.comment,
            vb.created_at,
            
            -- Anzahl Tage für diesen Antrag
            (SELECT COUNT(*) 
             FROM vacation_bookings vb2 
             WHERE vb2.employee_id = vb.employee_id
               AND vb2.created_at = vb.created_at
               AND vb2.status = 'pending') as total_days_in_request,
            
            -- Start- und Enddatum des Antrags
            (SELECT MIN(booking_date) 
             FROM vacation_bookings vb2 
             WHERE vb2.employee_id = vb.employee_id
               AND vb2.created_at = vb.created_at
               AND vb2.status = 'pending') as request_start_date,
            
            (SELECT MAX(booking_date) 
             FROM vacation_bookings vb2 
             WHERE vb2.employee_id = vb.employee_id
               AND vb2.created_at = vb.created_at
               AND vb2.status = 'pending') as request_end_date
            
        FROM vacation_bookings vb
        JOIN employees e ON vb.employee_id = e.id
        JOIN vacation_types vt ON vb.vacation_type_id = vt.id
        WHERE vb.status = 'pending'
        ORDER BY vb.created_at DESC
    """,
    
    'v_team_calendar': """
        CREATE VIEW IF NOT EXISTS v_team_calendar AS
        SELECT 
            vb.booking_date,
            vb.employee_id,
            e.first_name || ' ' || e.last_name as employee_name,
            e.department,
            e.location,
            vt.name as vacation_type,
            vt.color,
            vb.day_part,
            vb.status,
            vb.comment,
            
            -- Wochentag
            CASE CAST(strftime('%w', vb.booking_date) AS INTEGER)
                WHEN 0 THEN 'Sonntag'
                WHEN 1 THEN 'Montag'
                WHEN 2 THEN 'Dienstag'
                WHEN 3 THEN 'Mittwoch'
                WHEN 4 THEN 'Donnerstag'
                WHEN 5 THEN 'Freitag'
                WHEN 6 THEN 'Samstag'
            END as weekday,
            
            -- KW
            strftime('%W', vb.booking_date) as calendar_week
            
        FROM vacation_bookings vb
        JOIN employees e ON vb.employee_id = e.id
        JOIN vacation_types vt ON vb.vacation_type_id = vt.id
        WHERE vb.status IN ('approved', 'pending')
          AND e.aktiv = 1
        ORDER BY vb.booking_date, e.last_name
    """,
    
    'v_employee_vacation_summary': """
        CREATE VIEW IF NOT EXISTS v_employee_vacation_summary AS
        SELECT 
            e.id as employee_id,
            e.personal_nr,
            e.first_name || ' ' || e.last_name as name,
            e.email,
            e.department,
            e.location,
            e.aktiv,
            
            -- Urlaubstage 2025
            COALESCE((
                SELECT SUM(days_total)
                FROM vacation_entitlements ve
                WHERE ve.employee_id = e.id AND ve.year = 2025
            ), 0) as anspruch_2025,
            
            -- Genommen (approved)
            COALESCE((
                SELECT SUM(CASE WHEN day_part = 'full' THEN 1.0 ELSE 0.5 END)
                FROM vacation_bookings vb
                WHERE vb.employee_id = e.id
                  AND strftime('%Y', booking_date) = '2025'
                  AND status = 'approved'
            ), 0) as genommen_2025,
            
            -- Geplant (pending)
            COALESCE((
                SELECT SUM(CASE WHEN day_part = 'full' THEN 1.0 ELSE 0.5 END)
                FROM vacation_bookings vb
                WHERE vb.employee_id = e.id
                  AND strftime('%Y', booking_date) = '2025'
                  AND status = 'pending'
            ), 0) as geplant_2025,
            
            -- Letzter Urlaub
            (SELECT MAX(booking_date)
             FROM vacation_bookings vb
             WHERE vb.employee_id = e.id
               AND status = 'approved') as letzter_urlaub
            
        FROM employees e
        WHERE e.aktiv = 1
        ORDER BY e.last_name, e.first_name
    """,
    
    'v_department_capacity': """
        CREATE VIEW IF NOT EXISTS v_department_capacity AS
        SELECT 
            e.department,
            vb.booking_date,
            
            -- Gesamt Mitarbeiter
            COUNT(DISTINCT e.id) as total_employees,
            
            -- Abwesend (approved)
            COUNT(DISTINCT CASE 
                WHEN vb.status = 'approved' THEN vb.employee_id 
            END) as absent_count,
            
            -- Geplant abwesend (pending)
            COUNT(DISTINCT CASE 
                WHEN vb.status = 'pending' THEN vb.employee_id 
            END) as planned_absent_count,
            
            -- Anwesenheitsrate
            ROUND(100.0 * (COUNT(DISTINCT e.id) - COUNT(DISTINCT CASE 
                WHEN vb.status = 'approved' THEN vb.employee_id 
            END)) / COUNT(DISTINCT e.id), 1) as attendance_rate,
            
            -- Wochentag
            CASE CAST(strftime('%w', vb.booking_date) AS INTEGER)
                WHEN 0 THEN 'Sonntag'
                WHEN 1 THEN 'Montag'
                WHEN 2 THEN 'Dienstag'
                WHEN 3 THEN 'Mittwoch'
                WHEN 4 THEN 'Donnerstag'
                WHEN 5 THEN 'Freitag'
                WHEN 6 THEN 'Samstag'
            END as weekday
            
        FROM employees e
        LEFT JOIN vacation_bookings vb ON e.id = vb.employee_id
        WHERE e.aktiv = 1
          AND e.department IS NOT NULL
        GROUP BY e.department, vb.booking_date
        HAVING vb.booking_date IS NOT NULL
        ORDER BY vb.booking_date, e.department
    """
}


def main():
    """Hauptfunktion"""
    
    print("\n" + "="*70)
    print("📊 VACATION VIEWS SETUP")
    print("="*70)
    
    db_path = 'data/greiner_controlling.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Alte Views löschen (falls vorhanden)
    print("\n🗑️  Lösche alte Views...")
    for view_name in VIEWS.keys():
        try:
            cursor.execute(f"DROP VIEW IF EXISTS {view_name}")
            print(f"   ✓ {view_name} gelöscht")
        except Exception as e:
            print(f"   ⚠️  {view_name}: {e}")
    
    conn.commit()
    
    # Neue Views erstellen
    print("\n📝 Erstelle Views...")
    created = 0
    errors = 0
    
    for view_name, view_sql in VIEWS.items():
        try:
            cursor.execute(view_sql)
            print(f"   ✓ {view_name}")
            created += 1
        except Exception as e:
            print(f"   ❌ {view_name}: {e}")
            errors += 1
    
    conn.commit()
    
    # Test: Views abfragen
    print("\n🔍 Teste Views...")
    
    test_queries = {
        'v_vacation_balance_2025': "SELECT COUNT(*) as count FROM v_vacation_balance_2025",
        'v_pending_approvals': "SELECT COUNT(*) as count FROM v_pending_approvals",
        'v_team_calendar': "SELECT COUNT(*) as count FROM v_team_calendar",
        'v_employee_vacation_summary': "SELECT COUNT(*) as count FROM v_employee_vacation_summary",
        'v_department_capacity': "SELECT COUNT(DISTINCT department) as depts FROM v_department_capacity",
    }
    
    for view_name, query in test_queries.items():
        try:
            cursor.execute(query)
            result = cursor.fetchone()
            if view_name == 'v_department_capacity':
                print(f"   ✓ {view_name}: {result[0]} Abteilungen")
            else:
                print(f"   ✓ {view_name}: {result[0]} Zeilen")
        except Exception as e:
            print(f"   ❌ {view_name}: {e}")
    
    conn.close()
    
    # Zusammenfassung
    print("\n" + "="*70)
    print(f"✅ SETUP ABGESCHLOSSEN")
    print(f"   Erstellt: {created} Views")
    if errors > 0:
        print(f"   Fehler: {errors}")
    print("="*70)
    
    # Beispiel-Queries
    print("\n💡 Beispiel-Queries:")
    print("   # Urlaubssaldo anzeigen")
    print("   sqlite3 data/greiner_controlling.db 'SELECT * FROM v_vacation_balance_2025 LIMIT 5'")
    print("")
    print("   # Offene Genehmigungen")
    print("   sqlite3 data/greiner_controlling.db 'SELECT * FROM v_pending_approvals'")
    print("")
    print("   # Team-Kalender Dezember")
    print("   sqlite3 data/greiner_controlling.db \"SELECT * FROM v_team_calendar WHERE booking_date LIKE '2025-12-%'\"")
    print("")
    
    return 0 if errors == 0 else 1


if __name__ == '__main__':
    try:
        exit(main())
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
