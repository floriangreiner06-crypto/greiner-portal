#!/usr/bin/env python3
"""ANALYSE V2: Werkstattaufträge Details"""
import sys, os
sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')
import psycopg2

OUTPUT = '/mnt/greiner-portal-sync/analyse_werkstatt_v2.txt'

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
    p("ANALYSE V2: Werkstattaufträge (orders)")
    p("=" * 80)
    
    # 1. Stichprobe letzte Aufträge
    p("\n1. LETZTE 10 AUFTRÄGE:")
    p("-" * 60)
    cursor.execute("""
        SELECT number, subsidiary, order_date, dealer_vehicle_number, 
               dealer_vehicle_type, has_open_positions, order_classification_flag,
               order_customer
        FROM orders 
        ORDER BY order_date DESC NULLS LAST
        LIMIT 10
    """)
    p(f"  {'Nr':>8} | {'Sub':>3} | {'Datum':>10} | {'DV-Nr':>8} | {'Typ':>3} | {'Offen':>5} | {'Flag':>4} | {'Kunde':>8}")
    p("  " + "-" * 75)
    for row in cursor.fetchall():
        datum = str(row[2])[:10] if row[2] else 'NULL'
        p(f"  {row[0]:>8} | {row[1]:>3} | {datum:>10} | {row[3] or 'NULL':>8} | {row[4] or '-':>3} | {str(row[5]):>5} | {row[6] or '-':>4} | {row[7] or 'NULL':>8}")
    
    # 2. Was bedeuten die classification_flags?
    p("\n2. ORDER_CLASSIFICATION_FLAG Werte:")
    p("-" * 60)
    cursor.execute("""
        SELECT order_classification_flag, COUNT(*) 
        FROM orders 
        GROUP BY order_classification_flag
        ORDER BY COUNT(*) DESC
    """)
    for row in cursor.fetchall():
        p(f"  '{row[0]}': {row[1]} Aufträge")
    
    # 3. order_classifications_def Tabelle
    p("\n3. ORDER_CLASSIFICATIONS_DEF (Definitionen):")
    p("-" * 60)
    cursor.execute("""
        SELECT * FROM order_classifications_def LIMIT 20
    """)
    cols = [desc[0] for desc in cursor.description]
    p(f"  Spalten: {cols}")
    for row in cursor.fetchall():
        p(f"  {row}")
    
    # 4. Offene Aufträge mit Fahrzeug-Bezug
    p("\n4. OFFENE AUFTRÄGE (has_open_positions=true) mit Fahrzeug:")
    p("-" * 60)
    cursor.execute("""
        SELECT o.number, o.order_date, o.dealer_vehicle_number, o.dealer_vehicle_type,
               o.order_classification_flag, v.vin
        FROM orders o
        LEFT JOIN vehicles v ON o.dealer_vehicle_number = v.dealer_vehicle_number
                            AND o.dealer_vehicle_type = v.dealer_vehicle_type
        WHERE o.has_open_positions = true
          AND o.dealer_vehicle_number IS NOT NULL
        ORDER BY o.order_date DESC
        LIMIT 20
    """)
    p(f"  {'Nr':>8} | {'Datum':>10} | {'DV-Nr':>8} | {'Typ':>3} | {'Flag':>4} | VIN")
    p("  " + "-" * 70)
    for row in cursor.fetchall():
        datum = str(row[1])[:10] if row[1] else 'NULL'
        p(f"  {row[0]:>8} | {datum:>10} | {row[2]:>8} | {row[3] or '-':>3} | {row[4] or '-':>4} | {row[5] or 'NULL'}")
    
    # 5. Test: Aufträge für ein bekanntes Fahrzeug (111186)
    p("\n5. AUFTRÄGE FÜR FAHRZEUG 111186:")
    p("-" * 60)
    cursor.execute("""
        SELECT o.number, o.order_date, o.has_open_positions, o.order_classification_flag
        FROM orders o
        WHERE o.dealer_vehicle_number = 111186
        ORDER BY o.order_date DESC
    """)
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            datum = str(row[1])[:10] if row[1] else 'NULL'
            p(f"  Nr: {row[0]} | Datum: {datum} | Offen: {row[2]} | Flag: {row[3]}")
    else:
        p("  Keine Aufträge gefunden")
    
    cursor.close()
    pg.close()
    p("\n" + "=" * 80)

print(f"Fertig! Datei: {OUTPUT}")
