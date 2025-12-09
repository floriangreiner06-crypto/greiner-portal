#!/usr/bin/env python3
"""ANALYSE V2: Alle calc_* Felder für Fahrzeug 111186"""
import sys, os
sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')
import psycopg2

OUTPUT = '/mnt/greiner-portal-sync/analyse_bruttoertrag_v2.txt'

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
    p("ALLE calc_* WERTE für Fahrzeug 111186")
    p("=" * 80)
    
    cursor.execute("""
        SELECT 
            out_sale_price,
            calc_basic_charge,
            calc_accessory,
            calc_extra_expenses,
            calc_insurance,
            calc_usage_value_encr_internal,
            calc_usage_value_encr_external,
            calc_usage_value_encr_other,
            calc_total_writedown,
            calc_sales_aid,
            calc_sales_aid_finish,
            calc_sales_aid_bonus,
            calc_returns_workshop,
            calc_cost_internal_invoices,
            calc_cost_other,
            calc_commission_for_salesman,
            calc_commission_for_arranging,
            calc_actual_payed_interest,
            calc_interest_percent_stkdays,
            calc_cost_percent_stockingdays
        FROM dealer_vehicles
        WHERE dealer_vehicle_number = 111186
    """)
    row = cursor.fetchone()
    cols = ['out_sale_price', 'calc_basic_charge', 'calc_accessory', 'calc_extra_expenses',
            'calc_insurance', 'calc_usage_value_encr_internal', 'calc_usage_value_encr_external',
            'calc_usage_value_encr_other', 'calc_total_writedown', 'calc_sales_aid',
            'calc_sales_aid_finish', 'calc_sales_aid_bonus', 'calc_returns_workshop',
            'calc_cost_internal_invoices', 'calc_cost_other', 'calc_commission_for_salesman',
            'calc_commission_for_arranging', 'calc_actual_payed_interest',
            'calc_interest_percent_stkdays', 'calc_cost_percent_stockingdays']
    
    for col, val in zip(cols, row):
        p(f"  {col:35}: {val}")
    
    # Berechnung wie Locosoft
    p("\n" + "-" * 60)
    p("BERECHNUNG:")
    p("-" * 60)
    
    vk_brutto = float(row[0] or 0)
    vk_netto = vk_brutto / 1.19
    mwst = vk_brutto - vk_netto
    
    grundpreis = float(row[1] or 0)
    zubehoer = float(row[2] or 0)
    fracht = float(row[3] or 0)
    versicherung = float(row[4] or 0)
    intern_rg = float(row[5] or 0)  # usage_value_encr_internal
    extern_rg = float(row[6] or 0)
    abschreibung = float(row[8] or 0)
    
    einsatzwert = grundpreis + zubehoer + fracht + versicherung + intern_rg + extern_rg - abschreibung
    
    vku = float(row[9] or 0) + float(row[10] or 0) + float(row[11] or 0) + float(row[12] or 0)
    
    kosten_intern = float(row[13] or 0)
    kosten_sonst = float(row[14] or 0)
    provision_vk = float(row[15] or 0)
    provision_vermittl = float(row[16] or 0)
    
    var_kosten = kosten_intern + kosten_sonst + provision_vk + provision_vermittl
    
    db = vk_netto - einsatzwert - var_kosten + vku
    db_proz = (db / vk_netto * 100) if vk_netto > 0 else 0
    
    p(f"  VK brutto:       {vk_brutto:12.2f}")
    p(f"  VK netto:        {vk_netto:12.2f}")
    p(f"  MwSt:            {mwst:12.2f}")
    p(f"  Einsatzwert:     {einsatzwert:12.2f}")
    p(f"  VKU gesamt:      {vku:12.2f}")
    p(f"  Var. Kosten:     {var_kosten:12.2f}")
    p(f"  ---")
    p(f"  DB berechnet:    {db:12.2f}")
    p(f"  DB%:             {db_proz:12.2f}%")
    
    cursor.close()
    pg.close()
    p("\n" + "=" * 80)

print(f"Fertig! Datei: {OUTPUT}")
