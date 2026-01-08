"""
Berechnung: Gesamtstückzahl ALLER Fahrzeuge (NW + GW)
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session

print("=" * 100)
print("BERECHNUNG: Gesamtstückzahl ALLER Fahrzeuge (NW + GW)")
print("=" * 100)

vj_von = "2024-09-01"
vj_bis = "2025-09-01"

print(f"\nZeitraum: {vj_von} bis {vj_bis}")
print("\n" + "=" * 100)

with locosoft_session() as conn_loco:
    cursor_loco = conn_loco.cursor()
    
    # 1. GW (D+G+L)
    cursor_loco.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D', 'L')
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    gw_stueck = int(row[0] or 0) if row else 0
    print(f"\n1. GW (D+G+L): {gw_stueck} Stk.")
    
    # 2. NW (N+T+V)
    cursor_loco.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('N', 'T', 'V')
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    nw_stueck = int(row[0] or 0) if row else 0
    print(f"2. NW (N+T+V): {nw_stueck} Stk.")
    
    # 3. Gesamt (alle Fahrzeugtypen)
    cursor_loco.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    gesamt_stueck = int(row[0] or 0) if row else 0
    print(f"3. Gesamt (alle Typen): {gesamt_stueck} Stk.")
    
    # 4. Summe NW + GW
    summe_nw_gw = nw_stueck + gw_stueck
    print(f"\n4. Summe (NW + GW): {summe_nw_gw} Stk.")
    
    # 5. Nach Typen aufgeschlüsselt
    print(f"\n5. Nach Typen aufgeschlüsselt:")
    print("-" * 100)
    cursor_loco.execute("""
        SELECT 
            dealer_vehicle_type,
            COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
        GROUP BY dealer_vehicle_type
        ORDER BY dealer_vehicle_type
    """, (vj_von, vj_bis))
    
    rows = cursor_loco.fetchall()
    print(f"{'Typ':<10} {'Bedeutung':<20} {'Stück':<10}")
    print("-" * 100)
    typen = {
        'D': 'Demo',
        'G': 'Gebrauchtwagen',
        'L': 'Leihfahrzeug',
        'N': 'Neuwagen',
        'T': 'Tageszulassung',
        'V': 'Vorführwagen'
    }
    for row in rows:
        typ = row[0]
        stueck = row[1]
        bedeutung = typen.get(typ, 'Unbekannt')
        print(f"{typ:<10} {bedeutung:<20} {stueck:<10}")

print("\n\n" + "=" * 100)
print("VERGLEICH:")
print(f"  DRIVE Gesamt (alle Typen): {gesamt_stueck} Stk.")
print(f"  DRIVE Summe (NW + GW): {summe_nw_gw} Stk.")
print(f"  Global Cube (erwartet): 1069 Stk.")
print(f"  Differenz: {abs(gesamt_stueck - 1069)} Stk. ({abs(gesamt_stueck - 1069)/1069*100:.1f}%)")
print("=" * 100)

if gesamt_stueck == 1069:
    print("\n✅ Perfekte Übereinstimmung mit Global Cube!")
elif abs(gesamt_stueck - 1069) < 10:
    print(f"\n✅ Sehr gute Übereinstimmung (Differenz: {abs(gesamt_stueck - 1069)} Stk.)")
else:
    print(f"\n⚠️  Abweichung von Global Cube: {abs(gesamt_stueck - 1069)} Stk.")

