#!/usr/bin/env python3
"""ANALYSE: Werkstatt-Tabellen in Locosoft"""
import sys, os
sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')
import psycopg2

OUTPUT = '/mnt/greiner-portal-sync/analyse_werkstatt.txt'

def load_env():
    env = {}
    with open('config/.env') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k,v = line.strip().split('=',1)
                env[k] = v
    return env

with open(OUTPUT, 'w') as out:
    def p(msg=""): print(msg); out.write(msg + "\n")
    
    env = load_env()
    pg = psycopg2.connect(host=env['LOCOSOFT_HOST'], port=int(env['LOCOSOFT_PORT']),
        database=env['LOCOSOFT_DATABASE'], user=env['LOCOSOFT_USER'], password=env['LOCOSOFT_PASSWORD'])
    cursor = pg.cursor()
    
    p("=" * 80)
    p("ANALYSE: Werkstatt-Tabellen in Locosoft")
    p("=" * 80)
    
    # 1. Tabellen mit 'werkstatt', 'workshop', 'order', 'auftrag' im Namen
    p("\n1. TABELLEN mit relevanten Namen:")
    p("-" * 60)
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
          AND (table_name LIKE '%werkstatt%' 
               OR table_name LIKE '%workshop%' 
               OR table_name LIKE '%order%'
               OR table_name LIKE '%auftrag%'
               OR table_name LIKE '%job%'
               OR table_name LIKE '%repair%'
               OR table_name LIKE '%service%')
        ORDER BY table_name
    """)
    for row in cursor.fetchall():
        p(f"  {row[0]}")
    
    # 2. Alle Tabellen auflisten (Überblick)
    p("\n2. ALLE TABELLEN (Überblick):")
    p("-" * 60)
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    for t in tables:
        p(f"  {t}")
    
    # 3. orders-Tabelle genauer anschauen (falls vorhanden)
    if 'orders' in tables:
        p("\n3. ORDERS-Tabelle Struktur:")
        p("-" * 60)
        cursor.execute("""
            SELECT column_name, data_type FROM information_schema.columns 
            WHERE table_name = 'orders' ORDER BY ordinal_position
        """)
        for row in cursor.fetchall():
            p(f"  {row[0]:40} {row[1]}")
        
        # Stichprobe
        p("\n4. ORDERS Stichprobe (letzte 10):")
        p("-" * 60)
        cursor.execute("""
            SELECT * FROM orders ORDER BY order_number DESC LIMIT 10
        """)
        cols = [desc[0] for desc in cursor.description]
        p(f"  Spalten: {cols[:10]}...")  # Erste 10 Spalten
        for row in cursor.fetchall():
            p(f"  {row[:5]}...")  # Erste 5 Werte
    
    # 4. Suche nach VIN/Fahrzeug-Referenz in orders
    if 'orders' in tables:
        p("\n5. ORDERS - Fahrzeug-Referenz Felder:")
        p("-" * 60)
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'orders'
              AND (column_name LIKE '%vin%' 
                   OR column_name LIKE '%vehicle%'
                   OR column_name LIKE '%dealer_vehicle%'
                   OR column_name LIKE '%fzg%'
                   OR column_name LIKE '%chassis%')
        """)
        for row in cursor.fetchall():
            p(f"  {row[0]}")
    
    cursor.close()
    pg.close()
    p("\n" + "=" * 80)

print(f"Fertig! Datei: {OUTPUT}")
