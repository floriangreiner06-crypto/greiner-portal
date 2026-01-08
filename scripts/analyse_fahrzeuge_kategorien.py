"""
Detaillierte Analyse: Fahrzeuge nach Locosoft-Kategorien
=========================================================
Geschäftsjahr 2024/25 (Sep 2024 - Aug 2025)
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session

# Geschäftsjahr 2024/25: Sep 2024 - Aug 2025
gj_von = "2024-09-01"
gj_bis = "2025-09-01"

print("=" * 100)
print("Detaillierte Analyse: Fahrzeuge nach Locosoft-Kategorien")
print(f"Geschäftsjahr 2024/25 (Sep 2024 - Aug 2025)")
print("=" * 100)

with locosoft_session() as conn:
    cursor = conn.cursor()
    
    # 1. Übersicht nach dealer_vehicle_type
    print("\n1. ÜBERSICHT NACH dealer_vehicle_type:")
    print("-" * 100)
    
    cursor.execute("""
        SELECT 
            dealer_vehicle_type,
            CASE 
                WHEN dealer_vehicle_type = 'G' THEN 'Gebrauchtwagen'
                WHEN dealer_vehicle_type = 'D' THEN 'Demo'
                WHEN dealer_vehicle_type = 'N' THEN 'Neuwagen'
                WHEN dealer_vehicle_type = 'V' THEN 'Vorführwagen'
                WHEN dealer_vehicle_type = 'T' THEN 'Tageszulassung'
                ELSE dealer_vehicle_type
            END as typ_name,
            COUNT(*) as anzahl,
            COUNT(CASE WHEN out_sale_price > 0 THEN 1 END) as mit_preis,
            COUNT(CASE WHEN out_sale_price = 0 OR out_sale_price IS NULL THEN 1 END) as ohne_preis,
            COUNT(DISTINCT vehicle_number) as distinct_vehicle,
            COUNT(DISTINCT dealer_vehicle_number) as distinct_dealer_vehicle
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
        GROUP BY dealer_vehicle_type
        ORDER BY dealer_vehicle_type
    """, (gj_von, gj_bis))
    
    print(f"{'Typ':<5} {'Name':<20} {'Anzahl':<10} {'Mit Preis':<12} {'Ohne Preis':<12} {'Distinct VN':<12} {'Distinct DVN':<12}")
    print("-" * 100)
    
    for row in cursor.fetchall():
        typ = row[0] or 'NULL'
        typ_name = row[1] or 'Unbekannt'
        anzahl = int(row[2] or 0)
        mit_preis = int(row[3] or 0)
        ohne_preis = int(row[4] or 0)
        distinct_vn = int(row[5] or 0)
        distinct_dvn = int(row[6] or 0)
        print(f"{typ:<5} {typ_name:<20} {anzahl:<10} {mit_preis:<12} {ohne_preis:<12} {distinct_vn:<12} {distinct_dvn:<12}")
    
    # 2. GW-spezifisch: Nach Standort aufgeschlüsselt
    print("\n\n2. GEBRAUCHTWAGEN (G) - NACH STANDORT:")
    print("-" * 100)
    
    cursor.execute("""
        SELECT 
            CASE 
                WHEN out_subsidiary = 1 THEN 'Deggendorf (Stellantis)'
                WHEN out_subsidiary = 2 THEN 'Deggendorf (Hyundai)'
                WHEN out_subsidiary = 3 THEN 'Landau'
                ELSE 'Unbekannt'
            END as standort,
            COUNT(*) as anzahl,
            COUNT(CASE WHEN out_sale_price > 0 THEN 1 END) as mit_preis,
            COUNT(CASE WHEN out_sale_price = 0 OR out_sale_price IS NULL THEN 1 END) as ohne_preis,
            COUNT(DISTINCT vehicle_number) as distinct_vehicle
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type = 'G'
        GROUP BY out_subsidiary
        ORDER BY out_subsidiary
    """, (gj_von, gj_bis))
    
    print(f"{'Standort':<30} {'Anzahl':<10} {'Mit Preis':<12} {'Ohne Preis':<12} {'Distinct VN':<12}")
    print("-" * 100)
    
    for row in cursor.fetchall():
        standort = row[0] or 'Unbekannt'
        anzahl = int(row[1] or 0)
        mit_preis = int(row[2] or 0)
        ohne_preis = int(row[3] or 0)
        distinct_vn = int(row[4] or 0)
        print(f"{standort:<30} {anzahl:<10} {mit_preis:<12} {ohne_preis:<12} {distinct_vn:<12}")
    
    # 3. Demo (D) - Nach Standort
    print("\n\n3. DEMO (D) - NACH STANDORT:")
    print("-" * 100)
    
    cursor.execute("""
        SELECT 
            CASE 
                WHEN out_subsidiary = 1 THEN 'Deggendorf (Stellantis)'
                WHEN out_subsidiary = 2 THEN 'Deggendorf (Hyundai)'
                WHEN out_subsidiary = 3 THEN 'Landau'
                ELSE 'Unbekannt'
            END as standort,
            COUNT(*) as anzahl,
            COUNT(CASE WHEN out_sale_price > 0 THEN 1 END) as mit_preis,
            COUNT(CASE WHEN out_sale_price = 0 OR out_sale_price IS NULL THEN 1 END) as ohne_preis
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type = 'D'
        GROUP BY out_subsidiary
        ORDER BY out_subsidiary
    """, (gj_von, gj_bis))
    
    print(f"{'Standort':<30} {'Anzahl':<10} {'Mit Preis':<12} {'Ohne Preis':<12}")
    print("-" * 100)
    
    for row in cursor.fetchall():
        standort = row[0] or 'Unbekannt'
        anzahl = int(row[1] or 0)
        mit_preis = int(row[2] or 0)
        ohne_preis = int(row[3] or 0)
        print(f"{standort:<30} {anzahl:<10} {mit_preis:<12} {ohne_preis:<12}")
    
    # 4. GW + D Kombinationen
    print("\n\n4. GW + D KOMBINATIONEN (Gesamtbetrieb):")
    print("-" * 100)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as gesamt,
            COUNT(CASE WHEN dealer_vehicle_type = 'G' THEN 1 END) as nur_g,
            COUNT(CASE WHEN dealer_vehicle_type = 'D' THEN 1 END) as nur_d,
            COUNT(CASE WHEN dealer_vehicle_type IN ('G', 'D') THEN 1 END) as g_plus_d,
            COUNT(CASE WHEN dealer_vehicle_type IN ('G', 'D') AND out_sale_price > 0 THEN 1 END) as g_plus_d_mit_preis,
            COUNT(DISTINCT CASE WHEN dealer_vehicle_type IN ('G', 'D') THEN vehicle_number END) as g_plus_d_distinct
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
    """, (gj_von, gj_bis))
    
    row = cursor.fetchone()
    if row:
        print(f"  Gesamt (alle Typen): {int(row[0] or 0)} Stk.")
        print(f"  Nur G: {int(row[1] or 0)} Stk.")
        print(f"  Nur D: {int(row[2] or 0)} Stk.")
        print(f"  G + D: {int(row[3] or 0)} Stk.")
        print(f"  G + D (mit Preis > 0): {int(row[4] or 0)} Stk.")
        print(f"  G + D (DISTINCT vehicle_number): {int(row[5] or 0)} Stk.")
    
    # 5. NW + V Kombinationen
    print("\n\n5. NW + V KOMBINATIONEN (Gesamtbetrieb):")
    print("-" * 100)
    
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN dealer_vehicle_type = 'N' THEN 1 END) as nur_n,
            COUNT(CASE WHEN dealer_vehicle_type = 'V' THEN 1 END) as nur_v,
            COUNT(CASE WHEN dealer_vehicle_type IN ('N', 'V') THEN 1 END) as n_plus_v,
            COUNT(CASE WHEN dealer_vehicle_type IN ('N', 'V') AND out_sale_price > 0 THEN 1 END) as n_plus_v_mit_preis,
            COUNT(DISTINCT CASE WHEN dealer_vehicle_type IN ('N', 'V') THEN vehicle_number END) as n_plus_v_distinct
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
    """, (gj_von, gj_bis))
    
    row = cursor.fetchone()
    if row:
        print(f"  Nur N: {int(row[0] or 0)} Stk.")
        print(f"  Nur V: {int(row[1] or 0)} Stk.")
        print(f"  N + V: {int(row[2] or 0)} Stk.")
        print(f"  N + V (mit Preis > 0): {int(row[3] or 0)} Stk.")
        print(f"  N + V (DISTINCT vehicle_number): {int(row[4] or 0)} Stk.")
    
    # 6. Beispiel-Fahrzeuge pro Kategorie (erste 5)
    print("\n\n6. BEISPIEL-FAHRZEUGE (erste 5 pro Kategorie):")
    print("-" * 100)
    
    for typ in ['G', 'D', 'N', 'V']:
        typ_name = {'G': 'Gebrauchtwagen', 'D': 'Demo', 'N': 'Neuwagen', 'V': 'Vorführwagen'}.get(typ, typ)
        print(f"\n{typ_name} ({typ}):")
        cursor.execute("""
            SELECT 
                dealer_vehicle_number,
                vehicle_number,
                out_invoice_date,
                out_sale_price,
                dealer_vehicle_type,
                CASE 
                    WHEN out_subsidiary = 1 THEN 'DEG Stellantis'
                    WHEN out_subsidiary = 2 THEN 'DEG Hyundai'
                    WHEN out_subsidiary = 3 THEN 'Landau'
                    ELSE 'Unbekannt'
                END as standort
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type = %s
            ORDER BY out_invoice_date DESC
            LIMIT 5
        """, (gj_von, gj_bis, typ))
        
        print(f"  {'DV-Nr':<12} {'V-Nr':<12} {'Rechnungsdatum':<15} {'Verkaufspreis':<15} {'Standort':<15}")
        print("  " + "-" * 70)
        
        for row in cursor.fetchall():
            dv_nr = str(row[0] or '')[:12]
            v_nr = str(row[1] or '')[:12]
            rechnungsdatum = str(row[2] or '')[:15]
            verkaufspreis = f"{float(row[3] or 0):,.2f} €" if row[3] else "0,00 €"
            standort = row[5] or 'Unbekannt'
            print(f"  {dv_nr:<12} {v_nr:<12} {rechnungsdatum:<15} {verkaufspreis:<15} {standort:<15}")

