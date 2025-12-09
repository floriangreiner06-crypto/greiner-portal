#!/usr/bin/env python3
"""
============================================================================
ANALYSE: Modellbezeichnung-Felder in Locosoft
============================================================================
Erstellt: TAG83 - 25.11.2025
Problem: Code "2GU93KHOXKB0A0E5P0PR35FX" statt "Movano" angezeigt
============================================================================
"""

import sys
import os
sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')

import psycopg2

def load_env():
    """Liest .env Datei"""
    env = {}
    with open('config/.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env[key.strip()] = value.strip()
    return env

def main():
    print("=" * 80)
    print("ANALYSE: Modellbezeichnung-Felder")
    print("=" * 80)
    
    env = load_env()
    
    pg_creds = {
        'host': env['LOCOSOFT_HOST'],
        'port': int(env['LOCOSOFT_PORT']),
        'database': env['LOCOSOFT_DATABASE'],
        'user': env['LOCOSOFT_USER'],
        'password': env['LOCOSOFT_PASSWORD']
    }
    
    conn = psycopg2.connect(**pg_creds)
    cursor = conn.cursor()
    
    # 1. Schema von dealer_vehicles prüfen - Modell-relevante Felder
    print("\n1. MODELL-FELDER in dealer_vehicles:")
    print("-" * 60)
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'dealer_vehicles'
          AND (column_name LIKE '%model%' 
               OR column_name LIKE '%make%' 
               OR column_name LIKE '%description%'
               OR column_name LIKE '%fab%')
        ORDER BY column_name
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:40} {row[1]}")
    
    # 2. Schema von vehicles prüfen
    print("\n2. MODELL-FELDER in vehicles:")
    print("-" * 60)
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'vehicles'
          AND (column_name LIKE '%model%' 
               OR column_name LIKE '%make%' 
               OR column_name LIKE '%description%'
               OR column_name LIKE '%fab%'
               OR column_name LIKE '%type%')
        ORDER BY column_name
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:40} {row[1]}")
    
    # 3. Schema der models-Tabelle
    print("\n3. ALLE FELDER in models:")
    print("-" * 60)
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'models'
        ORDER BY column_name
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:40} {row[1]}")
    
    # 4. Suche nach Fahrzeug mit dem problematischen Code
    print("\n4. SUCHE Fahrzeug mit '2GU93KHOXKB0A0E5P0PR35FX':")
    print("-" * 60)
    
    # In dealer_vehicles
    cursor.execute("""
        SELECT * FROM dealer_vehicles 
        WHERE out_model_code LIKE '%2GU93%'
           OR dealer_vehicle_number::TEXT LIKE '%115527%'
        LIMIT 5
    """)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    if rows:
        for row in rows:
            print("\n  --- Fahrzeug gefunden ---")
            for col, val in zip(columns, row):
                if val is not None and ('model' in col.lower() or 'make' in col.lower() or 'desc' in col.lower() or 'code' in col.lower()):
                    print(f"  {col:35}: {val}")
    else:
        print("  Nicht gefunden mit Modell-Code, versuche VIN...")
        
        # Suche über VIN
        cursor.execute("""
            SELECT dv.*, v.vin
            FROM dealer_vehicles dv
            LEFT JOIN vehicles v ON dv.dealer_vehicle_number = v.dealer_vehicle_number 
                                  AND dv.dealer_vehicle_type = v.dealer_vehicle_type
            WHERE v.vin LIKE '%VXEYC%'
            LIMIT 5
        """)
        rows = cursor.fetchall()
        if rows:
            columns = [desc[0] for desc in cursor.description]
            for row in rows:
                print("\n  --- Fahrzeug über VIN gefunden ---")
                for col, val in zip(columns, row):
                    if val is not None and ('model' in col.lower() or 'make' in col.lower() or 'desc' in col.lower() or 'code' in col.lower() or col == 'vin'):
                        print(f"  {col:35}: {val}")
    
    # 5. Stichprobe: Welche Werte hat out_model_code typischerweise?
    print("\n5. STICHPROBE out_model_code (verschiedene Werte):")
    print("-" * 60)
    cursor.execute("""
        SELECT DISTINCT out_model_code, out_make_number, COUNT(*) as anzahl
        FROM dealer_vehicles
        WHERE out_model_code IS NOT NULL
          AND out_sales_contract_date >= '2025-01-01'
        GROUP BY out_model_code, out_make_number
        ORDER BY anzahl DESC
        LIMIT 20
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:30} Make:{row[1]}  ({row[2]} Fahrzeuge)")
    
    # 6. Prüfen ob models-Tabelle den Code kennt
    print("\n6. CHECK: Gibt es '2GU93%' in models.model_code?")
    print("-" * 60)
    cursor.execute("""
        SELECT model_code, make_number, description
        FROM models
        WHERE model_code LIKE '%2GU93%'
    """)
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"  {row[0]} | Make: {row[1]} | {row[2]}")
    else:
        print("  NICHT GEFUNDEN! → Das ist das Problem!")
        
    # 7. Movano-Einträge in models
    print("\n7. MOVANO-Einträge in models:")
    print("-" * 60)
    cursor.execute("""
        SELECT model_code, make_number, description
        FROM models
        WHERE LOWER(description) LIKE '%movano%'
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"  Code: {row[0]:20} Make: {row[1]}  → {row[2]}")
    
    # 8. Gibt es alternative Beschreibungs-Felder in dealer_vehicles?
    print("\n8. ALTERNATIVE Felder in dealer_vehicles (Stichprobe):")
    print("-" * 60)
    cursor.execute("""
        SELECT 
            dealer_vehicle_number,
            out_model_code,
            out_make_number,
            calc_model_description,
            model_text_line_1,
            model_text_line_2
        FROM dealer_vehicles
        WHERE out_sales_contract_date >= '2025-11-01'
        LIMIT 10
    """)
    cols = [desc[0] for desc in cursor.description]
    print(f"  {' | '.join(cols)}")
    for row in cursor.fetchall():
        print(f"  {' | '.join(str(v)[:25] if v else 'NULL' for v in row)}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("FERTIG - Bitte Ergebnisse prüfen!")
    print("=" * 80)

if __name__ == '__main__':
    main()
