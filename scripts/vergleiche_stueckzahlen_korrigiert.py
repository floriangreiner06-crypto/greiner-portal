"""
Vergleich: Stückzahlen Global Cube vs. DRIVE BWA (KORRIGIERT)
==============================================================
Tageszulassungen (T) gehören zu NW!
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')
import csv
import codecs

from api.db_utils import locosoft_session

# Geschäftsjahr 2024/25: Sep 2024 - Aug 2025
gj_von = "2024-09-01"
gj_bis = "2025-09-01"

print("=" * 80)
print("Vergleich: Stückzahlen Global Cube vs. DRIVE BWA (KORRIGIERT)")
print("Geschäftsjahr 2024/25 (Sep 2024 - Aug 2025)")
print("=" * 80)

# 1. Global Cube CSV parsen
csv_path = '/opt/greiner-portal/docs/F.03 BWA Vorjahres-Vergleich (17).csv'

globalcube_nw = None
globalcube_gw = None

try:
    with codecs.open(csv_path, 'r', encoding='utf-16') as f:
        csv_data = list(csv.reader(f, delimiter='\t'))
        
        # Zeile 4 (Index 3): Neuwagen - Spalte 17 = Jahr
        if len(csv_data) > 3 and len(csv_data[3]) > 17:
            try:
                cell = csv_data[3][17].strip().replace(',', '.')
                globalcube_nw = float(cell)
                print(f"\n✅ Global Cube NW (Jahr): {globalcube_nw:.2f} Stk.")
            except:
                pass
        
        # Zeile 5 (Index 4): Gebrauchtwagen - Spalte 17 = Jahr
        if len(csv_data) > 4 and len(csv_data[4]) > 17:
            try:
                cell = csv_data[4][17].strip().replace(',', '.')
                globalcube_gw = float(cell)
                print(f"✅ Global Cube GW (Jahr): {globalcube_gw:.2f} Stk.")
            except:
                pass
except Exception as e:
    print(f"⚠️  Fehler beim Lesen der CSV: {e}")

# 2. DRIVE BWA Stückzahlen (KORRIGIERT)
print(f"\n2. DRIVE BWA Stückzahlen (KORRIGIERT):")

with locosoft_session() as conn:
    cursor = conn.cursor()
    
    # NW: N + V + T (Tageszulassungen gehören zu NW!)
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('N', 'V', 'T')
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    stueck_nw_korrigiert = int(row[0] or 0) if row else 0
    
    # NW Aufschlüsselung
    cursor.execute("""
        SELECT 
            dealer_vehicle_type,
            COUNT(*) as anzahl
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('N', 'V', 'T')
        GROUP BY dealer_vehicle_type
        ORDER BY dealer_vehicle_type
    """, (gj_von, gj_bis))
    
    nw_aufschl = {}
    for row in cursor.fetchall():
        typ = row[0]
        anzahl = int(row[1] or 0)
        nw_aufschl[typ] = anzahl
    
    print(f"  NW (N+V+T): {stueck_nw_korrigiert} Stk.")
    print(f"    - N (Neuwagen): {nw_aufschl.get('N', 0)} Stk.")
    print(f"    - V (Vorführwagen): {nw_aufschl.get('V', 0)} Stk.")
    print(f"    - T (Tageszulassung): {nw_aufschl.get('T', 0)} Stk.")
    
    # GW: Verschiedene Interpretationen
    print(f"\n  GW (verschiedene Interpretationen):")
    
    # A) Nur G
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type = 'G'
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    stueck_gw_nur_g = int(row[0] or 0) if row else 0
    print(f"    A) Nur G: {stueck_gw_nur_g} Stk.")
    
    # B) G + D
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D')
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    stueck_gw_g_plus_d = int(row[0] or 0) if row else 0
    print(f"    B) G + D: {stueck_gw_g_plus_d} Stk.")
    
    # C) DISTINCT vehicle_number (G+D)
    cursor.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D')
          AND vehicle_number IS NOT NULL
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    stueck_gw_distinct = int(row[0] or 0) if row else 0
    print(f"    C) G + D (DISTINCT vehicle_number): {stueck_gw_distinct} Stk.")
    
    # D) G + D mit out_sale_price > 0
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D')
          AND out_sale_price > 0
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    stueck_gw_mit_preis = int(row[0] or 0) if row else 0
    print(f"    D) G + D (mit Preis > 0): {stueck_gw_mit_preis} Stk.")

# 3. Vergleich
print(f"\n3. VERGLEICH:")
print("-" * 80)

if globalcube_nw:
    print(f"\nNW (Neuwagen):")
    print(f"  Global Cube: {globalcube_nw:.2f} Stk.")
    print(f"  DRIVE BWA (N+V+T): {stueck_nw_korrigiert} Stk.")
    diff_nw = stueck_nw_korrigiert - globalcube_nw
    print(f"  Differenz: {diff_nw:+.2f} Stk. ({diff_nw/globalcube_nw*100 if globalcube_nw > 0 else 0:+.2f}%)")
    
    if abs(diff_nw) < 20:
        print(f"  ✅ Sehr gute Übereinstimmung!")

if globalcube_gw:
    print(f"\nGW (Gebrauchtwagen):")
    print(f"  Global Cube: {globalcube_gw:.2f} Stk.")
    print(f"  DRIVE BWA (Nur G): {stueck_gw_nur_g} Stk. (Diff: {stueck_gw_nur_g - globalcube_gw:+.2f})")
    print(f"  DRIVE BWA (G+D): {stueck_gw_g_plus_d} Stk. (Diff: {stueck_gw_g_plus_d - globalcube_gw:+.2f})")
    print(f"  DRIVE BWA (DISTINCT): {stueck_gw_distinct} Stk. (Diff: {stueck_gw_distinct - globalcube_gw:+.2f})")
    
    # Finde beste Übereinstimmung
    werte = [
        ('Nur G', stueck_gw_nur_g),
        ('G + D', stueck_gw_g_plus_d),
        ('DISTINCT vehicle_number', stueck_gw_distinct),
        ('Mit Preis > 0', stueck_gw_mit_preis)
    ]
    
    beste = min(werte, key=lambda x: abs(x[1] - globalcube_gw))
    print(f"\n  ✅ Beste Übereinstimmung: {beste[0]} = {beste[1]} Stk. (Diff: {abs(beste[1] - globalcube_gw):.2f})")

print(f"\n4. HINWEIS:")
print(f"  Programm 273 in Locosoft wird die Originalwerte liefern.")
print(f"  Diese können dann als Referenz für die korrekte Interpretation verwendet werden.")

