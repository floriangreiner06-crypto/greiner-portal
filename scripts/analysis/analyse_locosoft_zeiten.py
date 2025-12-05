#!/usr/bin/env python3
"""
Analyse der Locosoft PostgreSQL - Zeiterfassungs-Tabellen finden
"""

import json
import psycopg2

CREDENTIALS_PATH = '/opt/greiner-portal/config/credentials.json'

def get_locosoft_credentials():
    with open(CREDENTIALS_PATH, 'r') as f:
        creds = json.load(f)
    return creds['databases']['locosoft']

def connect_postgres():
    creds = get_locosoft_credentials()
    return psycopg2.connect(
        host=creds['host'],
        port=creds['port'],
        database=creds['database'],
        user=creds['user'],
        password=creds['password']
    )

def main():
    conn = connect_postgres()
    cursor = conn.cursor()
    
    print("=" * 80)
    print("LOCOSOFT POSTGRESQL - ZEITERFASSUNGS-ANALYSE")
    print("=" * 80)
    
    # 1. Alle Tabellen mit "time" im Namen
    print("\n### Tabellen mit 'time' im Namen:")
    cursor.execute("""
        SELECT table_name, 
               (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as cols
        FROM information_schema.tables t
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        AND (table_name ILIKE '%time%' OR table_name ILIKE '%zeit%' OR table_name ILIKE '%stamp%' OR table_name ILIKE '%clock%')
        ORDER BY table_name
    """)
    for row in cursor.fetchall():
        print(f"  - {row[0]} ({row[1]} Spalten)")
    
    # 2. Alle Tabellen mit "mechanic" oder "employee" und Zeiten
    print("\n### Tabellen mit Mitarbeiter-Bezug:")
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        AND (table_name ILIKE '%mechanic%' OR table_name ILIKE '%employ%' OR table_name ILIKE '%worker%')
        ORDER BY table_name
    """)
    for row in cursor.fetchall():
        print(f"  - {row[0]}")
    
    # 3. Struktur der times-Tabelle (falls vorhanden)
    print("\n### Struktur der 'times' Tabelle:")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'times'
        ORDER BY ordinal_position
    """)
    cols = cursor.fetchall()
    if cols:
        for col in cols:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
    else:
        print("  NICHT GEFUNDEN!")
    
    # 4. Anzahl Zeilen in times
    print("\n### Zeilen in 'times' Tabelle:")
    try:
        cursor.execute("SELECT COUNT(*) FROM times")
        count = cursor.fetchone()[0]
        print(f"  Anzahl: {count}")
        
        if count > 0:
            cursor.execute("SELECT MIN(start_time), MAX(start_time) FROM times WHERE start_time IS NOT NULL")
            row = cursor.fetchone()
            print(f"  Zeitraum: {row[0]} bis {row[1]}")
            
            # Beispiel-Daten
            print("\n### Beispiel-Daten aus 'times':")
            cursor.execute("SELECT * FROM times ORDER BY start_time DESC LIMIT 5")
            cols = [desc[0] for desc in cursor.description]
            print(f"  Spalten: {cols}")
            for row in cursor.fetchall():
                print(f"  {row}")
    except Exception as e:
        print(f"  Fehler: {e}")
    
    # 5. Alternative: labours mit Mechaniker-Zeiten
    print("\n### 'labours' Tabelle - Struktur (Auszug):")
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'labours'
        AND column_name IN ('mechanic_no', 'employee_no', 'time_units', 'usage_value', 'net_price_in_order')
        ORDER BY ordinal_position
    """)
    for col in cursor.fetchall():
        print(f"  - {col[0]}: {col[1]}")
    
    # 6. Prüfen ob es eine Stempelzeit-Tabelle gibt
    print("\n### Suche nach Stempelzeit-relevanten Spalten:")
    cursor.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND (column_name ILIKE '%start_time%' 
             OR column_name ILIKE '%end_time%' 
             OR column_name ILIKE '%duration%'
             OR column_name ILIKE '%stamp%'
             OR column_name ILIKE '%clock%')
        ORDER BY table_name, column_name
    """)
    results = cursor.fetchall()
    current_table = None
    for row in results:
        if row[0] != current_table:
            print(f"\n  {row[0]}:")
            current_table = row[0]
        print(f"    - {row[1]}")
    
    # 7. orders Tabelle - Zeiten
    print("\n\n### 'orders' Tabelle - Zeit-Spalten:")
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'orders'
        AND (column_name ILIKE '%time%' OR column_name ILIKE '%date%')
        ORDER BY ordinal_position
    """)
    for col in cursor.fetchall():
        print(f"  - {col[0]}: {col[1]}")
    
    conn.close()
    print("\n" + "=" * 80)
    print("ANALYSE ABGESCHLOSSEN")
    print("=" * 80)

if __name__ == '__main__':
    main()
