"""
Detaillierte Analyse: Global Cube CSV Version 18
================================================
Analysiert die detaillierte Aufschlüsselung der Global Cube BWA
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session

print("=" * 100)
print("Detaillierte Analyse: Global Cube CSV Version 18")
print("=" * 100)

# Aus der CSV-Datei extrahierte Werte (Spalte 17 = "Jahr")
globalcube_data = {
    'NW': {
        'Gesamt': 444.02,
        'Kunden Kauf': 47.17,
        'Kunden Leasing': 79.73,
        'Gewerbek. Kauf': 19.0,
        'Gewerbek. Leasing': 29.86,
        'Großkunden Kauf': 43.0,
        'Großkunden Leasing': 22.0,
        'VFW Kunden Kauf': 202.26,
        'Vermittler Kauf': 1.0
    },
    'GW': {
        'Gesamt': 625.17,
        'Kunden': 624.5,
        'Eintausch': 146.67,
        'Zukauf': 221.83,
        'Leas./Rückn.': 209.0,
        'Geschäftsw.': 47.0,
        'Handel': 0.67
    }
}

print("\nGlobal Cube Werte (Jahr 2024/25):")
print("-" * 100)
print(f"NW Gesamt: {globalcube_data['NW']['Gesamt']:.2f} Stk.")
print(f"  - Kunden Kauf: {globalcube_data['NW']['Kunden Kauf']:.2f}")
print(f"  - Kunden Leasing: {globalcube_data['NW']['Kunden Leasing']:.2f}")
print(f"  - Gewerbek. Kauf: {globalcube_data['NW']['Gewerbek. Kauf']:.2f}")
print(f"  - Gewerbek. Leasing: {globalcube_data['NW']['Gewerbek. Leasing']:.2f}")
print(f"  - Großkunden Kauf: {globalcube_data['NW']['Großkunden Kauf']:.2f}")
print(f"  - Großkunden Leasing: {globalcube_data['NW']['Großkunden Leasing']:.2f}")
print(f"  - VFW Kunden Kauf: {globalcube_data['NW']['VFW Kunden Kauf']:.2f}")
print(f"  - Vermittler Kauf: {globalcube_data['NW']['Vermittler Kauf']:.2f}")

nw_sum = (globalcube_data['NW']['Kunden Kauf'] + 
          globalcube_data['NW']['Kunden Leasing'] + 
          globalcube_data['NW']['Gewerbek. Kauf'] + 
          globalcube_data['NW']['Gewerbek. Leasing'] + 
          globalcube_data['NW']['Großkunden Kauf'] + 
          globalcube_data['NW']['Großkunden Leasing'] + 
          globalcube_data['NW']['VFW Kunden Kauf'] + 
          globalcube_data['NW']['Vermittler Kauf'])
print(f"  Summe Kategorien: {nw_sum:.2f} Stk.")
print(f"  Differenz zu Gesamt: {globalcube_data['NW']['Gesamt'] - nw_sum:.2f} Stk.")

print(f"\nGW Gesamt: {globalcube_data['GW']['Gesamt']:.2f} Stk.")
print(f"  - Kunden: {globalcube_data['GW']['Kunden']:.2f}")
print(f"  - Eintausch: {globalcube_data['GW']['Eintausch']:.2f}")
print(f"  - Zukauf: {globalcube_data['GW']['Zukauf']:.2f}")
print(f"  - Leas./Rückn.: {globalcube_data['GW']['Leas./Rückn.']:.2f}")
print(f"  - Geschäftsw.: {globalcube_data['GW']['Geschäftsw.']:.2f}")
print(f"  - Handel: {globalcube_data['GW']['Handel']:.2f}")

gw_sum = (globalcube_data['GW']['Kunden'] + 
          globalcube_data['GW']['Eintausch'] + 
          globalcube_data['GW']['Zukauf'] + 
          globalcube_data['GW']['Leas./Rückn.'] + 
          globalcube_data['GW']['Geschäftsw.'] + 
          globalcube_data['GW']['Handel'])
print(f"  Summe Kategorien: {gw_sum:.2f} Stk.")
print(f"  Differenz zu Gesamt: {globalcube_data['GW']['Gesamt'] - gw_sum:.2f} Stk.")

# Analyse: Was könnte "GW Kunden" vs "GW Gesamt" bedeuten?
print("\n" + "=" * 100)
print("Hypothese: GW Kategorien")
print("=" * 100)
print("'GW Kunden' (624,5) ist fast gleich 'GW Gesamt' (625,17)")
print("Mögliche Interpretationen:")
print("  1. 'GW Gesamt' = 'GW Kunden' + andere Kategorien?")
print("  2. 'GW Kunden' = Hauptverkäufe, andere = Nebenkategorien?")
print("  3. 'GW Gesamt' könnte DISTINCT vehicle_number sein?")

# Vergleich mit DRIVE BWA
print("\n" + "=" * 100)
print("Vergleich mit DRIVE BWA:")
print("=" * 100)

gj_von = "2024-09-01"
gj_bis = "2025-09-01"

with locosoft_session() as conn:
    cursor = conn.cursor()
    
    # NW (N+T+V)
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('N', 'T', 'V')
    """, (gj_von, gj_bis))
    drive_nw = int(cursor.fetchone()[0] or 0)
    
    # GW (D+G+L)
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
    """, (gj_von, gj_bis))
    drive_gw = int(cursor.fetchone()[0] or 0)
    
    # GW nur G
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type = 'G'
    """, (gj_von, gj_bis))
    drive_gw_g = int(cursor.fetchone()[0] or 0)
    
    # GW DISTINCT vehicle_number
    cursor.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
          AND vehicle_number IS NOT NULL
    """, (gj_von, gj_bis))
    drive_gw_distinct = int(cursor.fetchone()[0] or 0)
    
    # GW nur G DISTINCT
    cursor.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type = 'G'
          AND vehicle_number IS NOT NULL
    """, (gj_von, gj_bis))
    drive_gw_g_distinct = int(cursor.fetchone()[0] or 0)
    
    # GW mit Preis > 0
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
          AND out_sale_price > 0
    """, (gj_von, gj_bis))
    drive_gw_with_price = int(cursor.fetchone()[0] or 0)
    
    # GW nur G mit Preis > 0
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type = 'G'
          AND out_sale_price > 0
    """, (gj_von, gj_bis))
    drive_gw_g_with_price = int(cursor.fetchone()[0] or 0)
    
    print(f"\nNW:")
    print(f"  Global Cube: {globalcube_data['NW']['Gesamt']:.2f} Stk.")
    print(f"  DRIVE (N+T+V): {drive_nw} Stk.")
    diff_nw = drive_nw - globalcube_data['NW']['Gesamt']
    diff_pct_nw = (diff_nw / globalcube_data['NW']['Gesamt']) * 100 if globalcube_data['NW']['Gesamt'] > 0 else 0
    print(f"  Differenz: {diff_nw:+.2f} Stk. ({diff_pct_nw:+.2f}%)")
    
    print(f"\nGW - Verschiedene Interpretationen:")
    print(f"  Global Cube Gesamt: {globalcube_data['GW']['Gesamt']:.2f} Stk.")
    print(f"  Global Cube Kunden: {globalcube_data['GW']['Kunden']:.2f} Stk.")
    print(f"\n  DRIVE Optionen:")
    print(f"    A) D+G+L (alle): {drive_gw} Stk. (Diff: {drive_gw - globalcube_data['GW']['Gesamt']:+.2f})")
    print(f"    B) Nur G: {drive_gw_g} Stk. (Diff: {drive_gw_g - globalcube_data['GW']['Gesamt']:+.2f})")
    print(f"    C) D+G+L DISTINCT: {drive_gw_distinct} Stk. (Diff: {drive_gw_distinct - globalcube_data['GW']['Gesamt']:+.2f})")
    print(f"    D) Nur G DISTINCT: {drive_gw_g_distinct} Stk. (Diff: {drive_gw_g_distinct - globalcube_data['GW']['Gesamt']:+.2f})")
    print(f"    E) D+G+L mit Preis: {drive_gw_with_price} Stk. (Diff: {drive_gw_with_price - globalcube_data['GW']['Gesamt']:+.2f})")
    print(f"    F) Nur G mit Preis: {drive_gw_g_with_price} Stk. (Diff: {drive_gw_g_with_price - globalcube_data['GW']['Gesamt']:+.2f})")
    
    # Finde beste Übereinstimmung
    gw_options = {
        'D+G+L (alle)': drive_gw,
        'Nur G': drive_gw_g,
        'D+G+L DISTINCT': drive_gw_distinct,
        'Nur G DISTINCT': drive_gw_g_distinct,
        'D+G+L mit Preis': drive_gw_with_price,
        'Nur G mit Preis': drive_gw_g_with_price
    }
    
    beste_gw_name = None
    beste_diff = float('inf')
    
    for name, value in gw_options.items():
        diff = abs(value - globalcube_data['GW']['Gesamt'])
        if diff < beste_diff:
            beste_diff = diff
            beste_gw_name = name
    
    print(f"\n  ✅ Beste Übereinstimmung für 'GW Gesamt':")
    print(f"     {beste_gw_name} = {gw_options[beste_gw_name]} Stk.")
    print(f"     Differenz: {gw_options[beste_gw_name] - globalcube_data['GW']['Gesamt']:+.2f} Stk.")
    
    # Teste auch "GW Kunden"
    beste_gw_kunden_name = None
    beste_diff_kunden = float('inf')
    
    for name, value in gw_options.items():
        diff = abs(value - globalcube_data['GW']['Kunden'])
        if diff < beste_diff_kunden:
            beste_diff_kunden = diff
            beste_gw_kunden_name = name
    
    print(f"\n  ✅ Beste Übereinstimmung für 'GW Kunden':")
    print(f"     {beste_gw_kunden_name} = {gw_options[beste_gw_kunden_name]} Stk.")
    print(f"     Differenz: {gw_options[beste_gw_kunden_name] - globalcube_data['GW']['Kunden']:+.2f} Stk.")

