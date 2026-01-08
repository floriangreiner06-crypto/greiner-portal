"""
Finale Entschlüsselung: Global Cube Filter-Logik
=================================================
Testet alle möglichen Filter-Kombinationen inkl. Standort-Filter
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session

print("=" * 100)
print("Finale Entschlüsselung: Global Cube Filter-Logik")
print("Geschäftsjahr 2024/25 (Sep 2024 - Aug 2025)")
print("=" * 100)

# Global Cube Referenzwerte
globalcube_nw = 444.02
globalcube_gw = 625.17
globalcube_gw_kunden = 624.5

print(f"\nGlobal Cube Referenzwerte:")
print(f"  NW: {globalcube_nw:.2f} Stk.")
print(f"  GW Gesamt: {globalcube_gw:.2f} Stk.")
print(f"  GW Kunden: {globalcube_gw_kunden:.2f} Stk.")

gj_von = "2024-09-01"
gj_bis = "2025-09-01"

print(f"\n\n1. NW (N+T+V) - STANDORT-FILTER:")
print("-" * 100)

with locosoft_session() as conn:
    cursor = conn.cursor()
    
    nw_tests = []
    
    # Alle Standorte
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('N', 'T', 'V')
    """, (gj_von, gj_bis))
    nw_tests.append(('Alle Standorte', int(cursor.fetchone()[0] or 0)))
    
    # Nur Deggendorf (Stellantis + Hyundai)
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('N', 'T', 'V')
          AND (out_subsidiary = 1 OR out_subsidiary = 2)
    """, (gj_von, gj_bis))
    nw_tests.append(('Nur Deggendorf (1+2)', int(cursor.fetchone()[0] or 0)))
    
    # Nur Landau (out_subsidiary = 1, aber wir können nicht zwischen Deggendorf und Landau unterscheiden)
    # Daher: Landau = out_subsidiary = 1, aber wir müssen das anders identifizieren
    # Für jetzt: Landau ist auch out_subsidiary = 1, daher können wir es nicht separat filtern
    # Stattdessen: Alle außer Deggendorf (1+2) = Rest
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('N', 'T', 'V')
          AND out_subsidiary = 1
          AND NOT (out_subsidiary = 1 OR out_subsidiary = 2)
    """, (gj_von, gj_bis))
    # Das wird 0 ergeben, da out_subsidiary = 1 immer true ist wenn out_subsidiary = 1
    # Stattdessen: Berechne Landau als Differenz
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('N', 'T', 'V')
    """, (gj_von, gj_bis))
    total_nw = int(cursor.fetchone()[0] or 0)
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('N', 'T', 'V')
          AND (out_subsidiary = 1 OR out_subsidiary = 2)
    """, (gj_von, gj_bis))
    degg_nw = int(cursor.fetchone()[0] or 0)
    landau_nw = total_nw - degg_nw
    nw_tests.append(('Nur Landau (berechnet)', landau_nw))
    
    # DISTINCT + Deggendorf
    cursor.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('N', 'T', 'V')
          AND vehicle_number IS NOT NULL
          AND (out_subsidiary = 1 OR out_subsidiary = 2)
    """, (gj_von, gj_bis))
    nw_tests.append(('DISTINCT + Deggendorf', int(cursor.fetchone()[0] or 0)))
    
    print(f"{'Filter':<30} {'Stück':<10} {'Diff zu GC':<15} {'Diff %':<10}")
    print("-" * 100)
    
    for name, stueck in nw_tests:
        diff = stueck - globalcube_nw
        diff_pct = (diff / globalcube_nw * 100) if globalcube_nw > 0 else 0
        marker = "✅" if abs(diff) < 5 else "  "
        print(f"{marker} {name:<28} {stueck:<10} {diff:+.2f} Stk.      {diff_pct:+.2f}%")
    
    print(f"\n\n2. GW (D+G+L) - STANDORT-FILTER + DISTINCT:")
    print("-" * 100)
    
    gw_tests = []
    
    # Alle Standorte - verschiedene Kombinationen
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
    """, (gj_von, gj_bis))
    gw_tests.append(('Alle Standorte (D+G+L)', int(cursor.fetchone()[0] or 0)))
    
    cursor.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
          AND vehicle_number IS NOT NULL
    """, (gj_von, gj_bis))
    gw_tests.append(('Alle Standorte DISTINCT', int(cursor.fetchone()[0] or 0)))
    
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type = 'G'
    """, (gj_von, gj_bis))
    gw_tests.append(('Alle Standorte (nur G)', int(cursor.fetchone()[0] or 0)))
    
    # Deggendorf (1+2)
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
          AND (out_subsidiary = 1 OR out_subsidiary = 2)
    """, (gj_von, gj_bis))
    gw_tests.append(('Deggendorf (1+2) D+G+L', int(cursor.fetchone()[0] or 0)))
    
    cursor.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
          AND vehicle_number IS NOT NULL
          AND (out_subsidiary = 1 OR out_subsidiary = 2)
    """, (gj_von, gj_bis))
    gw_tests.append(('Deggendorf (1+2) DISTINCT', int(cursor.fetchone()[0] or 0)))
    
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type = 'G'
          AND (out_subsidiary = 1 OR out_subsidiary = 2)
    """, (gj_von, gj_bis))
    gw_tests.append(('Deggendorf (1+2) nur G', int(cursor.fetchone()[0] or 0)))
    
    # Landau (berechnet als Differenz: Alle - Deggendorf)
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
    """, (gj_von, gj_bis))
    total_gw = int(cursor.fetchone()[0] or 0)
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
          AND (out_subsidiary = 1 OR out_subsidiary = 2)
    """, (gj_von, gj_bis))
    degg_gw = int(cursor.fetchone()[0] or 0)
    landau_gw = total_gw - degg_gw
    gw_tests.append(('Landau D+G+L (berechnet)', landau_gw))
    
    cursor.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
          AND vehicle_number IS NOT NULL
    """, (gj_von, gj_bis))
    total_gw_distinct = int(cursor.fetchone()[0] or 0)
    cursor.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
          AND vehicle_number IS NOT NULL
          AND (out_subsidiary = 1 OR out_subsidiary = 2)
    """, (gj_von, gj_bis))
    degg_gw_distinct = int(cursor.fetchone()[0] or 0)
    landau_gw_distinct = total_gw_distinct - degg_gw_distinct
    gw_tests.append(('Landau DISTINCT (berechnet)', landau_gw_distinct))
    
    # Kombinationen: DISTINCT + Preis > 0
    cursor.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
          AND vehicle_number IS NOT NULL
          AND out_sale_price > 0
    """, (gj_von, gj_bis))
    gw_tests.append(('DISTINCT + Preis > 0', int(cursor.fetchone()[0] or 0)))
    
    # Kombinationen: Deggendorf + DISTINCT + Preis > 0
    cursor.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
          AND vehicle_number IS NOT NULL
          AND out_sale_price > 0
          AND (out_subsidiary = 1 OR out_subsidiary = 2)
    """, (gj_von, gj_bis))
    gw_tests.append(('Deggendorf DISTINCT + Preis', int(cursor.fetchone()[0] or 0)))
    
    print(f"{'Filter':<30} {'Stück':<10} {'Diff GW Gesamt':<18} {'Diff GW Kunden':<18}")
    print("-" * 100)
    
    beste_gw_gesamt = None
    beste_diff_gesamt = float('inf')
    beste_gw_kunden = None
    beste_diff_kunden = float('inf')
    
    for name, stueck in gw_tests:
        diff_gesamt = stueck - globalcube_gw
        diff_kunden = stueck - globalcube_gw_kunden
        marker1 = "✅" if abs(diff_gesamt) < 20 else "  "
        marker2 = "✅" if abs(diff_kunden) < 20 else "  "
        print(f"{marker1}{marker2} {name:<26} {stueck:<10} {diff_gesamt:+.2f} Stk.        {diff_kunden:+.2f} Stk.")
        
        if abs(diff_gesamt) < beste_diff_gesamt:
            beste_diff_gesamt = abs(diff_gesamt)
            beste_gw_gesamt = (name, stueck, diff_gesamt)
        
        if abs(diff_kunden) < beste_diff_kunden:
            beste_diff_kunden = abs(diff_kunden)
            beste_gw_kunden = (name, stueck, diff_kunden)
    
    print(f"\n  ✅ Beste Übereinstimmung für 'GW Gesamt' ({globalcube_gw:.2f}):")
    if beste_gw_gesamt:
        print(f"     {beste_gw_gesamt[0]} = {beste_gw_gesamt[1]} Stk. (Diff: {beste_gw_gesamt[2]:+.2f})")
    
    print(f"\n  ✅ Beste Übereinstimmung für 'GW Kunden' ({globalcube_gw_kunden:.2f}):")
    if beste_gw_kunden:
        print(f"     {beste_gw_kunden[0]} = {beste_gw_kunden[1]} Stk. (Diff: {beste_gw_kunden[2]:+.2f})")
    
    # Zusätzliche Analyse: Vielleicht verwendet Global Cube eine Kombination?
    print(f"\n\n3. KOMBINATIONS-TEST:")
    print("-" * 100)
    print("Teste ob Global Cube eine Kombination aus mehreren Standorten verwendet...")
    
    # Deggendorf + Landau = Alle (da beide out_subsidiary = 1 oder 2 haben)
    cursor.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
          AND vehicle_number IS NOT NULL
    """, (gj_von, gj_bis))
    degg_landau_distinct = int(cursor.fetchone()[0] or 0)
    
    print(f"  Deggendorf + Landau DISTINCT: {degg_landau_distinct} Stk.")
    print(f"    Diff zu GW Gesamt: {degg_landau_distinct - globalcube_gw:+.2f} Stk.")
    print(f"    Diff zu GW Kunden: {degg_landau_distinct - globalcube_gw_kunden:+.2f} Stk.")

