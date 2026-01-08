#!/usr/bin/env python3
"""
Prüft Vorjahreswerte für Deggendorf (Standort 1) für Geschäftsjahr 2024/25
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db_utils import locosoft_session

def main():
    vj_von = "2024-09-01"
    vj_bis = "2025-09-01"
    
    print(f"Prüfe Vorjahreswerte für Deggendorf (Standort 1) - Geschäftsjahr 2024/25")
    print(f"Zeitraum: {vj_von} bis {vj_bis}")
    print()
    
    with locosoft_session() as conn_loco:
        cursor_loco = conn_loco.cursor()
        
        # GW für Deggendorf: Stellantis (subsidiary=1) + Hyundai (subsidiary=2)
        cursor_loco.execute("""
            SELECT COUNT(*) as stueck
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type IN ('G', 'D')
              AND (out_subsidiary = 1 OR out_subsidiary = 2)
        """, (vj_von, vj_bis))
        row = cursor_loco.fetchone()
        gw_deggendorf = int(row[0] or 0) if row else 0
        
        # GW nach subsidiary aufgeteilt
        cursor_loco.execute("""
            SELECT 
                out_subsidiary,
                COUNT(*) as stueck
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type IN ('G', 'D')
              AND (out_subsidiary = 1 OR out_subsidiary = 2)
            GROUP BY out_subsidiary
            ORDER BY out_subsidiary
        """, (vj_von, vj_bis))
        rows = cursor_loco.fetchall()
        
        print(f"GW Deggendorf gesamt (subsidiary 1+2): {gw_deggendorf}")
        print()
        print("GW nach subsidiary:")
        for row in rows:
            subsidiary = row[0]
            stueck = row[1]
            standort_name = {1: "Stellantis", 2: "Hyundai"}.get(subsidiary, f"Unbekannt ({subsidiary})")
            print(f"  {standort_name} (subsidiary {subsidiary}): {stueck} Stk.")
        
        # Prüfe auch für einen einzelnen Monat (z.B. Januar 2025 = GJ-Monat 5)
        monat_von = "2025-01-01"
        monat_bis = "2025-02-01"
        cursor_loco.execute("""
            SELECT COUNT(*) as stueck
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type IN ('G', 'D')
              AND (out_subsidiary = 1 OR out_subsidiary = 2)
        """, (monat_von, monat_bis))
        row = cursor_loco.fetchone()
        gw_monat = int(row[0] or 0) if row else 0
        
        print()
        print(f"GW Deggendorf für Januar 2025 (GJ-Monat 5): {gw_monat} Stk.")
        print()
        print(f"Wenn 29 Stk. für einen Monat stimmt, dann wären das für 12 Monate: {29 * 12} Stk.")
        print(f"Tatsächlich gefunden (Jahr): {gw_deggendorf} Stk.")

if __name__ == '__main__':
    main()

