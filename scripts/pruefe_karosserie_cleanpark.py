#!/usr/bin/env python3
"""
Prüfe Karosserie und Clean Park Konten
======================================
TAG 196: Prüft welche Konten für Karosserie und Clean Park verwendet werden sollten
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
print("PRÜFE KAROSSERIE UND CLEAN PARK KONTEN")
print("="*80)
print(f"Zeitraum: {datum_von} bis {datum_bis}")
print()

with db_session() as conn:
    cursor = conn.cursor()
    
    # Prüfe 8405xx (Karosserie Erlös)
    print("="*80)
    print("8405XX - KAROSSERIE ERLÖS")
    print("="*80)
    query = f"""
        SELECT 
            nominal_account_number as konto,
            SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as wert,
            COUNT(*) as anzahl
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 840500 AND 840599
          {firma_filter}
          {guv_filter}
        GROUP BY nominal_account_number
        ORDER BY nominal_account_number
    """
    cursor.execute(convert_placeholders(query), (datum_von, datum_bis))
    rows = cursor.fetchall()
    total = 0
    for row in rows:
        r = row_to_dict(row)
        wert = float(r.get('wert', 0) or 0)
        total += wert
        if abs(wert) > 0:
            print(f"  {r['konto']}: {wert:,.2f} € ({r.get('anzahl', 0)} Buchungen)")
    print(f"Gesamt: {total:,.2f} €")
    print()
    
    # Prüfe 745xxx (Karosserie Einsatz)
    print("="*80)
    print("745XXX - KAROSSERIE EINSATZ")
    print("="*80)
    query = f"""
        SELECT 
            nominal_account_number as konto,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert,
            COUNT(*) as anzahl
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 745000 AND 745999
          AND nominal_account_number != 743002
          {firma_filter}
          {guv_filter}
        GROUP BY nominal_account_number
        ORDER BY nominal_account_number
    """
    cursor.execute(convert_placeholders(query), (datum_von, datum_bis))
    rows = cursor.fetchall()
    total = 0
    for row in rows:
        r = row_to_dict(row)
        wert = float(r.get('wert', 0) or 0)
        total += wert
        if abs(wert) > 0:
            print(f"  {r['konto']}: {wert:,.2f} € ({r.get('anzahl', 0)} Buchungen)")
    print(f"Gesamt: {total:,.2f} €")
    print()
    
    # Prüfe 87xxxx (Clean Park Erlös)
    print("="*80)
    print("87XXXX - CLEAN PARK ERLÖS")
    print("="*80)
    query = f"""
        SELECT 
            nominal_account_number as konto,
            SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as wert,
            COUNT(*) as anzahl
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 870000 AND 879999
          {firma_filter}
          {guv_filter}
        GROUP BY nominal_account_number
        ORDER BY nominal_account_number
    """
    cursor.execute(convert_placeholders(query), (datum_von, datum_bis))
    rows = cursor.fetchall()
    total = 0
    for row in rows:
        r = row_to_dict(row)
        wert = float(r.get('wert', 0) or 0)
        total += wert
        if abs(wert) > 0:
            print(f"  {r['konto']}: {wert:,.2f} € ({r.get('anzahl', 0)} Buchungen)")
    print(f"Gesamt: {total:,.2f} €")
    print()
    
    # Prüfe 77xxxx (Clean Park Einsatz)
    print("="*80)
    print("77XXXX - CLEAN PARK EINSATZ")
    print("="*80)
    query = f"""
        SELECT 
            nominal_account_number as konto,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert,
            COUNT(*) as anzahl
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 770000 AND 779999
          AND nominal_account_number != 743002
          {firma_filter}
          {guv_filter}
        GROUP BY nominal_account_number
        ORDER BY nominal_account_number
    """
    cursor.execute(convert_placeholders(query), (datum_von, datum_bis))
    rows = cursor.fetchall()
    total = 0
    for row in rows:
        r = row_to_dict(row)
        wert = float(r.get('wert', 0) or 0)
        total += wert
        if abs(wert) > 0:
            print(f"  {r['konto']}: {wert:,.2f} € ({r.get('anzahl', 0)} Buchungen)")
    print(f"Gesamt: {total:,.2f} €")
