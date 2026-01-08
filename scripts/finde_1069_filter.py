"""
Finde den Filter, der genau 1069 ergibt
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session

print("=" * 100)
print("SUCHE: Welcher Filter ergibt genau 1069?")
print("=" * 100)

vj_von = "2024-09-01"
vj_bis = "2025-09-01"

with locosoft_session() as conn_loco:
    cursor_loco = conn_loco.cursor()
    
    # Test verschiedene Kombinationen
    tests = [
        ("Alle DISTINCT", "dealer_vehicle_type IN ('D', 'G', 'L', 'N', 'T', 'V')"),
        ("Ohne D", "dealer_vehicle_type IN ('G', 'L', 'N', 'T', 'V')"),
        ("Ohne D+L", "dealer_vehicle_type IN ('G', 'N', 'T', 'V')"),
        ("Nur G+N+T+V mit Preis >= 1000", "dealer_vehicle_type IN ('G', 'N', 'T', 'V') AND out_sale_price >= 1000"),
        ("Nur G+N+T+V mit Preis >= 5000", "dealer_vehicle_type IN ('G', 'N', 'T', 'V') AND out_sale_price >= 5000"),
        ("Alle mit Preis >= 1000", "dealer_vehicle_type IN ('D', 'G', 'L', 'N', 'T', 'V') AND out_sale_price >= 1000"),
        ("Alle mit Preis >= 5000", "dealer_vehicle_type IN ('D', 'G', 'L', 'N', 'T', 'V') AND out_sale_price >= 5000"),
        ("Ohne D, Preis >= 1000", "dealer_vehicle_type IN ('G', 'L', 'N', 'T', 'V') AND out_sale_price >= 1000"),
        ("Ohne D, Preis >= 5000", "dealer_vehicle_type IN ('G', 'L', 'N', 'T', 'V') AND out_sale_price >= 5000"),
    ]
    
    print(f"\n{'Filter':<40} {'Stück':<10} {'Differenz':<15}")
    print("-" * 100)
    
    beste_differenz = float('inf')
    bester_filter = None
    
    for name, filter_condition in tests:
        query = f"""
            SELECT COUNT(DISTINCT vehicle_number) as stueck
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND vehicle_number IS NOT NULL
              AND {filter_condition}
        """
        
        cursor_loco.execute(query, (vj_von, vj_bis))
        row = cursor_loco.fetchone()
        stueck = int(row[0] or 0) if row else 0
        differenz = abs(stueck - 1069)
        
        print(f"{name:<40} {stueck:<10} {differenz:<15}")
        
        if differenz < beste_differenz:
            beste_differenz = differenz
            bester_filter = (name, stueck, differenz)
    
    print("\n" + "=" * 100)
    if bester_filter and bester_filter[2] == 0:
        print(f"✅ GEFUNDEN: {bester_filter[0]} = {bester_filter[1]} Stk. (exakt 1069!)")
    elif bester_filter and bester_filter[2] < 10:
        print(f"⚠️  Am nächsten: {bester_filter[0]} = {bester_filter[1]} Stk. (Differenz: {bester_filter[2]})")
    else:
        print(f"⚠️  Keine exakte Übereinstimmung. Bester Filter: {bester_filter[0]} = {bester_filter[1]} Stk. (Differenz: {bester_filter[2]})")
        print(f"\nMöglicherweise verwendet Global Cube:")
        print(f"  - Andere Zeiträume")
        print(f"  - Andere Verkaufsarten-Filter")
        print(f"  - Andere Datenquelle")
        print(f"  - Kombination mehrerer Filter")

