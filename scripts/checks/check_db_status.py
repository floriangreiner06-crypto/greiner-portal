#!/usr/bin/env python3
"""
============================================================================
PHASE 1 - DB-STATUS PRÜFEN (NEUER SERVER)
============================================================================
Erstellt: 06.11.2025
Server: 10.80.80.20 (srvlinux01)
Pfad: /opt/greiner-portal
Zweck: Aktuellen Zustand der Datenbank analysieren vor Migration
============================================================================
"""

import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = "data/greiner_controlling.db"

def check_database():
    """Prüft den aktuellen Zustand der Datenbank"""
    
    if not Path(DB_PATH).exists():
        print("❌ Fehler: data/greiner_controlling.db nicht gefunden!")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 70)
    print("📊 DATENBANK-STATUS VOR MIGRATION")
    print("=" * 70)
    print()
    
    # 1. EMPLOYEES
    print("👥 EMPLOYEES (Mitarbeiter)")
    print("-" * 70)
    cursor.execute("SELECT COUNT(*) as count FROM employees")
    employee_count = cursor.fetchone()['count']
    print(f"  Gesamt: {employee_count} Mitarbeiter")
    
    # Aktive Mitarbeiter
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM employees 
        WHERE exit_date IS NULL OR exit_date > date('now')
    """)
    active_count = cursor.fetchone()['count']
    print(f"  Aktiv:  {active_count} Mitarbeiter")
    
    # Nach Abteilung
    cursor.execute("""
        SELECT department_name, COUNT(*) as count 
        FROM employees 
        WHERE department_name IS NOT NULL
        GROUP BY department_name 
        ORDER BY count DESC
    """)
    print("\n  Nach Abteilung:")
    for row in cursor.fetchall():
        print(f"    • {row['department_name']}: {row['count']}")
    
    print()
    
    # 2. VACATION_TYPES
    print("📋 VACATION_TYPES (Urlaubsarten)")
    print("-" * 70)
    cursor.execute("SELECT COUNT(*) as count FROM vacation_types")
    types_count = cursor.fetchone()['count']
    print(f"  Gesamt: {types_count} Urlaubsarten")
    
    cursor.execute("""
        SELECT name, color, available_for_user, deduct_from_contingent 
        FROM vacation_types 
        ORDER BY id
    """)
    print("\n  Übersicht:")
    for row in cursor.fetchall():
        user_flag = "👤" if row['available_for_user'] else "  "
        deduct_flag = "📉" if row['deduct_from_contingent'] else "  "
        print(f"    {user_flag} {deduct_flag} {row['name']:20} ({row['color']})")
    
    print()
    
    # 3. VACATION_BOOKINGS
    print("📅 VACATION_BOOKINGS (Buchungen)")
    print("-" * 70)
    cursor.execute("SELECT COUNT(*) as count FROM vacation_bookings")
    bookings_count = cursor.fetchone()['count']
    print(f"  Gesamt: {bookings_count} Buchungen")
    
    # Nach Status
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM vacation_bookings 
        GROUP BY status 
        ORDER BY count DESC
    """)
    print("\n  Nach Status:")
    for row in cursor.fetchall():
        print(f"    • {row['status']:15} {row['count']:5} Buchungen")
    
    # Nach Jahr
    cursor.execute("""
        SELECT strftime('%Y', booking_date) as year, COUNT(*) as count 
        FROM vacation_bookings 
        GROUP BY year 
        ORDER BY year DESC
    """)
    print("\n  Nach Jahr:")
    for row in cursor.fetchall():
        print(f"    • {row['year']}: {row['count']:5} Buchungen")
    
    # Nach Typ
    cursor.execute("""
        SELECT vt.name, COUNT(*) as count 
        FROM vacation_bookings vb
        JOIN vacation_types vt ON vb.vacation_type_id = vt.id
        GROUP BY vt.name 
        ORDER BY count DESC
        LIMIT 5
    """)
    print("\n  Top 5 Urlaubsarten:")
    for row in cursor.fetchall():
        print(f"    • {row['name']:20} {row['count']:5} Buchungen")
    
    print()
    
    # 4. VACATION_ADJUSTMENTS
    print("⚖️  VACATION_ADJUSTMENTS (Anpassungen)")
    print("-" * 70)
    cursor.execute("SELECT COUNT(*) as count FROM vacation_adjustments")
    adjustments_count = cursor.fetchone()['count']
    print(f"  Gesamt: {adjustments_count} Anpassungen")
    
    if adjustments_count > 0:
        cursor.execute("""
            SELECT adjustment_type, COUNT(*) as count 
            FROM vacation_adjustments 
            GROUP BY adjustment_type
        """)
        print("\n  Nach Typ:")
        for row in cursor.fetchall():
            print(f"    • {row['adjustment_type']}: {row['count']}")
    
    print()
    
    # 5. TABELLEN-STRUKTUR PRÜFEN
    print("🔧 SCHEMA-PRÜFUNG")
    print("-" * 70)
    
    # Prüfe welche Spalten in employees existieren
    cursor.execute("PRAGMA table_info(employees)")
    employee_columns = [row['name'] for row in cursor.fetchall()]
    
    # Zu erwartende neue Spalten
    new_columns = ['vorgesetzter_id', 'aktiv', 'personal_nr']
    
    print("  Neue Spalten in 'employees':")
    for col in new_columns:
        if col in employee_columns:
            print(f"    ✅ {col} (bereits vorhanden)")
        else:
            print(f"    ⬜ {col} (wird erstellt)")
    
    # Prüfe ob neue Tabellen existieren
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        AND name IN ('holidays', 'vacation_entitlements', 'vacation_audit_log')
    """)
    existing_tables = [row['name'] for row in cursor.fetchall()]
    
    new_tables = ['holidays', 'vacation_entitlements', 'vacation_audit_log']
    print("\n  Neue Tabellen:")
    for table in new_tables:
        if table in existing_tables:
            print(f"    ✅ {table} (bereits vorhanden)")
        else:
            print(f"    ⬜ {table} (wird erstellt)")
    
    print()
    
    # 6. ZUSAMMENFASSUNG
    print("=" * 70)
    print("✅ ZUSAMMENFASSUNG")
    print("=" * 70)
    print()
    print(f"  Mitarbeiter:  {employee_count:5} ({active_count} aktiv)")
    print(f"  Urlaubsarten: {types_count:5}")
    print(f"  Buchungen:    {bookings_count:5}")
    print(f"  Anpassungen:  {adjustments_count:5}")
    print()
    print("🎯 BEREIT FÜR MIGRATION!")
    print()
    print("⚠️  WICHTIG: Backup erstellen vor Migration!")
    print("   → ./phase1_tag1_setup.sh")
    print()
    
    conn.close()
    return True

if __name__ == '__main__':
    try:
        check_database()
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
