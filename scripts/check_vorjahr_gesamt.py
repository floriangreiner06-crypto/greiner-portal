#!/usr/bin/env python3
"""
Prüft Vorjahreswerte für gesamtes Unternehmen (Sep 24 - Aug 25)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db_utils import locosoft_session

def main():
    vj_von = "2024-09-01"
    vj_bis = "2025-09-01"
    
    print(f"Prüfe Vorjahreswerte für Geschäftsjahr 2024/25 (Sep 24 - Aug 25)")
    print(f"Zeitraum: {vj_von} bis {vj_bis}")
    print()
    
    with locosoft_session() as conn_loco:
        cursor_loco = conn_loco.cursor()
        
        # GW: dealer_vehicle_type IN ('G', 'D')
        # WICHTIG: Nur fakturierte Fahrzeuge (out_invoice_date IS NOT NULL)
        # UND out_sale_price > 0 (um Testdaten auszuschließen)
        cursor_loco.execute("""
            SELECT COUNT(*) as stueck
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type IN ('G', 'D')
              AND out_sale_price > 0
        """, (vj_von, vj_bis))
        row = cursor_loco.fetchone()
        gw_gesamt = int(row[0] or 0) if row else 0
        
        # NW: dealer_vehicle_type IN ('N', 'V')
        cursor_loco.execute("""
            SELECT COUNT(*) as stueck
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type IN ('N', 'V')
              AND out_sale_price > 0
        """, (vj_von, vj_bis))
        row = cursor_loco.fetchone()
        nw_gesamt = int(row[0] or 0) if row else 0
        
        # GW nach Standort aufgeteilt
        cursor_loco.execute("""
            SELECT 
                out_subsidiary,
                COUNT(*) as stueck
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type IN ('G', 'D')
              AND out_sale_price > 0
            GROUP BY out_subsidiary
            ORDER BY out_subsidiary
        """, (vj_von, vj_bis))
        rows = cursor_loco.fetchall()
        
        print(f"GW gesamt (alle Standorte): {gw_gesamt}")
        print(f"NW gesamt (alle Standorte): {nw_gesamt}")
        print()
        print("GW nach Standort (out_subsidiary):")
        for row in rows:
            subsidiary = row[0]
            stueck = row[1]
            standort_name = {1: "Stellantis (DEG+LAN)", 2: "Hyundai DEG"}.get(subsidiary, f"Unbekannt ({subsidiary})")
            print(f"  {standort_name}: {stueck} Stk.")
        
        print()
        print(f"Erwartet: 625 GW, 444 NW")
        print(f"Gefunden: {gw_gesamt} GW, {nw_gesamt} NW")
        
        if gw_gesamt != 625:
            print(f"⚠️  GW-Abweichung: {625 - gw_gesamt} Stk.")
        if nw_gesamt != 444:
            print(f"⚠️  NW-Abweichung: {444 - nw_gesamt} Stk.")

if __name__ == '__main__':
    main()

