#!/usr/bin/env python3
"""
Vergleicht BWA-Werte aus Global Cube CSV mit DRIVE BWA
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db_utils import db_session, locosoft_session, row_to_dict
from api.db_connection import convert_placeholders

def main():
    # Werte aus CSV (manuell extrahiert aus Zeile 4 und 5)
    # Zeile 4: Neuwagen Stk. - Kumuliert per Aug./2025: 444,02
    # Zeile 5: Gebrauchtwagen Stk. - Kumuliert per Aug./2025: 625,17
    globalcube = {
        'NW_stueck': 444.02,  # Geschäftsjahr 2024/25 (Sep 24 - Aug 25)
        'GW_stueck': 625.17   # Geschäftsjahr 2024/25 (Sep 24 - Aug 25)
    }
    
    print("=" * 80)
    print("BWA-Vergleich: Global Cube CSV vs. DRIVE BWA")
    print("=" * 80)
    print()
    print(f"Global Cube CSV (Geschäftsjahr 2024/25, Sep 24 - Aug 25):")
    print(f"   NW Stück: {globalcube['NW_stueck']:.2f}")
    print(f"   GW Stück: {globalcube['GW_stueck']:.2f}")
    print()
    
    # DRIVE BWA Werte holen
    vj_von = "2024-09-01"
    vj_bis = "2025-09-01"
    
    print("📊 Lese DRIVE BWA Werte aus Locosoft dealer_vehicles...")
    
    with locosoft_session() as conn_loco:
        cursor_loco = conn_loco.cursor()
        
        # NW: dealer_vehicle_type IN ('N', 'V')
        cursor_loco.execute("""
            SELECT COUNT(*) as stueck
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type IN ('N', 'V')
        """, (vj_von, vj_bis))
        row = cursor_loco.fetchone()
        drive_nw = int(row[0] or 0) if row else 0
        
        # GW: dealer_vehicle_type IN ('G', 'D')
        cursor_loco.execute("""
            SELECT COUNT(*) as stueck
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type IN ('G', 'D')
        """, (vj_von, vj_bis))
        row = cursor_loco.fetchone()
        drive_gw = int(row[0] or 0) if row else 0
        
        # GW nach Standort aufgeteilt
        cursor_loco.execute("""
            SELECT 
                out_subsidiary,
                COUNT(*) as stueck
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type IN ('G', 'D')
            GROUP BY out_subsidiary
            ORDER BY out_subsidiary
        """, (vj_von, vj_bis))
        rows = cursor_loco.fetchall()
        
        print(f"✅ DRIVE BWA Werte (Geschäftsjahr 2024/25, Sep 24 - Aug 25):")
        print(f"   NW Stück: {drive_nw}")
        print(f"   GW Stück: {drive_gw}")
        print()
        print("GW nach Standort (out_subsidiary):")
        for row in rows:
            subsidiary = row[0]
            stueck = row[1]
            standort_name = {1: "Stellantis (DEG+LAN)", 2: "Hyundai DEG", 3: "Unbekannt"}.get(subsidiary, f"Unbekannt ({subsidiary})")
            print(f"   {standort_name}: {stueck} Stk.")
        print()
        
        # Deggendorf (Standort 1) = Stellantis + Hyundai
        cursor_loco.execute("""
            SELECT COUNT(*) as stueck
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type IN ('G', 'D')
              AND (out_subsidiary = 1 OR out_subsidiary = 2)
        """, (vj_von, vj_bis))
        row = cursor_loco.fetchone()
        drive_gw_deggendorf = int(row[0] or 0) if row else 0
        
        print(f"GW Deggendorf (subsidiary 1+2): {drive_gw_deggendorf} Stk.")
        print()
    
    # Vergleich
    print("=" * 80)
    print("VERGLEICH:")
    print("=" * 80)
    
    # NW Stück
    diff_nw = drive_nw - globalcube['NW_stueck']
    diff_pct_nw = (diff_nw / globalcube['NW_stueck'] * 100) if globalcube['NW_stueck'] > 0 else 0
    print(f"NW Stück (Gesamt):")
    print(f"   Global Cube: {globalcube['NW_stueck']:.2f}")
    print(f"   DRIVE BWA:   {drive_nw:.2f}")
    print(f"   Differenz:   {diff_nw:+.2f} ({diff_pct_nw:+.2f}%)")
    if abs(diff_nw) > 5:
        print(f"   ⚠️  GROSSE ABWEICHUNG!")
    print()
    
    # GW Stück
    diff_gw = drive_gw - globalcube['GW_stueck']
    diff_pct_gw = (diff_gw / globalcube['GW_stueck'] * 100) if globalcube['GW_stueck'] > 0 else 0
    print(f"GW Stück (Gesamt):")
    print(f"   Global Cube: {globalcube['GW_stueck']:.2f}")
    print(f"   DRIVE BWA:   {drive_gw:.2f}")
    print(f"   Differenz:   {diff_gw:+.2f} ({diff_pct_gw:+.2f}%)")
    if abs(diff_gw) > 5:
        print(f"   ⚠️  GROSSE ABWEICHUNG!")
    print()
    
    print("=" * 80)
    print("ANALYSE:")
    print("=" * 80)
    print(f"Die CSV zeigt {globalcube['GW_stueck']:.2f} GW für das gesamte Unternehmen.")
    print(f"DRIVE zeigt {drive_gw} GW für das gesamte Unternehmen.")
    print()
    print(f"Für Deggendorf (Standort 1) zeigt DRIVE: {drive_gw_deggendorf} GW")
    print(f"Das sind {drive_gw_deggendorf / globalcube['GW_stueck'] * 100:.1f}% des Gesamtunternehmens.")
    print()
    print("⚠️  Wenn im Formular noch 29 Stk. angezeigt wird, dann wird")
    print("   möglicherweise der Monatswert statt des Jahreswerts angezeigt!")

if __name__ == '__main__':
    main()

