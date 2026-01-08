"""
Analyse: Landau Standort-Filter in Locosoft
===========================================
Prüft die tatsächlichen subsidiary-Werte für Landau-Fahrzeuge in Locosoft.
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session, db_session, row_to_dict
from api.db_connection import convert_placeholders

print("=" * 100)
print("ANALYSE: Landau Standort-Filter in Locosoft")
print("=" * 100)

# Zeitraum: Geschäftsjahr 2024/25 (Sep 2024 - Aug 2025)
vj_von = "2024-09-01"
vj_bis = "2025-09-01"

print(f"\nZeitraum: {vj_von} bis {vj_bis}")
print("\n" + "=" * 100)

# 1. dealer_vehicles: Welche subsidiary-Werte haben Landau-Fahrzeuge?
print("\n1. DEALER_VEHICLES - Verkäufe (out_subsidiary):")
print("-" * 100)

with locosoft_session() as conn_loco:
    cursor_loco = conn_loco.cursor()
    
    # Alle GW-Verkäufe im Zeitraum nach subsidiary gruppiert
    cursor_loco.execute("""
        SELECT 
            out_subsidiary,
            COUNT(*) as stueck,
            SUM(out_sale_price) as umsatz,
            AVG(out_sale_price) as avg_preis
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D', 'L')
        GROUP BY out_subsidiary
        ORDER BY out_subsidiary
    """, (vj_von, vj_bis))
    
    rows = cursor_loco.fetchall()
    print(f"{'Subsidiary':<15} {'Stück':<10} {'Umsatz (€)':<20} {'Ø Preis (€)':<15}")
    print("-" * 100)
    for row in rows:
        print(f"{row[0]:<15} {row[1]:<10} {row[2]:>15,.2f} {row[3]:>15,.2f}")
    
    # Landau-spezifisch: location-Filter
    print("\n\n1b. DEALER_VEHICLES - Landau nach location:")
    print("-" * 100)
    cursor_loco.execute("""
        SELECT 
            location,
            out_subsidiary,
            COUNT(*) as stueck,
            SUM(out_sale_price) as umsatz
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D', 'L')
          AND location LIKE '%%LAN%%'
        GROUP BY location, out_subsidiary
        ORDER BY location, out_subsidiary
    """, (vj_von, vj_bis))
    
    rows = cursor_loco.fetchall()
    print(f"{'Location':<15} {'Subsidiary':<15} {'Stück':<10} {'Umsatz (€)':<20}")
    print("-" * 100)
    for row in rows:
        print(f"{row[0]:<15} {row[1]:<15} {row[2]:<10} {row[3]:>15,.2f}")

# 2. dealer_vehicles: Bestand (in_subsidiary)
print("\n\n2. DEALER_VEHICLES - Bestand (in_subsidiary):")
print("-" * 100)

with locosoft_session() as conn_loco:
    cursor_loco = conn_loco.cursor()
    
    cursor_loco.execute("""
        SELECT 
            in_subsidiary,
            COUNT(*) as stueck,
            AVG(CURRENT_DATE - COALESCE(in_arrival_date, created_date)) as avg_standzeit
        FROM dealer_vehicles
        WHERE out_invoice_date IS NULL
          AND dealer_vehicle_type IN ('G', 'D', 'L')
          AND in_arrival_date IS NOT NULL
        GROUP BY in_subsidiary
        ORDER BY in_subsidiary
    """)
    
    rows = cursor_loco.fetchall()
    print(f"{'Subsidiary':<15} {'Stück (Bestand)':<20} {'Ø Standzeit (Tage)':<25}")
    print("-" * 100)
    for row in rows:
        print(f"{row[0]:<15} {row[1]:<20} {row[2]:>25,.1f}")
    
    # Landau-spezifisch
    print("\n\n2b. DEALER_VEHICLES - Landau Bestand nach location:")
    print("-" * 100)
    cursor_loco.execute("""
        SELECT 
            location,
            in_subsidiary,
            COUNT(*) as stueck,
            AVG(CURRENT_DATE - COALESCE(in_arrival_date, created_date)) as avg_standzeit
        FROM dealer_vehicles
        WHERE out_invoice_date IS NULL
          AND dealer_vehicle_type IN ('G', 'D', 'L')
          AND in_arrival_date IS NOT NULL
          AND location LIKE '%%LAN%%'
        GROUP BY location, in_subsidiary
        ORDER BY location, in_subsidiary
    """)
    
    rows = cursor_loco.fetchall()
    print(f"{'Location':<15} {'Subsidiary':<15} {'Stück':<10} {'Ø Standzeit (Tage)':<25}")
    print("-" * 100)
    for row in rows:
        print(f"{row[0]:<15} {row[1]:<15} {row[2]:<10} {row[3]:>25,.1f}")

# 3. BWA: Landau-Werte zum Vergleich
print("\n\n3. BWA - Landau GW-Werte (zum Vergleich):")
print("-" * 100)

with db_session() as conn:
    cursor = conn.cursor()
    
    from api.controlling_api import build_firma_standort_filter, BEREICHE_CONFIG, _berechne_bereich_werte
    
    # Landau: firma='1', standort='2' (laut build_firma_standort_filter)
    firma_filter_umsatz, firma_filter_einsatz, _, _ = build_firma_standort_filter('1', '2')
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    
    gw_config = BEREICHE_CONFIG['GW']
    gw_werte = _berechne_bereich_werte(cursor, 'GW', gw_config, vj_von, vj_bis,
                                       firma_filter_umsatz, guv_filter, firma_filter_einsatz)
    
    print(f"Umsatz: {gw_werte['erlos']:,.2f} €")
    print(f"Einsatz: {gw_werte['einsatz']:,.2f} €")
    print(f"DB1: {gw_werte['bruttoertrag']:,.2f} €")

# 4. Vergleich: Was sollte Landau sein?
print("\n\n4. ERWARTETE WERTE (aus Screenshot):")
print("-" * 100)
print("Stück: 351")
print("Umsatz: 2.455.065,42 €")
print("DB1: 80.398,34 €")
print("\n" + "=" * 100)
print("\nFAZIT: Welche subsidiary-Werte haben Landau-Fahrzeuge?")
print("=" * 100)

