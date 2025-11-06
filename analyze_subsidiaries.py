#!/usr/bin/env python3
"""
Prüft subsidiary-Werte und ordnet sie Standorten zu
"""

import sys
import psycopg2
from pathlib import Path

def load_env_file(env_path='config/.env'):
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    return env_vars

def analyze_subsidiaries():
    env = load_env_file('config/.env')
    
    conn = psycopg2.connect(
        host=env['LOCOSOFT_HOST'],
        port=int(env['LOCOSOFT_PORT']),
        database=env['LOCOSOFT_DATABASE'],
        user=env['LOCOSOFT_USER'],
        password=env['LOCOSOFT_PASSWORD']
    )
    
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("SUBSIDIARY-ANALYSE (STANDORTE)")
    print("="*80 + "\n")
    
    # 1. Übersicht aller subsidiary-Werte
    print("1️⃣  SUBSIDIARY-VERTEILUNG:")
    print("-"*80)
    cursor.execute("""
        SELECT 
            subsidiary,
            COUNT(*) as anzahl
        FROM employees_history
        WHERE is_latest_record = true
        AND employee_number >= 1000
        AND (leave_date IS NULL OR leave_date > CURRENT_DATE)
        GROUP BY subsidiary
        ORDER BY subsidiary
    """)
    
    for sub, count in cursor.fetchall():
        sub_name = sub if sub is not None else "NULL"
        print(f"  Subsidiary {sub_name:3}: {count:3} Mitarbeiter")
    
    print("\n" + "="*80)
    print("2️⃣  BEISPIEL-MITARBEITER PRO SUBSIDIARY:")
    print("="*80)
    
    # Für jede subsidiary 3 Beispiel-Mitarbeiter zeigen
    cursor.execute("""
        SELECT DISTINCT subsidiary
        FROM employees_history
        WHERE is_latest_record = true
        AND employee_number >= 1000
        AND (leave_date IS NULL OR leave_date > CURRENT_DATE)
        ORDER BY subsidiary
    """)
    
    subsidiaries = [row[0] for row in cursor.fetchall()]
    
    for sub in subsidiaries:
        sub_display = sub if sub is not None else "NULL"
        print(f"\n📍 SUBSIDIARY {sub_display}:")
        print("-"*80)
        
        cursor.execute("""
            SELECT 
                employee_number,
                name
            FROM employees_history
            WHERE is_latest_record = true
            AND employee_number >= 1000
            AND (leave_date IS NULL OR leave_date > CURRENT_DATE)
            AND (subsidiary = %s OR (subsidiary IS NULL AND %s IS NULL))
            ORDER BY employee_number
            LIMIT 5
        """, (sub, sub))
        
        for emp_num, name in cursor.fetchall():
            # Name splitten
            if ',' in name:
                parts = name.split(',', 1)
                vorname = parts[1].strip() if len(parts) > 1 else ""
                nachname = parts[0].strip()
            else:
                vorname = ""
                nachname = name
            
            print(f"  • #{emp_num}: {vorname} {nachname}")
    
    print("\n" + "="*80)
    print("💡 MAPPING-VORSCHLAG:")
    print("="*80)
    print("\n  Basierend auf den Werten vermutlich:")
    print("  • Subsidiary 0 oder 1 → Deggendorf")
    print("  • Subsidiary 2       → Landau a.d. Isar")
    print("  • Subsidiary 3       → ? (ggf. weitere Betriebsstätte)")
    print("  • Subsidiary 4       → ?")
    print("\n  ⚠️  Bitte überprüfen anhand der bekannten Mitarbeiter!\n")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    try:
        analyze_subsidiaries()
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
