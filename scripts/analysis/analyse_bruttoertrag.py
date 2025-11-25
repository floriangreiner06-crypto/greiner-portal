#!/usr/bin/env python3
"""ANALYSE: Bruttoertrag-Felder"""
import sys, os
sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')
import psycopg2, sqlite3

OUTPUT = '/mnt/greiner-portal-sync/analyse_bruttoertrag.txt'

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
    p("ANALYSE: Bruttoertrag/Deckungsbeitrag Felder")
    p("=" * 80)
    
    # 1. Alle calc_* Felder in dealer_vehicles
    p("\n1. ALLE calc_* FELDER in dealer_vehicles:")
    p("-" * 60)
    cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'dealer_vehicles' AND column_name LIKE 'calc%'
        ORDER BY column_name
    """)
    for row in cursor.fetchall():
        p(f"  {row[0]}")
    
    # 2. Fahrzeug aus Screenshot (Kom.Nr. 111186)
    p("\n2. FAHRZEUG Kom.Nr. 111186 - Locosoft Werte:")
    p("-" * 60)
    cursor.execute("""
        SELECT 
            dv.dealer_vehicle_number,
            dv.out_invoice_date,
            dv.out_sale_price,
            dv.calc_basic_charge,
            dv.calc_accessory,
            dv.calc_extra_expenses,
            dv.calc_cost_internal_invoices,
            v.vin
        FROM dealer_vehicles dv
        LEFT JOIN vehicles v ON dv.dealer_vehicle_number = v.dealer_vehicle_number 
                            AND dv.dealer_vehicle_type = v.dealer_vehicle_type
        WHERE dv.dealer_vehicle_number = 111186
    """)
    row = cursor.fetchone()
    if row:
        p(f"  dealer_vehicle_number:       {row[0]}")
        p(f"  VIN:                         {row[7]}")
        p(f"  out_invoice_date:            {row[1]}")
        p(f"  out_sale_price:              {row[2]}")
        p(f"  calc_basic_charge:           {row[3]}")
        p(f"  calc_accessory:              {row[4]}")
        p(f"  calc_extra_expenses:         {row[5]}")
        p(f"  calc_cost_internal_invoices: {row[6]}")
    
    # 3. Vergleich SQLite
    p("\n3. VERGLEICH SQLite (Kom.Nr. 111186):")
    p("-" * 60)
    sq = sqlite3.connect('data/greiner_controlling.db')
    sqc = sq.cursor()
    sqc.execute("""
        SELECT deckungsbeitrag, db_prozent, out_sale_price,
               fahrzeuggrundpreis, zubehoer, kosten_intern_rg, verkaufsunterstuetzung
        FROM sales WHERE dealer_vehicle_number = 111186
    """)
    row = sqc.fetchone()
    if row:
        p(f"  deckungsbeitrag:        {row[0]}")
        p(f"  db_prozent:             {row[1]}")
        p(f"  out_sale_price:         {row[2]}")
        p(f"  fahrzeuggrundpreis:     {row[3]}")
        p(f"  zubehoer:               {row[4]}")
        p(f"  kosten_intern_rg:       {row[5]}")
        p(f"  verkaufsunterstuetzung: {row[6]}")
    sq.close()
    
    cursor.close()
    pg.close()
    p("\n" + "=" * 80)

print(f"Fertig! Datei: {OUTPUT}")
