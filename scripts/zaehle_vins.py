"""
Zähle VINs: DISTINCT VINs vs. alle Einträge
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session

print("=" * 100)
print("ANALYSE: VINs zählen - DISTINCT vs. alle Einträge")
print("=" * 100)

vj_von = "2024-09-01"
vj_bis = "2025-09-01"

print(f"\nZeitraum: {vj_von} bis {vj_bis}")
print("\n" + "=" * 100)

with locosoft_session() as conn_loco:
    cursor_loco = conn_loco.cursor()
    
    # 1. Alle Einträge (aktuell)
    cursor_loco.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    alle_eintraege = int(row[0] or 0) if row else 0
    print(f"\n1. Alle Einträge (COUNT(*)): {alle_eintraege} Stk.")
    
    # 2. DISTINCT VINs
    cursor_loco.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND vehicle_number IS NOT NULL
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    distinct_vin = int(row[0] or 0) if row else 0
    print(f"2. DISTINCT vehicle_number: {distinct_vin} Stk.")
    
    # 3. Einträge ohne vehicle_number
    cursor_loco.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND vehicle_number IS NULL
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    ohne_vin = int(row[0] or 0) if row else 0
    print(f"3. Einträge ohne vehicle_number: {ohne_vin} Stk.")
    
    # 4. Doppelzählungen (VINs die mehrfach vorkommen)
    cursor_loco.execute("""
        SELECT 
            vehicle_number,
            COUNT(*) as anzahl
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND vehicle_number IS NOT NULL
        GROUP BY vehicle_number
        HAVING COUNT(*) > 1
        ORDER BY anzahl DESC
        LIMIT 10
    """, (vj_von, vj_bis))
    
    rows = cursor_loco.fetchall()
    doppelzaehlungen = sum(row[1] - 1 for row in rows)  # -1 weil eine ist "normal"
    
    # Gesamt-Doppelzählungen
    cursor_loco.execute("""
        SELECT SUM(cnt - 1) as doppel
        FROM (
            SELECT vehicle_number, COUNT(*) as cnt
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND vehicle_number IS NOT NULL
            GROUP BY vehicle_number
            HAVING COUNT(*) > 1
        ) as dup
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    gesamt_doppel = int(row[0] or 0) if row else 0
    
    print(f"\n4. Doppelzählungen (VINs die mehrfach vorkommen):")
    print(f"   Anzahl VINs mit >1 Eintrag: {len(rows)}")
    print(f"   Gesamt-Doppelzählungen: {gesamt_doppel} Stk.")
    
    if len(rows) > 0:
        print(f"\n   Top 10 Doppelzählungen:")
        print(f"   {'VIN':<20} {'Anzahl':<10}")
        print("   " + "-" * 30)
        for row in rows[:10]:
            print(f"   {row[0]:<20} {row[1]:<10}")
    
    # 5. Nach Typen: DISTINCT vs. alle
    print(f"\n5. Nach Typen: DISTINCT vs. alle Einträge")
    print("-" * 100)
    print(f"{'Typ':<10} {'Alle':<15} {'DISTINCT VIN':<20} {'Differenz':<15}")
    print("-" * 100)
    
    typen = ['D', 'G', 'L', 'N', 'T', 'V']
    for typ in typen:
        # Alle
        cursor_loco.execute("""
            SELECT COUNT(*) as stueck
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type = %s
        """, (vj_von, vj_bis, typ))
        row = cursor_loco.fetchone()
        alle_typ = int(row[0] or 0) if row else 0
        
        # DISTINCT
        cursor_loco.execute("""
            SELECT COUNT(DISTINCT vehicle_number) as stueck
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type = %s
              AND vehicle_number IS NOT NULL
        """, (vj_von, vj_bis, typ))
        row = cursor_loco.fetchone()
        distinct_typ = int(row[0] or 0) if row else 0
        
        diff = alle_typ - distinct_typ
        print(f"{typ:<10} {alle_typ:<15} {distinct_typ:<20} {diff:<15}")

print("\n\n" + "=" * 100)
print("VERGLEICH:")
print(f"  Alle Einträge: {alle_eintraege} Stk.")
print(f"  DISTINCT VINs: {distinct_vin} Stk.")
print(f"  Doppelzählungen: {gesamt_doppel} Stk.")
print(f"  Ohne VIN: {ohne_vin} Stk.")
print(f"\n  Global Cube (erwartet): 1069 Stk.")
print(f"  DISTINCT VINs: {distinct_vin} Stk.")
print(f"  Differenz: {abs(distinct_vin - 1069)} Stk.")
print("=" * 100)

if distinct_vin == 1069:
    print("\n✅ DISTINCT VINs = Global Cube (1069) - Das ist der Filter!")
elif abs(distinct_vin - 1069) < 10:
    print(f"\n✅ DISTINCT VINs sehr nah an Global Cube (Differenz: {abs(distinct_vin - 1069)} Stk.)")
else:
    print(f"\n⚠️  DISTINCT VINs ({distinct_vin}) ≠ Global Cube (1069)")

