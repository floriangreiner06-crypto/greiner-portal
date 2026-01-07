#!/usr/bin/env python3
"""
Analysiert Diskrepanz zwischen Auslieferungsliste (sales) und FIBU (journal_accountings)
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.db_utils import db_session, locosoft_session, row_to_dict
import psycopg2.extras

def main():
    monat = 1  # Januar
    jahr = 2026
    von = f"{jahr}-{monat:02d}-01"
    bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"
    
    print(f"\n{'='*60}")
    print(f"ANALYSE: Auslieferungen vs. FIBU - {von} bis {bis}")
    print(f"{'='*60}\n")
    
    # 1. Auslieferungen aus sales (DRIVE Portal DB)
    print("[1] Auslieferungen aus sales (DRIVE Portal DB):")
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                dealer_vehicle_type,
                COUNT(*) as anzahl,
                SUM(out_sale_price) / 100.0 as umsatz
            FROM sales
            WHERE out_invoice_date >= %s
              AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
            GROUP BY dealer_vehicle_type
            ORDER BY dealer_vehicle_type
        """, (von, bis))
        rows = cursor.fetchall()
        gesamt_sales = 0
        for row in rows:
            r = row_to_dict(row)
            typ = r['dealer_vehicle_type']
            typ_name = {'N': 'NW', 'G': 'GW', 'V': 'Vorführ', 'D': 'Demo', 'T': 'Tausch'}.get(typ, typ)
            print(f"   {typ_name} ({typ}): {r['anzahl']} Stück, {r['umsatz'] or 0:,.2f} EUR")
            gesamt_sales += r['anzahl']
        print(f"   GESAMT: {gesamt_sales} Stück")
    
    # 2. Auslieferungen aus dealer_vehicles (Locosoft direkt)
    print(f"\n[2] Auslieferungen aus dealer_vehicles (Locosoft direkt):")
    with locosoft_session() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT 
                dealer_vehicle_type,
                COUNT(*) as anzahl,
                SUM(out_sale_price) / 100.0 as umsatz
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s
              AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND out_sale_price > 0
            GROUP BY dealer_vehicle_type
            ORDER BY dealer_vehicle_type
        """, (von, bis))
        rows = cur.fetchall()
        gesamt_dealer = 0
        for row in rows:
            typ = row['dealer_vehicle_type']
            typ_name = {'N': 'NW', 'G': 'GW', 'V': 'Vorführ', 'D': 'Demo', 'T': 'Tausch'}.get(typ, typ)
            print(f"   {typ_name} ({typ}): {row['anzahl']} Stück, {row['umsatz'] or 0:,.2f} EUR")
            gesamt_dealer += row['anzahl']
        print(f"   GESAMT: {gesamt_dealer} Stück")
    
    # 3. FIBU-Buchungen aus journal_accountings (Locosoft direkt)
    print(f"\n[3] FIBU-Buchungen aus journal_accountings (Locosoft direkt):")
    with locosoft_session() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # NW (810000-819999)
        cur.execute("""
            SELECT 
                COUNT(*) as anzahl_buchungen,
                COUNT(DISTINCT vehicle_reference) FILTER (WHERE vehicle_reference IS NOT NULL AND vehicle_reference != '') as stueck_mit_ref,
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
            FROM journal_accountings
            WHERE accounting_date >= %s
              AND accounting_date < %s
              AND nominal_account_number BETWEEN 810000 AND 819999
        """, (von, bis))
        row_nw = cur.fetchone()
        
        # GW (820000-829999)
        cur.execute("""
            SELECT 
                COUNT(*) as anzahl_buchungen,
                COUNT(DISTINCT vehicle_reference) FILTER (WHERE vehicle_reference IS NOT NULL AND vehicle_reference != '') as stueck_mit_ref,
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
            FROM journal_accountings
            WHERE accounting_date >= %s
              AND accounting_date < %s
              AND nominal_account_number BETWEEN 820000 AND 829999
        """, (von, bis))
        row_gw = cur.fetchone()
        
        print(f"   NW: {row_nw['anzahl_buchungen'] or 0} Buchungen, {row_nw['stueck_mit_ref'] or 0} Stück mit Ref, {row_nw['umsatz'] or 0:,.2f} EUR")
        print(f"   GW: {row_gw['anzahl_buchungen'] or 0} Buchungen, {row_gw['stueck_mit_ref'] or 0} Stück mit Ref, {row_gw['umsatz'] or 0:,.2f} EUR")
        print(f"   GESAMT: {(row_nw['anzahl_buchungen'] or 0) + (row_gw['anzahl_buchungen'] or 0)} Buchungen")
    
    # 4. Vergleich: sales vs. dealer_vehicles
    print(f"\n[4] Vergleich sales vs. dealer_vehicles:")
    print(f"   sales: {gesamt_sales} Stück")
    print(f"   dealer_vehicles: {gesamt_dealer} Stück")
    print(f"   Differenz: {gesamt_sales - gesamt_dealer} Stück")
    
    # 5. Detail: Welche Fahrzeuge sind in sales aber nicht in dealer_vehicles?
    print(f"\n[5] Detail-Analyse: VINs in sales vs. dealer_vehicles:")
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT vin, dealer_vehicle_type, out_invoice_date
            FROM sales
            WHERE out_invoice_date >= %s
              AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
            ORDER BY out_invoice_date
            LIMIT 20
        """, (von, bis))
        sales_vins = {row[0]: (row[1], row[2]) for row in cursor.fetchall() if row[0]}
    
    with locosoft_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT v.vin, dv.dealer_vehicle_type, dv.out_invoice_date
            FROM dealer_vehicles dv
            LEFT JOIN vehicles v ON v.dealer_vehicle_number = dv.dealer_vehicle_number
                                 AND v.dealer_vehicle_type = dv.dealer_vehicle_type
            WHERE dv.out_invoice_date >= %s
              AND dv.out_invoice_date < %s
              AND dv.out_invoice_date IS NOT NULL
            ORDER BY dv.out_invoice_date
            LIMIT 20
        """, (von, bis))
        dealer_vins = {row[0]: (row[1], row[2]) for row in cur.fetchall() if row[0]}
    
    nur_in_sales = set(sales_vins.keys()) - set(dealer_vins.keys())
    nur_in_dealer = set(dealer_vins.keys()) - set(sales_vins.keys())
    
    print(f"   VINs nur in sales: {len(nur_in_sales)}")
    if nur_in_sales:
        for vin in list(nur_in_sales)[:5]:
            typ, datum = sales_vins[vin]
            print(f"      {vin} ({typ}) - {datum}")
    
    print(f"   VINs nur in dealer_vehicles: {len(nur_in_dealer)}")
    if nur_in_dealer:
        for vin in list(nur_in_dealer)[:5]:
            typ, datum = dealer_vins[vin]
            print(f"      {vin} ({typ}) - {datum}")
    
    print(f"\n{'='*60}\n")

if __name__ == '__main__':
    main()

