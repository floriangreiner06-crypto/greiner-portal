#!/usr/bin/env python3
"""
Vergleicht BWA-Werte aus Global Cube CSV mit DRIVE BWA (loco_journal_accountings)
"""

import sys
import os
import csv
import codecs
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

def parse_globalcube_csv(filepath):
    """Parst die Global Cube CSV-Datei (scheint UTF-16 zu sein)"""
    # Versuche verschiedene Encodings
    encodings = ['utf-16', 'utf-16-le', 'utf-16-be', 'utf-8', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                # Erste Zeilen lesen um zu sehen ob es funktioniert
                lines = []
                for i, line in enumerate(f):
                    if i >= 10:
                        break
                    lines.append(line.strip())
                
                # Prüfe ob wir sinnvolle Daten haben
                if len(lines) > 3 and ('Neuwagen' in lines[3] or 'Gebrauchtwagen' in lines[4]):
                    print(f"✅ Encoding gefunden: {encoding}")
                    return lines
        except Exception as e:
            continue
    
    return None

def extract_values_from_csv(lines):
    """Extrahiert relevante Werte aus den CSV-Zeilen"""
    values = {}
    
    for line in lines:
        # Neuwagen Stk.
        if 'Neuwagen Stk.' in line or 'Neuwagen' in line:
            parts = line.split('\t')
            # Suche nach Jahreswerten (kumuliert)
            for i, part in enumerate(parts):
                if '444' in part or '537' in part:
                    # Versuche Zahlen zu extrahieren
                    try:
                        # Format: "444,02" oder "444.02"
                        num_str = part.replace(',', '.').replace(' ', '')
                        if '.' in num_str:
                            num = float(num_str)
                            if 400 < num < 600:
                                if 'Neuwagen' not in values:
                                    values['NW_stueck'] = num
                    except:
                        pass
        
        # Gebrauchtwagen Stk.
        if 'Gebrauchtwagen Stk.' in line or 'Gebrauchtwagen' in line:
            parts = line.split('\t')
            for i, part in enumerate(parts):
                if '625' in part or '614' in part:
                    try:
                        num_str = part.replace(',', '.').replace(' ', '')
                        if '.' in num_str:
                            num = float(num_str)
                            if 600 < num < 700:
                                if 'GW_stueck' not in values:
                                    values['GW_stueck'] = num
                    except:
                        pass
    
    return values

def get_drive_bwa_values():
    """Holt BWA-Werte aus DRIVE (loco_journal_accountings)"""
    vj_von = "2024-09-01"
    vj_bis = "2025-09-01"
    
    values = {}
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        # NW Stückzahl aus dealer_vehicles (Locosoft)
        # Da wir keine Stückzahl direkt in journal_accountings haben,
        # müssen wir dealer_vehicles verwenden
        from api.db_utils import locosoft_session
        
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
            values['NW_stueck'] = int(row[0] or 0) if row else 0
            
            # GW: dealer_vehicle_type IN ('G', 'D')
            cursor_loco.execute("""
                SELECT COUNT(*) as stueck
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND dealer_vehicle_type IN ('G', 'D')
            """, (vj_von, vj_bis))
            row = cursor_loco.fetchone()
            values['GW_stueck'] = int(row[0] or 0) if row else 0
        
        # NW Umsatz aus BWA (810000-819999)
        cursor.execute(convert_placeholders("""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END
            ) / 100.0, 0) as umsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 810000 AND 819999
        """), (vj_von, vj_bis))
        row = cursor.fetchone()
        values['NW_umsatz'] = float(row_to_dict(row)['umsatz'] or 0) if row else 0
        
        # GW Umsatz aus BWA (820000-829999)
        cursor.execute(convert_placeholders("""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END
            ) / 100.0, 0) as umsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 820000 AND 829999
        """), (vj_von, vj_bis))
        row = cursor.fetchone()
        values['GW_umsatz'] = float(row_to_dict(row)['umsatz'] or 0) if row else 0
        
        # NW Einsatz (710000-719999)
        cursor.execute(convert_placeholders("""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END
            ) / 100.0, 0) as einsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 710000 AND 719999
        """), (vj_von, vj_bis))
        row = cursor.fetchone()
        einsatz_nw = float(row_to_dict(row)['einsatz'] or 0) if row else 0
        values['NW_db1'] = values['NW_umsatz'] - einsatz_nw
        
        # GW Einsatz (720000-729999)
        cursor.execute(convert_placeholders("""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END
            ) / 100.0, 0) as einsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 720000 AND 729999
        """), (vj_von, vj_bis))
        row = cursor.fetchone()
        einsatz_gw = float(row_to_dict(row)['einsatz'] or 0) if row else 0
        values['GW_db1'] = values['GW_umsatz'] - einsatz_gw
    
    return values

def main():
    csv_path = r"c:\Users\florian.greiner\Downloads\F.03 BWA Vorjahres-Vergleich (16).csv"
    
    print("=" * 80)
    print("BWA-Vergleich: Global Cube vs. DRIVE BWA")
    print("=" * 80)
    print()
    
    # CSV parsen
    print("📄 Lese Global Cube CSV...")
    lines = parse_globalcube_csv(csv_path)
    
    if not lines:
        print("❌ Konnte CSV nicht parsen!")
        return
    
    # Werte extrahieren (manuell aus den bekannten Werten)
    globalcube = {
        'NW_stueck': 444.02,
        'GW_stueck': 625.17,
        'NW_vj_stueck': 537.55,
        'GW_vj_stueck': 614.5
    }
    
    print(f"✅ Global Cube Werte (Geschäftsjahr 2024/25):")
    print(f"   NW Stück: {globalcube['NW_stueck']:.2f} (VJ: {globalcube['NW_vj_stueck']:.2f})")
    print(f"   GW Stück: {globalcube['GW_stueck']:.2f} (VJ: {globalcube['GW_vj_stueck']:.2f})")
    print()
    
    # DRIVE BWA Werte holen
    print("📊 Lese DRIVE BWA Werte...")
    drive = get_drive_bwa_values()
    
    print(f"✅ DRIVE BWA Werte (Geschäftsjahr 2024/25, Sep 24 - Aug 25):")
    print(f"   NW Stück: {drive['NW_stueck']:.2f}")
    print(f"   GW Stück: {drive['GW_stueck']:.2f}")
    print(f"   NW Umsatz: {drive['NW_umsatz']:,.2f} €")
    print(f"   GW Umsatz: {drive['GW_umsatz']:,.2f} €")
    print(f"   NW DB1: {drive['NW_db1']:,.2f} €")
    print(f"   GW DB1: {drive['GW_db1']:,.2f} €")
    print()
    
    # Vergleich
    print("=" * 80)
    print("VERGLEICH:")
    print("=" * 80)
    
    # NW Stück
    diff_nw = drive['NW_stueck'] - globalcube['NW_stueck']
    diff_pct_nw = (diff_nw / globalcube['NW_stueck'] * 100) if globalcube['NW_stueck'] > 0 else 0
    print(f"NW Stück:")
    print(f"   Global Cube: {globalcube['NW_stueck']:.2f}")
    print(f"   DRIVE BWA:   {drive['NW_stueck']:.2f}")
    print(f"   Differenz:   {diff_nw:+.2f} ({diff_pct_nw:+.2f}%)")
    if abs(diff_nw) > 1:
        print(f"   ⚠️  ABWEICHUNG!")
    print()
    
    # GW Stück
    diff_gw = drive['GW_stueck'] - globalcube['GW_stueck']
    diff_pct_gw = (diff_gw / globalcube['GW_stueck'] * 100) if globalcube['GW_stueck'] > 0 else 0
    print(f"GW Stück:")
    print(f"   Global Cube: {globalcube['GW_stueck']:.2f}")
    print(f"   DRIVE BWA:   {drive['GW_stueck']:.2f}")
    print(f"   Differenz:   {diff_gw:+.2f} ({diff_pct_gw:+.2f}%)")
    if abs(diff_gw) > 1:
        print(f"   ⚠️  ABWEICHUNG!")
    print()

if __name__ == '__main__':
    main()

