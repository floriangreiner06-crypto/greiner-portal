"""
Analyse: Warum 771 statt 625? Was filtert Global Cube anders?
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session

print("=" * 100)
print("ANALYSE: Stückzahl-Differenz 771 vs. 625")
print("=" * 100)

vj_von = "2024-09-01"
vj_bis = "2025-09-01"

print(f"\nZeitraum: {vj_von} bis {vj_bis}")
print("\n" + "=" * 100)

with locosoft_session() as conn_loco:
    cursor_loco = conn_loco.cursor()
    
    # 1. Alle GW-Verkäufe (aktuell)
    cursor_loco.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D', 'L')
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    gesamt = int(row[0] or 0) if row else 0
    print(f"\n1. Aktuell (D+G+L, alle): {gesamt} Stk.")
    
    # 2. Nur G (Gebrauchtwagen) - ohne D und L
    cursor_loco.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type = 'G'
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    nur_g = int(row[0] or 0) if row else 0
    print(f"2. Nur G (ohne D+L): {nur_g} Stk.")
    print(f"   Differenz: {gesamt - nur_g} Stk. (D+L)")
    
    # 3. Mit out_sale_price > 0 (bereits geprüft, aber nochmal)
    cursor_loco.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D', 'L')
          AND out_sale_price > 0
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    mit_preis = int(row[0] or 0) if row else 0
    print(f"3. Mit Preis > 0: {mit_preis} Stk.")
    
    # 4. Prüfe: Gibt es out_sales_contract_date vs. out_invoice_date Unterschied?
    cursor_loco.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_sales_contract_date >= %s AND out_sales_contract_date < %s
          AND out_sales_contract_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D', 'L')
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    mit_vertrag = int(row[0] or 0) if row else 0
    print(f"4. Mit out_sales_contract_date: {mit_vertrag} Stk.")
    
    # 5. Prüfe: Gibt es interne Verkäufe? (Spalte existiert nicht, überspringen)
    ohne_kunde = 0
    print(f"5. Ohne Kunde: (Spalte existiert nicht)")
    
    # 6. Umbuchungen: (Spalte existiert nicht, überspringen)
    umbuchung_nw_gw = 0
    print(f"6. Umbuchung NW→GW: (Spalte existiert nicht)")
    
    # 7. Prüfe: Gibt es doppelte Einträge (gleiche VIN)?
    cursor_loco.execute("""
        SELECT COUNT(DISTINCT vin) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D', 'L')
          AND vin IS NOT NULL
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    distinct_vin = int(row[0] or 0) if row else 0
    print(f"7. DISTINCT VIN: {distinct_vin} Stk.")
    print(f"   Differenz (mögliche Doppelte): {gesamt - distinct_vin} Stk.")

print("\n\n" + "=" * 100)
print("VERGLEICH:")
print(f"  Locosoft (DRIVE): {gesamt} Stk.")
print(f"  Global Cube: 625 Stk.")
print(f"  Differenz: {gesamt - 625} Stk.")
print("\nMögliche Erklärungen:")
print("  1. Global Cube zählt nur G (ohne D+L): {nur_g} Stk. (Differenz: {gesamt - nur_g} Stk.)")
print("  2. Global Cube verwendet DISTINCT VIN: {distinct_vin} Stk. (Differenz: {gesamt - distinct_vin} Stk.)")
print("  3. Global Cube filtert Umbuchungen: {gesamt - umbuchung_nw_gw} Stk. (ohne Umbuchungen)")
print("=" * 100)

