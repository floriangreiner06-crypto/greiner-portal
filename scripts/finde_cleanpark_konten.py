#!/usr/bin/env python3
"""
Finde Clean Park Konten
=======================
TAG 196: Findet welche Konten für Clean Park verwendet werden sollten
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

# Dezember 2025
datum_von = '2025-12-01'
datum_bis = '2026-01-01'

# Gesamtsumme Filter (firma=0, standort=0)
firma_filter = """AND (
    ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
    OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
    OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
)"""
guv_filter = "AND NOT ((nominal_account_number BETWEEN 890000 AND 899999 AND substr(CAST(nominal_account_number AS TEXT), 4, 1) = '9') OR (nominal_account_number BETWEEN 490000 AND 499999 AND substr(CAST(nominal_account_number AS TEXT), 4, 1) = '9'))"

print("="*80)
print("FINDE CLEAN PARK KONTEN")
print("="*80)
print(f"Zeitraum: {datum_von} bis {datum_bis}")
print()
print("Suche nach möglichen Clean Park Konten in verschiedenen Bereichen...")
print()

with db_session() as conn:
    cursor = conn.cursor()
    
    # Prüfe verschiedene mögliche Bereiche
    bereiche = [
        ("86xxxx (Sonstige Erlöse)", 860000, 869999, "H"),
        ("76xxxx (Sonstiger Einsatz)", 760000, 769999, "S"),
        ("85xxxx (Lack/Sonstige)", 850000, 859999, "H"),
        ("75xxxx (Sonstiger Einsatz)", 750000, 759999, "S"),
        ("88xxxx (Vermietung)", 880000, 889999, "H"),
        ("84xxxx (Lohn - könnte CP enthalten)", 840000, 849999, "H"),
        ("74xxxx (Lohn Einsatz - könnte CP enthalten)", 740000, 749999, "S"),
    ]
    
    for bezeichnung, von, bis, debit_credit in bereiche:
        if debit_credit == "H":
            case_expr = "CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END"
        else:
            case_expr = "CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END"
        
        query = f"""
            SELECT 
                nominal_account_number as konto,
                SUM({case_expr})/100.0 as wert,
                COUNT(*) as anzahl
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN {von} AND {bis}
              AND nominal_account_number != 743002
              {firma_filter}
              {guv_filter}
            GROUP BY nominal_account_number
            HAVING ABS(SUM({case_expr})) > 1000
            ORDER BY ABS(SUM({case_expr})) DESC
            LIMIT 20
        """
        
        cursor.execute(convert_placeholders(query), (datum_von, datum_bis))
        rows = cursor.fetchall()
        
        if rows:
            print(f"={bezeichnung}=")
            total = 0
            for row in rows:
                r = row_to_dict(row)
                wert = float(r.get('wert', 0) or 0)
                total += wert
                print(f"  {r['konto']}: {wert:,.2f} € ({r.get('anzahl', 0)} Buchungen)")
            print(f"  Gesamt (>1000€): {total:,.2f} €")
            print()
    
    # Prüfe spezifisch nach Konten mit "clean", "park", "cp" in der Beschreibung
    print("="*80)
    print("SUCHE NACH KONTEN MIT 'CLEAN', 'PARK', 'CP' IN BESCHREIBUNG")
    print("="*80)
    
    query_desc = """
        SELECT DISTINCT
            nominal_account_number,
            account_description
        FROM loco_nominal_accounts
        WHERE LOWER(account_description) LIKE '%clean%'
           OR LOWER(account_description) LIKE '%park%'
           OR LOWER(account_description) LIKE '%cp%'
        ORDER BY nominal_account_number
        LIMIT 50
    """
    
    cursor.execute(convert_placeholders(query_desc))
    rows = cursor.fetchall()
    
    if rows:
        for row in rows:
            r = row_to_dict(row)
            print(f"  {r['nominal_account_number']}: {r.get('account_description', 'N/A')}")
    else:
        print("  Keine Konten mit 'clean', 'park', 'cp' in Beschreibung gefunden.")
    print()
    
    # Prüfe Konten mit 6. Ziffer = '6' (KST 60 = Clean Park)
    print("="*80)
    print("KONTEN MIT 6. ZIFFER = '6' (MÖGLICHE KST 60 = CLEAN PARK)")
    print("="*80)
    
    for prefix in [81, 82, 83, 84, 85, 86, 87, 88]:
        query_kst6 = f"""
            SELECT 
                nominal_account_number as konto,
                SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as wert,
                COUNT(*) as anzahl
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN {prefix}0000 AND {prefix}9999
              AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '6'
              {firma_filter}
              {guv_filter}
            GROUP BY nominal_account_number
            HAVING ABS(SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)) > 100
            ORDER BY ABS(SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)) DESC
            LIMIT 10
        """
        cursor.execute(convert_placeholders(query_kst6), (datum_von, datum_bis))
        rows = cursor.fetchall()
        if rows:
            print(f"{prefix}xxxx mit 6. Ziffer='6':")
            for row in rows:
                r = row_to_dict(row)
                print(f"  {r['konto']}: {float(r.get('wert', 0) or 0):,.2f} € ({r.get('anzahl', 0)} Buchungen)")
            print()
