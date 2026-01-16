#!/usr/bin/env python3
"""
Detaillierte Clean Park Analyse
================================
TAG 196: Analysiert alle Clean Park Konten (847102 gefunden!)
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
firma_filter_umsatz = """AND (
    ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
    OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
    OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
)"""
firma_filter_einsatz = """AND (
    ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
    OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
    OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
)"""
guv_filter = "AND NOT ((nominal_account_number BETWEEN 890000 AND 899999 AND substr(CAST(nominal_account_number AS TEXT), 4, 1) = '9') OR (nominal_account_number BETWEEN 490000 AND 499999 AND substr(CAST(nominal_account_number AS TEXT), 4, 1) = '9'))"

print("="*80)
print("DETAILLIERTE CLEAN PARK ANALYSE")
print("="*80)
print(f"Zeitraum: {datum_von} bis {datum_bis}")
print()

with db_session() as conn:
    cursor = conn.cursor()
    
    # Alle 847xxx Konten (Clean Park Erlös)
    print("="*80)
    print("847XXX - CLEAN PARK ERLÖS")
    print("="*80)
    query = f"""
        SELECT 
            nominal_account_number as konto,
            SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as wert,
            COUNT(*) as anzahl,
            branch_number,
            subsidiary_to_company_ref
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 847000 AND 847999
          {firma_filter_umsatz}
          {guv_filter}
        GROUP BY nominal_account_number, branch_number, subsidiary_to_company_ref
        ORDER BY nominal_account_number, branch_number, subsidiary_to_company_ref
    """
    cursor.execute(convert_placeholders(query), (datum_von, datum_bis))
    rows = cursor.fetchall()
    total_erlos = 0
    for row in rows:
        r = row_to_dict(row)
        wert = float(r.get('wert', 0) or 0)
        total_erlos += wert
        if abs(wert) > 0:
            print(f"  {r['konto']}: {wert:,.2f} € ({r.get('anzahl', 0)} Buchungen, branch={r.get('branch_number', 'N/A')}, subsidiary={r.get('subsidiary_to_company_ref', 'N/A')})")
    print(f"Gesamt Erlös 847xxx: {total_erlos:,.2f} €")
    print()
    
    # Alle 747xxx Konten (Clean Park Einsatz)
    print("="*80)
    print("747XXX - CLEAN PARK EINSATZ")
    print("="*80)
    query = f"""
        SELECT 
            nominal_account_number as konto,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert,
            COUNT(*) as anzahl,
            branch_number,
            subsidiary_to_company_ref
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 747000 AND 747999
          AND nominal_account_number != 743002
          {firma_filter_einsatz}
          {guv_filter}
        GROUP BY nominal_account_number, branch_number, subsidiary_to_company_ref
        ORDER BY nominal_account_number, branch_number, subsidiary_to_company_ref
    """
    cursor.execute(convert_placeholders(query), (datum_von, datum_bis))
    rows = cursor.fetchall()
    total_einsatz = 0
    for row in rows:
        r = row_to_dict(row)
        wert = float(r.get('wert', 0) or 0)
        total_einsatz += wert
        if abs(wert) > 0:
            print(f"  {r['konto']}: {wert:,.2f} € ({r.get('anzahl', 0)} Buchungen, branch={r.get('branch_number', 'N/A')}, subsidiary={r.get('subsidiary_to_company_ref', 'N/A')})")
    print(f"Gesamt Einsatz 747xxx: {total_einsatz:,.2f} €")
    print()
    
    # Bruttoertrag
    bruttoertrag = total_erlos - total_einsatz
    print("="*80)
    print("ZUSAMMENFASSUNG")
    print("="*80)
    print(f"Erlös 847xxx: {total_erlos:,.2f} €")
    print(f"Einsatz 747xxx: {total_einsatz:,.2f} €")
    print(f"Bruttoertrag Clean Park: {bruttoertrag:,.2f} €")
    print()
    
    # Prüfe Kontobezeichnungen
    print("="*80)
    print("KONTOBEZEICHNUNGEN")
    print("="*80)
    for konto in [847102, 747102]:
        query_desc = """
            SELECT DISTINCT account_description
            FROM loco_nominal_accounts
            WHERE nominal_account_number = %s
            LIMIT 5
        """
        cursor.execute(convert_placeholders(query_desc), (konto,))
        rows = cursor.fetchall()
        for row in rows:
            r = row_to_dict(row)
            desc = r.get('account_description', 'N/A')
            if desc:
                print(f"  {konto}: {desc}")
