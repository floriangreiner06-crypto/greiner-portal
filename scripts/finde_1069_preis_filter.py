"""
Suche nach Preis-Filter, der 1069 ergibt
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session

print("=" * 100)
print("SUCHE: Preis-Filter für 1069")
print("=" * 100)

vj_von = "2024-09-01"
vj_bis = "2025-09-01"

with locosoft_session() as conn_loco:
    cursor_loco = conn_loco.cursor()
    
    # Test verschiedene Preis-Schwellen
    preis_schwellen = [4000, 4500, 5000, 5500, 6000, 7000, 8000, 10000]
    
    print(f"\n{'Preis-Schwelle':<20} {'Stück':<10} {'Differenz':<15}")
    print("-" * 100)
    
    beste_differenz = float('inf')
    bester_preis = None
    
    for schwelle in preis_schwellen:
        query = f"""
            SELECT COUNT(DISTINCT vehicle_number) as stueck
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND vehicle_number IS NOT NULL
              AND out_sale_price >= %s
        """
        
        cursor_loco.execute(query, (vj_von, vj_bis, schwelle))
        row = cursor_loco.fetchone()
        stueck = int(row[0] or 0) if row else 0
        differenz = abs(stueck - 1069)
        
        marker = "✅" if differenz == 0 else "  "
        print(f"{marker} >= {schwelle:>6} €      {stueck:<10} {differenz:<15}")
        
        if differenz < beste_differenz:
            beste_differenz = differenz
            bester_preis = (schwelle, stueck, differenz)
    
    # Test auch mit Typ-Filter
    print(f"\n\nMit Typ-Filter (ohne D):")
    print("-" * 100)
    for schwelle in preis_schwellen:
        query = f"""
            SELECT COUNT(DISTINCT vehicle_number) as stueck
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND vehicle_number IS NOT NULL
              AND dealer_vehicle_type IN ('G', 'N', 'T', 'V')
              AND out_sale_price >= %s
        """
        
        cursor_loco.execute(query, (vj_von, vj_bis, schwelle))
        row = cursor_loco.fetchone()
        stueck = int(row[0] or 0) if row else 0
        differenz = abs(stueck - 1069)
        
        marker = "✅" if differenz == 0 else "  "
        print(f"{marker} >= {schwelle:>6} € (ohne D) {stueck:<10} {differenz:<15}")
        
        if differenz < beste_differenz:
            beste_differenz = differenz
            bester_preis = (schwelle, stueck, differenz, "ohne D")
    
    print("\n" + "=" * 100)
    if bester_preis and bester_preis[2] == 0:
        print(f"✅ GEFUNDEN: Preis >= {bester_preis[0]} € = {bester_preis[1]} Stk. (exakt 1069!)")
    elif bester_preis:
        print(f"⚠️  Am nächsten: Preis >= {bester_preis[0]} € = {bester_preis[1]} Stk. (Differenz: {bester_preis[2]})")
        if len(bester_preis) > 3:
            print(f"   Filter: {bester_preis[3]}")

