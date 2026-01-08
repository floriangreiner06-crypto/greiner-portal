"""
Entschlüsselung: Global Cube Filter-Logik
==========================================
Testet alle möglichen Filter-Kombinationen um Global Cube zu matchen
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')
import csv
import codecs

from api.db_utils import locosoft_session

# Geschäftsjahr 2024/25: Sep 2024 - Aug 2025
gj_von = "2024-09-01"
gj_bis = "2025-09-01"

print("=" * 100)
print("Entschlüsselung: Global Cube Filter-Logik")
print(f"Geschäftsjahr 2024/25 (Sep 2024 - Aug 2025)")
print("=" * 100)

# Global Cube Werte aus CSV
globalcube_nw = 444.02
globalcube_gw = 625.17

print(f"\nGlobal Cube Referenzwerte:")
print(f"  NW: {globalcube_nw:.2f} Stk.")
print(f"  GW: {globalcube_gw:.2f} Stk.")

# Teste verschiedene Filter-Kombinationen
print(f"\n\n1. NW (N+T+V) - VERSCHIEDENE FILTER:")
print("-" * 100)

with locosoft_session() as conn:
    cursor = conn.cursor()
    
    nw_tests = []
    
    # Test 1: Standard (N+T+V)
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('N', 'T', 'V')
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    nw_tests.append(('Standard (N+T+V)', int(row[0] or 0)))
    
    # Test 2: DISTINCT vehicle_number
    cursor.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('N', 'T', 'V')
          AND vehicle_number IS NOT NULL
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    nw_tests.append(('DISTINCT vehicle_number', int(row[0] or 0)))
    
    # Test 3: Mit out_sale_price > 0
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('N', 'T', 'V')
          AND out_sale_price > 0
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    nw_tests.append(('Mit Preis > 0', int(row[0] or 0)))
    
    # Test 4: DISTINCT + Preis > 0
    cursor.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('N', 'T', 'V')
          AND vehicle_number IS NOT NULL
          AND out_sale_price > 0
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    nw_tests.append(('DISTINCT + Preis > 0', int(row[0] or 0)))
    
    # Test 5: Nur bestimmte Standorte?
    # Test 5a: Nur Deggendorf (Stellantis + Hyundai)
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('N', 'T', 'V')
          AND (out_subsidiary = 1 OR out_subsidiary = 2)
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    nw_tests.append(('Nur Deggendorf (1+2)', int(row[0] or 0)))
    
    # Test 5b: Nur Landau
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('N', 'T', 'V')
          AND out_subsidiary = 3
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    nw_tests.append(('Nur Landau (3)', int(row[0] or 0)))
    
    # Ausgabe NW-Tests
    print(f"{'Filter':<30} {'Stück':<10} {'Diff zu GC':<15} {'Diff %':<10}")
    print("-" * 100)
    
    beste_nw = None
    beste_diff_nw = float('inf')
    
    for name, stueck in nw_tests:
        diff = stueck - globalcube_nw
        diff_pct = (diff / globalcube_nw * 100) if globalcube_nw > 0 else 0
        marker = "✅" if abs(diff) < 5 else "  "
        print(f"{marker} {name:<28} {stueck:<10} {diff:+.2f} Stk.      {diff_pct:+.2f}%")
        
        if abs(diff) < beste_diff_nw:
            beste_diff_nw = abs(diff)
            beste_nw = (name, stueck, diff)
    
    if beste_nw:
        print(f"\n  ✅ Beste NW-Übereinstimmung: {beste_nw[0]} = {beste_nw[1]} Stk. (Diff: {beste_nw[2]:+.2f})")
    
    # 2. GW (D+G+L) - VERSCHIEDENE FILTER
    print(f"\n\n2. GW (D+G+L) - VERSCHIEDENE FILTER:")
    print("-" * 100)
    
    gw_tests = []
    
    # Test 1: Standard (D+G+L)
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    gw_tests.append(('Standard (D+G+L)', int(row[0] or 0)))
    
    # Test 2: DISTINCT vehicle_number
    cursor.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
          AND vehicle_number IS NOT NULL
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    gw_tests.append(('DISTINCT vehicle_number', int(row[0] or 0)))
    
    # Test 3: Mit out_sale_price > 0
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
          AND out_sale_price > 0
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    gw_tests.append(('Mit Preis > 0', int(row[0] or 0)))
    
    # Test 4: DISTINCT + Preis > 0
    cursor.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
          AND vehicle_number IS NOT NULL
          AND out_sale_price > 0
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    gw_tests.append(('DISTINCT + Preis > 0', int(row[0] or 0)))
    
    # Test 5: Nur G (ohne D+L)
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type = 'G'
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    gw_tests.append(('Nur G (ohne D+L)', int(row[0] or 0)))
    
    # Test 6: G + D (ohne L)
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D')
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    gw_tests.append(('G + D (ohne L)', int(row[0] or 0)))
    
    # Test 7: DISTINCT (G+D)
    cursor.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D')
          AND vehicle_number IS NOT NULL
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    gw_tests.append(('DISTINCT (G+D)', int(row[0] or 0)))
    
    # Test 8: Nur bestimmte Standorte?
    # Test 8a: Nur Deggendorf (Stellantis + Hyundai)
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
          AND (out_subsidiary = 1 OR out_subsidiary = 2)
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    gw_tests.append(('Nur Deggendorf (1+2)', int(row[0] or 0)))
    
    # Test 8b: Nur Landau
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
          AND out_subsidiary = 3
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    gw_tests.append(('Nur Landau (3)', int(row[0] or 0)))
    
    # Test 9: DISTINCT + Deggendorf
    cursor.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
          AND vehicle_number IS NOT NULL
          AND (out_subsidiary = 1 OR out_subsidiary = 2)
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    gw_tests.append(('DISTINCT + Deggendorf', int(row[0] or 0)))
    
    # Test 10: G + D + DISTINCT + Deggendorf
    cursor.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D')
          AND vehicle_number IS NOT NULL
          AND (out_subsidiary = 1 OR out_subsidiary = 2)
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    gw_tests.append(('DISTINCT (G+D) + Deggendorf', int(row[0] or 0)))
    
    # Test 11: Prüfe ob accounting_date statt out_invoice_date verwendet wird
    # (Das müsste aus BWA kommen, nicht aus dealer_vehicles)
    
    # Ausgabe GW-Tests
    print(f"{'Filter':<30} {'Stück':<10} {'Diff zu GC':<15} {'Diff %':<10}")
    print("-" * 100)
    
    beste_gw = None
    beste_diff_gw = float('inf')
    
    for name, stueck in gw_tests:
        diff = stueck - globalcube_gw
        diff_pct = (diff / globalcube_gw * 100) if globalcube_gw > 0 else 0
        marker = "✅" if abs(diff) < 10 else "  "
        print(f"{marker} {name:<28} {stueck:<10} {diff:+.2f} Stk.      {diff_pct:+.2f}%")
        
        if abs(diff) < beste_diff_gw:
            beste_diff_gw = abs(diff)
            beste_gw = (name, stueck, diff)
    
    if beste_gw:
        print(f"\n  ✅ Beste GW-Übereinstimmung: {beste_gw[0]} = {beste_gw[1]} Stk. (Diff: {beste_gw[2]:+.2f})")
    
    # 3. Kombinierte Analyse: Welche Kombination passt am besten?
    print(f"\n\n3. KOMBINIERTE ANALYSE:")
    print("-" * 100)
    
    if beste_nw and beste_gw:
        print(f"  NW: {beste_nw[0]} = {beste_nw[1]} Stk. (Diff: {beste_nw[2]:+.2f})")
        print(f"  GW: {beste_gw[0]} = {beste_gw[1]} Stk. (Diff: {beste_gw[2]:+.2f})")
        
        if abs(beste_nw[2]) < 5 and abs(beste_gw[2]) < 10:
            print(f"\n  ✅ Diese Filter-Kombination könnte Global Cube entsprechen!")
        else:
            print(f"\n  ⚠️  Noch keine perfekte Übereinstimmung gefunden.")
            print(f"     Möglicherweise verwendet Global Cube andere Filter oder Zeiträume.")

