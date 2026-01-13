#!/usr/bin/env python3
"""Debug: Prüfe Kosten-Zuordnung für Landau"""
import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session
from api.db_connection import convert_placeholders
import psycopg2.extras

with locosoft_session() as conn:
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print('=== KOSTEN-VERTEILUNG DEZEMBER 2025 (Stellantis) ===\n')
    
    # 1. Alle Kosten Stellantis
    cursor.execute(convert_placeholders('''
        SELECT 
            COUNT(*) as anzahl,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as summe
        FROM journal_accountings
        WHERE accounting_date >= '2025-12-01' AND accounting_date < '2026-01-01'
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND subsidiary_to_company_ref = 1
    '''))
    row = cursor.fetchone()
    print(f'Alle Kosten Stellantis: {row["anzahl"]} Buchungen, {row["summe"]:,.2f} €\n')
    
    # 2. Verteilung nach branch_number
    cursor.execute(convert_placeholders('''
        SELECT 
            branch_number,
            COUNT(*) as anzahl,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as summe
        FROM journal_accountings
        WHERE accounting_date >= '2025-12-01' AND accounting_date < '2026-01-01'
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND subsidiary_to_company_ref = 1
        GROUP BY branch_number
        ORDER BY branch_number NULLS LAST
    '''))
    print('Nach branch_number:')
    for r in cursor.fetchall():
        branch = r['branch_number'] if r['branch_number'] is not None else 'NULL'
        print(f'  branch_number {branch}: {r["anzahl"]} Buchungen, {r["summe"]:,.2f} €')
    print()
    
    # 3. Verteilung nach 6. Ziffer
    cursor.execute(convert_placeholders('''
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 6, 1) as ziffer_6,
            COUNT(*) as anzahl,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as summe
        FROM journal_accountings
        WHERE accounting_date >= '2025-12-01' AND accounting_date < '2026-01-01'
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND subsidiary_to_company_ref = 1
        GROUP BY substr(CAST(nominal_account_number AS TEXT), 6, 1)
        ORDER BY ziffer_6 NULLS LAST
    '''))
    print('Nach 6. Ziffer:')
    for r in cursor.fetchall():
        ziffer = r['ziffer_6'] if r['ziffer_6'] is not None else 'NULL'
        print(f'  6. Ziffer = {ziffer}: {r["anzahl"]} Buchungen, {r["summe"]:,.2f} €')
    print()
    
    # 4. Prüfe NULL branch_number
    cursor.execute(convert_placeholders('''
        SELECT 
            COUNT(*) FILTER (WHERE branch_number IS NOT NULL) as anzahl_mit_branch,
            COUNT(*) FILTER (WHERE branch_number IS NULL) as anzahl_ohne_branch,
            SUM(CASE WHEN debit_or_credit='S' AND branch_number IS NOT NULL THEN posted_value ELSE -posted_value END)/100.0 as summe_mit_branch,
            SUM(CASE WHEN debit_or_credit='S' AND branch_number IS NULL THEN posted_value ELSE -posted_value END)/100.0 as summe_ohne_branch
        FROM journal_accountings
        WHERE accounting_date >= '2025-12-01' AND accounting_date < '2026-01-01'
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND subsidiary_to_company_ref = 1
    '''))
    row = cursor.fetchone()
    print(f'Kosten mit branch_number: {row["anzahl_mit_branch"]} Buchungen, {row["summe_mit_branch"]:,.2f} €')
    print(f'Kosten OHNE branch_number (NULL): {row["anzahl_ohne_branch"]} Buchungen, {row["summe_ohne_branch"]:,.2f} €\n')
    
    # 5. Vergleich: branch_number=3 vs. 6. Ziffer=2
    cursor.execute(convert_placeholders('''
        SELECT 
            COUNT(*) FILTER (WHERE branch_number = 3) as anzahl_branch3,
            COUNT(*) FILTER (WHERE substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2') as anzahl_ziffer2,
            COUNT(*) FILTER (WHERE branch_number = 3 AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2') as anzahl_beide,
            SUM(CASE WHEN debit_or_credit='S' AND branch_number = 3 THEN posted_value ELSE -posted_value END)/100.0 as summe_branch3,
            SUM(CASE WHEN debit_or_credit='S' AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' THEN posted_value ELSE -posted_value END)/100.0 as summe_ziffer2,
            SUM(CASE WHEN debit_or_credit='S' AND branch_number = 3 AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' THEN posted_value ELSE -posted_value END)/100.0 as summe_beide
        FROM journal_accountings
        WHERE accounting_date >= '2025-12-01' AND accounting_date < '2026-01-01'
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND subsidiary_to_company_ref = 1
    '''))
    row = cursor.fetchone()
    print('=== VERGLEICH LANDAU-FILTER ===')
    print(f'branch_number = 3: {row["anzahl_branch3"]} Buchungen, {row["summe_branch3"]:,.2f} €')
    print(f'6. Ziffer = 2: {row["anzahl_ziffer2"]} Buchungen, {row["summe_ziffer2"]:,.2f} €')
    print(f'Beide (branch=3 AND ziffer=2): {row["anzahl_beide"]} Buchungen, {row["summe_beide"]:,.2f} €')
    print()
    
    # 6. Prüfe Deggendorf zum Vergleich
    cursor.execute(convert_placeholders('''
        SELECT 
            COUNT(*) FILTER (WHERE branch_number = 1) as anzahl_branch1,
            COUNT(*) FILTER (WHERE substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1') as anzahl_ziffer1,
            SUM(CASE WHEN debit_or_credit='S' AND branch_number = 1 THEN posted_value ELSE -posted_value END)/100.0 as summe_branch1,
            SUM(CASE WHEN debit_or_credit='S' AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' THEN posted_value ELSE -posted_value END)/100.0 as summe_ziffer1
        FROM journal_accountings
        WHERE accounting_date >= '2025-12-01' AND accounting_date < '2026-01-01'
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND subsidiary_to_company_ref = 1
    '''))
    row = cursor.fetchone()
    print('=== VERGLEICH DEGGENDORF-FILTER ===')
    print(f'branch_number = 1: {row["anzahl_branch1"]} Buchungen, {row["summe_branch1"]:,.2f} €')
    print(f'6. Ziffer = 1: {row["anzahl_ziffer1"]} Buchungen, {row["summe_ziffer1"]:,.2f} €')
