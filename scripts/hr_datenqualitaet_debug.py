#!/usr/bin/env python3
"""
HR DATENQUALITÄTS-CHECK FÜR LOCOSOFT - DEBUG VERSION
=====================================================
Erstellt: 08.12.2025 (TAG 102)

DEBUG: Prüft zuerst die Rohdaten bevor gefiltert wird!
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import psycopg2
from dotenv import load_dotenv

env_path = PROJECT_ROOT / 'config' / '.env'
load_dotenv(env_path)

LOCOSOFT_CONFIG = {
    'host': os.getenv('LOCOSOFT_HOST', '10.80.80.8'),
    'port': int(os.getenv('LOCOSOFT_PORT', 5432)),
    'database': os.getenv('LOCOSOFT_DATABASE', 'loco_auswertung_db'),
    'user': os.getenv('LOCOSOFT_USER', 'loco_auswertung_benutzer'),
    'password': os.getenv('LOCOSOFT_PASSWORD', 'loco')
}


def get_connection():
    return psycopg2.connect(**LOCOSOFT_CONFIG)


def debug_worktimes(conn):
    """Debug: Was steht wirklich in employees_worktimes?"""
    print("\n" + "="*70)
    print("🔍 DEBUG: employees_worktimes Rohdaten")
    print("="*70)
    
    cursor = conn.cursor()
    
    # Gesamtanzahl
    cursor.execute("SELECT COUNT(*) FROM employees_worktimes")
    total = cursor.fetchone()[0]
    print(f"\nGesamt Einträge: {total}")
    
    # Nach is_latest_record
    cursor.execute("""
        SELECT is_latest_record, COUNT(*) 
        FROM employees_worktimes 
        GROUP BY is_latest_record
    """)
    print(f"\nNach is_latest_record:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} Einträge")
    
    # Wie viele MA haben worktimes?
    cursor.execute("""
        SELECT COUNT(DISTINCT employee_number) 
        FROM employees_worktimes
    """)
    print(f"\nAnzahl MA mit worktimes (alle): {cursor.fetchone()[0]}")
    
    cursor.execute("""
        SELECT COUNT(DISTINCT employee_number) 
        FROM employees_worktimes
        WHERE is_latest_record = true
    """)
    print(f"Anzahl MA mit worktimes (is_latest_record=true): {cursor.fetchone()[0]}")
    
    # Beispiel-Daten für einen MA
    cursor.execute("""
        SELECT employee_number, validity_date, dayofweek, work_duration, 
               worktime_start, worktime_end, is_latest_record
        FROM employees_worktimes
        WHERE employee_number = 5004
        ORDER BY validity_date DESC, dayofweek
        LIMIT 20
    """)
    print(f"\nBeispiel MA 5004 (Dederer, Andreas):")
    print(f"{'MA-Nr':<8} {'Gültig ab':<12} {'Tag':<5} {'Dauer':<8} {'Von':<8} {'Bis':<8} {'Latest'}")
    print("-" * 70)
    for row in cursor.fetchall():
        print(f"{row[0]:<8} {str(row[1]):<12} {row[2]:<5} {str(row[3]):<8} {str(row[4]):<8} {str(row[5]):<8} {row[6]}")


def debug_employees(conn):
    """Debug: employees_history Struktur"""
    print("\n" + "="*70)
    print("🔍 DEBUG: employees_history")
    print("="*70)
    
    cursor = conn.cursor()
    
    # Wie viele aktive?
    cursor.execute("""
        SELECT COUNT(*) 
        FROM employees_history 
        WHERE is_latest_record = true AND leave_date IS NULL
    """)
    print(f"\nAktive MA (is_latest_record=true, leave_date IS NULL): {cursor.fetchone()[0]}")
    
    # Beispiel eines aktiven MA
    cursor.execute("""
        SELECT employee_number, name, is_latest_record, validity_date, 
               leave_date, mechanic_number, productivity_factor
        FROM employees_history
        WHERE employee_number = 5004
        ORDER BY validity_date DESC
        LIMIT 5
    """)
    print(f"\nBeispiel MA 5004:")
    for row in cursor.fetchall():
        print(f"  {row}")


def debug_breaktimes(conn):
    """Debug: employees_breaktimes"""
    print("\n" + "="*70)
    print("🔍 DEBUG: employees_breaktimes")
    print("="*70)
    
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM employees_breaktimes")
    print(f"\nGesamt Einträge: {cursor.fetchone()[0]}")
    
    cursor.execute("""
        SELECT is_latest_record, COUNT(*) 
        FROM employees_breaktimes 
        GROUP BY is_latest_record
    """)
    print(f"\nNach is_latest_record:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} Einträge")
    
    # Beispiel
    cursor.execute("""
        SELECT employee_number, validity_date, dayofweek, break_start, break_end, is_latest_record
        FROM employees_breaktimes
        WHERE employee_number = 5004
        ORDER BY validity_date DESC, dayofweek
        LIMIT 15
    """)
    print(f"\nBeispiel MA 5004:")
    for row in cursor.fetchall():
        print(f"  {row}")


def check_worktimes_without_filter(conn):
    """Check ohne is_latest_record Filter"""
    print("\n" + "="*70)
    print("🔍 ARBEITSZEITEN-CHECK OHNE is_latest_record Filter")
    print("="*70)
    
    query = """
    WITH aktive_ma AS (
        SELECT DISTINCT eh.employee_number, eh.name
        FROM employees_history eh
        WHERE eh.is_latest_record = true
          AND eh.leave_date IS NULL
    ),
    arbeitszeiten AS (
        SELECT DISTINCT
            employee_number,
            dayofweek
        FROM employees_worktimes
        WHERE work_duration > 0
        -- KEIN is_latest_record Filter!
    )
    SELECT 
        am.employee_number,
        am.name,
        COALESCE(string_agg(
            CASE az.dayofweek 
                WHEN 1 THEN 'Mo'
                WHEN 2 THEN 'Di'
                WHEN 3 THEN 'Mi'
                WHEN 4 THEN 'Do'
                WHEN 5 THEN 'Fr'
                WHEN 6 THEN 'Sa'
            END, ', ' ORDER BY az.dayofweek
        ), 'KEINE') as vorhandene_tage,
        COUNT(DISTINCT az.dayofweek) as anzahl_tage
    FROM aktive_ma am
    LEFT JOIN arbeitszeiten az ON am.employee_number = az.employee_number
    GROUP BY am.employee_number, am.name
    ORDER BY COUNT(DISTINCT az.dayofweek) DESC, am.name
    LIMIT 20
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"\nTop 20 MA nach Anzahl Arbeitstage (OHNE is_latest_record):\n")
    print(f"{'MA-Nr':<8} {'Name':<30} {'Vorhandene Tage':<25} {'Anzahl'}")
    print("-" * 75)
    for row in results:
        ma_nr, name, tage, anzahl = row
        name_str = name[:29] if name else '-'
        print(f"{ma_nr:<8} {name_str:<30} {tage:<25} {anzahl}/5")


def check_schedule_index(conn):
    """Prüft ob Schichtpläne verwendet werden (schedule_index)"""
    print("\n" + "="*70)
    print("🔍 SCHICHTPLAN-CHECK (schedule_index in employees_history)")
    print("="*70)
    
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT schedule_index, COUNT(*) 
        FROM employees_history 
        WHERE is_latest_record = true AND leave_date IS NULL
        GROUP BY schedule_index
        ORDER BY schedule_index
    """)
    
    print(f"\nVerteilung schedule_index bei aktiven MA:")
    for row in cursor.fetchall():
        idx, count = row
        print(f"  schedule_index={idx}: {count} MA")
    
    # Was bedeuten die Werte?
    print(f"\n📋 Bedeutung aus Locosoft-Handbuch:")
    print(f"   schedule_index = Planungsindex für WTP-Kapazitätsplanung")
    print(f"   100 = voll verfügbar, 50 = halbtags, 0 = nicht produktiv")


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║     HR DATENQUALITÄTS-CHECK - DEBUG VERSION                          ║
║     Prüft Rohdaten in Locosoft                                       ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        conn = get_connection()
        print("✅ Verbindung zu Locosoft hergestellt\n")
        
        debug_employees(conn)
        debug_worktimes(conn)
        debug_breaktimes(conn)
        check_worktimes_without_filter(conn)
        check_schedule_index(conn)
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
