"""
Vergleich: Stückzahlen Global Cube vs. DRIVE BWA
==================================================
Prüft Unterschiede in der Interpretation
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')
import csv
import codecs

from api.db_utils import db_session, locosoft_session
from api.db_connection import convert_placeholders

# Geschäftsjahr 2024/25: Sep 2024 - Aug 2025
gj_von = "2024-09-01"
gj_bis = "2025-09-01"

print("=" * 80)
print("Vergleich: Stückzahlen Global Cube vs. DRIVE BWA")
print("Geschäftsjahr 2024/25 (Sep 2024 - Aug 2025)")
print("=" * 80)

# 1. Global Cube CSV parsen
csv_path = "/opt/greiner-portal/docs/F.03 BWA Vorjahres-Vergleich (17).csv"

globalcube_nw = None
globalcube_gw = None

try:
    # Versuche verschiedene Encodings und Delimiter
    encodings = ['utf-16', 'utf-8', 'latin-1', 'cp1252']
    csv_data = None
    
    for encoding in encodings:
        try:
            with codecs.open(csv_path, 'r', encoding=encoding) as f:
                # Versuche Tab-Delimiter
                csv_data = list(csv.reader(f, delimiter='\t'))
                if len(csv_data) > 4 and len(csv_data[4]) > 17:
                    print(f"\n✅ CSV erfolgreich gelesen mit Encoding: {encoding}, Delimiter: Tab")
                    break
                # Falls Tab nicht funktioniert, versuche Komma
                f.seek(0)
                csv_data = list(csv.reader(f))
                if len(csv_data) > 4 and len(csv_data[4]) > 17:
                    print(f"\n✅ CSV erfolgreich gelesen mit Encoding: {encoding}, Delimiter: Komma")
                    break
        except Exception as e:
            continue
    
    if csv_data is None:
        print("❌ Konnte CSV nicht lesen")
    else:
        # Suche nach Stückzahlen
        # Zeile 4 (Index 3): Neuwagen Stk. - Spalte 17 = Jahr (444,02)
        # Zeile 5 (Index 4): Gebrauchtwagen Stk. - Spalte 17 = Jahr (625,17)
        for i, row in enumerate(csv_data):
            if len(row) > 0:
                row_text = ' '.join(row).lower()
                
                # Zeile 4: Neuwagen Stk. - Spalte 17 = Jahr
                if 'neuwagen' in row_text and 'stk' in row_text and len(row) > 17:
                    try:
                        cell = row[17].strip().replace(',', '.')
                        num = float(cell)
                        if 400 < num < 600:
                            globalcube_nw = num
                            print(f"  Global Cube NW (Jahr, Spalte 17): {num:.2f} Stk.")
                    except:
                        pass
                
                # Zeile 5: Gebrauchtwagen Stk. - Spalte 17 = Jahr
                if 'gebrauchtwagen' in row_text and 'stk' in row_text and len(row) > 17:
                    try:
                        cell = row[17].strip().replace(',', '.')
                        num = float(cell)
                        if 600 < num < 650:
                            globalcube_gw = num
                            print(f"  Global Cube GW (Jahr, Spalte 17): {num:.2f} Stk.")
                    except:
                        pass
        
        # Alternative: Direkt aus bekannten Zeilen extrahieren
        # Zeile 4 (Index 3): Neuwagen - Spalte 17 = Jahr (444,02)
        # Zeile 5 (Index 4): Gebrauchtwagen - Spalte 17 = Jahr (625,17)
        if globalcube_nw is None and len(csv_data) > 3:
            row4 = csv_data[3]  # Index 3 = Zeile 4
            if len(row4) > 17:
                try:
                    cell = row4[17].strip().replace(',', '.')
                    num = float(cell)
                    if 400 < num < 600:
                        globalcube_nw = num
                        print(f"  Global Cube NW (Spalte 17 = Jahr): {num:.2f} Stk.")
                except:
                    pass
        
        if globalcube_gw is None and len(csv_data) > 4:
            row5 = csv_data[4]  # Index 4 = Zeile 5
            if len(row5) > 17:
                try:
                    cell = row5[17].strip().replace(',', '.')
                    num = float(cell)
                    if 600 < num < 650:
                        globalcube_gw = num
                        print(f"  Global Cube GW (Spalte 17 = Jahr): {num:.2f} Stk.")
                except:
                    pass

except Exception as e:
    print(f"⚠️  Fehler beim Lesen der CSV: {e}")
    import traceback
    traceback.print_exc()

# 2. DRIVE BWA Stückzahlen (verschiedene Interpretationen)
print(f"\n2. DRIVE BWA Stückzahlen (verschiedene Filter):")

with locosoft_session() as conn_loco:
    cursor_loco = conn_loco.cursor()
    
    # A) Standard: out_invoice_date, dealer_vehicle_type IN ('G', 'D')
    cursor_loco.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D')
    """, (gj_von, gj_bis))
    row = cursor_loco.fetchone()
    stueck_gw_standard = int(row[0] or 0) if row else 0
    print(f"  A) Standard (G+D, out_invoice_date): {stueck_gw_standard} Stk.")
    
    # B) Nur 'G' (ohne 'D')
    cursor_loco.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type = 'G'
    """, (gj_von, gj_bis))
    row = cursor_loco.fetchone()
    stueck_gw_nur_g = int(row[0] or 0) if row else 0
    print(f"  B) Nur 'G' (ohne 'D'): {stueck_gw_nur_g} Stk.")
    
    # C) Mit out_sale_price > 0 (nur echte Verkäufe)
    cursor_loco.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D')
          AND out_sale_price > 0
    """, (gj_von, gj_bis))
    row = cursor_loco.fetchone()
    stueck_gw_mit_preis = int(row[0] or 0) if row else 0
    print(f"  C) Mit out_sale_price > 0: {stueck_gw_mit_preis} Stk.")
    
    # D) DISTINCT vehicle_number (keine Duplikate)
    cursor_loco.execute("""
        SELECT COUNT(DISTINCT vehicle_number) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D')
          AND vehicle_number IS NOT NULL
    """, (gj_von, gj_bis))
    row = cursor_loco.fetchone()
    stueck_gw_distinct_vin = int(row[0] or 0) if row else 0
    print(f"  D) DISTINCT vehicle_number: {stueck_gw_distinct_vin} Stk.")
    
    # E) Nach Standort aufgeschlüsselt
    print(f"\n  E) Nach Standort aufgeschlüsselt:")
    cursor_loco.execute("""
        SELECT 
            CASE 
                WHEN out_subsidiary = 1 THEN 'Deggendorf (Stellantis)'
                WHEN out_subsidiary = 2 THEN 'Deggendorf (Hyundai)'
                WHEN out_subsidiary = 3 THEN 'Landau'
                ELSE 'Unbekannt'
            END as standort,
            COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D')
        GROUP BY out_subsidiary
        ORDER BY out_subsidiary
    """, (gj_von, gj_bis))
    
    for row in cursor_loco.fetchall():
        standort = row[0]
        stueck = int(row[1] or 0)
        print(f"     {standort}: {stueck} Stk.")
    
    # F) Nach Typ aufgeschlüsselt
    print(f"\n  F) Nach Typ aufgeschlüsselt:")
    cursor_loco.execute("""
        SELECT 
            dealer_vehicle_type,
            COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D', 'N', 'V')
        GROUP BY dealer_vehicle_type
        ORDER BY dealer_vehicle_type
    """, (gj_von, gj_bis))
    
    for row in cursor_loco.fetchall():
        typ = row[0]
        stueck = int(row[1] or 0)
        typ_name = {'G': 'Gebrauchtwagen', 'D': 'Demo', 'N': 'Neuwagen', 'V': 'Vorführwagen'}.get(typ, typ)
        print(f"     {typ_name} ({typ}): {stueck} Stk.")

# 3. Vergleich
print(f"\n3. VERGLEICH:")
if globalcube_gw:
    print(f"  Global Cube GW (Jahr): {globalcube_gw:.2f} Stk.")
    print(f"  DRIVE BWA (Standard G+D): {stueck_gw_standard} Stk.")
    print(f"  DRIVE BWA (Nur G): {stueck_gw_nur_g} Stk.")
    print(f"  DRIVE BWA (DISTINCT): {stueck_gw_distinct_vin} Stk.")
    
    print(f"\n  Differenzen:")
    print(f"    Standard vs. Global Cube: {stueck_gw_standard - globalcube_gw:+.2f} Stk. ({((stueck_gw_standard - globalcube_gw) / globalcube_gw * 100) if globalcube_gw > 0 else 0:+.2f}%)")
    print(f"    Nur G vs. Global Cube: {stueck_gw_nur_g - globalcube_gw:+.2f} Stk. ({((stueck_gw_nur_g - globalcube_gw) / globalcube_gw * 100) if globalcube_gw > 0 else 0:+.2f}%)")
    print(f"    DISTINCT vs. Global Cube: {stueck_gw_distinct_vin - globalcube_gw:+.2f} Stk. ({((stueck_gw_distinct_vin - globalcube_gw) / globalcube_gw * 100) if globalcube_gw > 0 else 0:+.2f}%)")
    
    # Demo-Fahrzeuge (D) = Differenz zwischen Standard und Nur G
    demo_anzahl = stueck_gw_standard - stueck_gw_nur_g
    print(f"\n  Demo-Fahrzeuge (D): {demo_anzahl} Stk.")
    print(f"  Wenn Global Cube nur 'G' zählt: {stueck_gw_nur_g} vs. {globalcube_gw:.2f} = Diff: {stueck_gw_nur_g - globalcube_gw:+.2f} Stk.")
    
    # Finde beste Übereinstimmung
    werte = [
        ('Standard (G+D)', stueck_gw_standard),
        ('Nur G', stueck_gw_nur_g),
        ('Mit Preis > 0', stueck_gw_mit_preis),
        ('DISTINCT vehicle_number', stueck_gw_distinct_vin)
    ]
    
    beste = min(werte, key=lambda x: abs(x[1] - globalcube_gw))
    print(f"\n  ✅ Beste Übereinstimmung: {beste[0]} = {beste[1]} Stk. (Diff: {abs(beste[1] - globalcube_gw):.2f})")
else:
    print("  ⚠️  Konnte Global Cube GW-Wert nicht extrahieren")

# NW-Vergleich (neue Connection)
with locosoft_session() as conn_loco2:
    cursor_loco2 = conn_loco2.cursor()
    
    if globalcube_nw:
        print(f"\n  Global Cube NW (Jahr): {globalcube_nw:.2f} Stk.")
        # NW aus DRIVE
        cursor_loco2.execute("""
            SELECT COUNT(*) as stueck
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type IN ('N', 'V')
        """, (gj_von, gj_bis))
        row = cursor_loco2.fetchone()
        stueck_nw = int(row[0] or 0) if row else 0
        print(f"  DRIVE BWA NW: {stueck_nw} Stk.")
        print(f"  Differenz: {stueck_nw - globalcube_nw:+.2f} Stk. ({((stueck_nw - globalcube_nw) / globalcube_nw * 100) if globalcube_nw > 0 else 0:+.2f}%)")

