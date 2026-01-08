"""
Analyse: Welche Filter verwendet Global Cube?
Vergleich verschiedene Kombinationen mit 1069
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session

print("=" * 100)
print("ANALYSE: Global Cube Filter - Welche Kombination ergibt 1069?")
print("=" * 100)

vj_von = "2024-09-01"
vj_bis = "2025-09-01"

print(f"\nZeitraum: {vj_von} bis {vj_bis}")
print(f"Global Cube (Ziel): 1069 Stk.")
print("\n" + "=" * 100)

with locosoft_session() as conn_loco:
    cursor_loco = conn_loco.cursor()
    
    # 1. Alle Typen
    cursor_loco.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND vehicle_number IS NOT NULL
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    alle = int(row[0] or 0) if row else 0
    print(f"\n1. Alle Typen (DISTINCT): {alle} Stk. (Differenz: {abs(alle - 1069)})")
    
    # 2. Ohne L (Leihfahrzeug)
    cursor_loco.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND vehicle_number IS NOT NULL
          AND dealer_vehicle_type != 'L'
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    ohne_l = int(row[0] or 0) if row else 0
    print(f"2. Ohne L (Leihfahrzeug): {ohne_l} Stk. (Differenz: {abs(ohne_l - 1069)})")
    
    # 3. Nur G+N+T+V (ohne D und L)
    cursor_loco.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND vehicle_number IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'N', 'T', 'V')
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    nur_gntv = int(row[0] or 0) if row else 0
    print(f"3. Nur G+N+T+V (ohne D+L): {nur_gntv} Stk. (Differenz: {abs(nur_gntv - 1069)})")
    
    # 4. Mit out_sale_price > 0
    cursor_loco.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND vehicle_number IS NOT NULL
          AND out_sale_price > 0
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    mit_preis = int(row[0] or 0) if row else 0
    print(f"4. Mit Preis > 0: {mit_preis} Stk. (Differenz: {abs(mit_preis - 1069)})")
    
    # 5. Prüfe: Gibt es L (Leihfahrzeug) überhaupt?
    cursor_loco.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type = 'L'
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    l_stueck = int(row[0] or 0) if row else 0
    print(f"\n5. L (Leihfahrzeug) vorhanden: {l_stueck} Stk.")
    
    # 6. Prüfe: Wie viele D (Demo) gibt es?
    cursor_loco.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND vehicle_number IS NOT NULL
          AND dealer_vehicle_type = 'D'
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    d_distinct = int(row[0] or 0) if row else 0
    print(f"6. D (Demo) DISTINCT: {d_distinct} Stk.")
    
    # 7. Berechne: 1223 - 1069 = 154, was könnte das sein?
    print(f"\n7. Berechnung:")
    print(f"   DISTINCT VINs: {alle} Stk.")
    print(f"   Global Cube: 1069 Stk.")
    print(f"   Differenz: {alle - 1069} Stk.")
    print(f"   Das sind {((alle - 1069) / alle * 100):.1f}% der DISTINCT VINs")
    
    # 8. Prüfe: Gibt es bestimmte Preis-Schwellen?
    cursor_loco.execute("""
        SELECT 
            COUNT(DISTINCT vehicle_number) FILTER (WHERE out_sale_price < 1000) as unter_1000,
            COUNT(DISTINCT vehicle_number) FILTER (WHERE out_sale_price >= 1000 AND out_sale_price < 5000) as zwischen,
            COUNT(DISTINCT vehicle_number) FILTER (WHERE out_sale_price >= 5000) as ueber_5000
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND vehicle_number IS NOT NULL
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    print(f"\n8. Nach Preis-Schwellen (DISTINCT VINs):")
    print(f"   Unter 1.000 €: {row[0] or 0} Stk.")
    print(f"   1.000 - 5.000 €: {row[1] or 0} Stk.")
    print(f"   Über 5.000 €: {row[2] or 0} Stk.")
    
    # 9. Prüfe: Was ist die Differenz? Welche Typen könnten gefiltert werden?
    print(f"\n9. Analyse der Differenz (154 Stk.):")
    print(f"   D (Demo): {d_distinct} Stk.")
    print(f"   Wenn Global Cube D ausschließt: {alle - d_distinct} Stk. (Differenz: {abs((alle - d_distinct) - 1069)})")
    
    # 10. Prüfe: Kombinationen
    cursor_loco.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND vehicle_number IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'N', 'T', 'V')
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    ohne_d = int(row[0] or 0) if row else 0
    print(f"   Ohne D (nur G+N+T+V): {ohne_d} Stk. (Differenz: {abs(ohne_d - 1069)})")

print("\n\n" + "=" * 100)
print("FAZIT:")
print("=" * 100)
if ohne_l == 1069:
    print("✅ Global Cube filtert L (Leihfahrzeug) aus!")
elif nur_gntv == 1069:
    print("✅ Global Cube zählt nur G+N+T+V (ohne D+L)!")
elif abs(ohne_l - 1069) < abs(nur_gntv - 1069):
    print(f"⚠️  Am nächsten: Ohne L = {ohne_l} Stk. (Differenz: {abs(ohne_l - 1069)})")
else:
    print(f"⚠️  Am nächsten: Nur G+N+T+V = {nur_gntv} Stk. (Differenz: {abs(nur_gntv - 1069)})")

