#!/usr/bin/env python3
"""ANALYSE V2: Wo kommt der lange Code her?"""
import sys, os
sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')
import psycopg2, sqlite3

OUTPUT_FILE = '/mnt/greiner-portal-sync/analyse_modell_output.txt'

def load_env():
    env = {}
    with open('config/.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env[key.strip()] = value.strip()
    return env

with open(OUTPUT_FILE, 'w') as out:
    def p(msg=""):
        print(msg)
        out.write(msg + "\n")
    
    env = load_env()
    conn = psycopg2.connect(
        host=env['LOCOSOFT_HOST'], port=int(env['LOCOSOFT_PORT']),
        database=env['LOCOSOFT_DATABASE'], user=env['LOCOSOFT_USER'],
        password=env['LOCOSOFT_PASSWORD']
    )
    cursor = conn.cursor()
    
    p("=" * 80)
    p("ANALYSE V2: Modellbezeichnung - Wo kommt der lange Code her?")
    p("=" * 80)
    
    # 1. Suche spezifisch nach dem Movano aus Screenshot
    p("\n1. FAHRZEUG AUS SCREENSHOT (VIN VXEYCBPFB12W74173):")
    p("-" * 60)
    cursor.execute("""
        SELECT 
            v.vin,
            v.free_form_model_text,
            v.free_form_make_text,
            v.model_code as v_model_code,
            dv.out_model_code as dv_model_code,
            dv.out_make_number,
            m.description as models_description
        FROM vehicles v
        LEFT JOIN dealer_vehicles dv ON v.dealer_vehicle_number = dv.dealer_vehicle_number 
                                    AND v.dealer_vehicle_type = dv.dealer_vehicle_type
        LEFT JOIN models m ON dv.out_model_code = m.model_code AND dv.out_make_number = m.make_number
        WHERE v.vin LIKE '%VXEYC%' OR v.vin LIKE '%74173%'
    """)
    for row in cursor.fetchall():
        p(f"  VIN:                  {row[0]}")
        p(f"  free_form_model_text: {row[1]}")
        p(f"  free_form_make_text:  {row[2]}")
        p(f"  v.model_code:         {row[3]}")
        p(f"  dv.out_model_code:    {row[4]}")
        p(f"  out_make_number:      {row[5]}")
        p(f"  models.description:   {row[6]}")
    
    # 2. Check SQLite
    p("\n2. WAS STEHT IN SQLITE (sales-Tabelle)?")
    p("-" * 60)
    sq = sqlite3.connect('data/greiner_controlling.db')
    sqc = sq.cursor()
    sqc.execute("""
        SELECT vin, model_description, make_number, dealer_vehicle_number
        FROM sales 
        WHERE vin LIKE '%VXEYC%' OR vin LIKE '%74173%'
    """)
    for row in sqc.fetchall():
        p(f"  VIN:               {row[0]}")
        p(f"  model_description: {row[1]}")
        p(f"  make_number:       {row[2]}")
        p(f"  dealer_vehicle_nr: {row[3]}")
    
    # 3. Suche nach Code mit P0PR
    p("\n3. SUCHE CODE MIT 'P0PR' (der lange Code):")
    p("-" * 60)
    sqc.execute("""
        SELECT vin, model_description FROM sales 
        WHERE model_description LIKE '%P0PR%' LIMIT 5
    """)
    for row in sqc.fetchall():
        p(f"  VIN: {row[0]} | model_desc: {row[1]}")
    
    sq.close()
    cursor.close()
    conn.close()
    
    p("\n" + "=" * 80)
    p(f"OUTPUT GESPEICHERT IN: {OUTPUT_FILE}")
    p("=" * 80)

print(f"\nDatei erstellt: {OUTPUT_FILE}")
