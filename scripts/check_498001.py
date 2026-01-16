#!/usr/bin/env python3
"""Prüft 498001 in indirekten Kosten"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

datum_von = '2025-12-01'
datum_bis = '2026-01-01'
firma_filter_kosten = "AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2)) OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1))"
guv_filter = "AND NOT ((nominal_account_number BETWEEN 890000 AND 899999 AND substr(CAST(nominal_account_number AS TEXT), 4, 1) = '9') OR (nominal_account_number BETWEEN 490000 AND 499999 AND substr(CAST(nominal_account_number AS TEXT), 4, 1) = '9'))"

with db_session() as conn:
    cursor = conn.cursor()
    
    # Indirekte Kosten gesamt
    query_gesamt = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND (
            (nominal_account_number BETWEEN 400000 AND 499999
             AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
            OR (nominal_account_number BETWEEN 424000 AND 424999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR (nominal_account_number BETWEEN 438000 AND 438999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR nominal_account_number BETWEEN 498000 AND 499999
            OR (nominal_account_number BETWEEN 891000 AND 896999
                AND NOT (nominal_account_number BETWEEN 893200 AND 893299)
                AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
          )
          {firma_filter_kosten}
          {guv_filter}
    """
    cursor.execute(convert_placeholders(query_gesamt), (datum_von, datum_bis))
    row = cursor.fetchone()
    indirekte_gesamt = float(row_to_dict(row)['wert'] or 0)
    
    # 498001 separat
    query_498001 = f"""
        SELECT 
            debit_or_credit,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert,
            COUNT(*) as anzahl
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number = 498001
          {firma_filter_kosten}
          {guv_filter}
        GROUP BY debit_or_credit
    """
    cursor.execute(convert_placeholders(query_498001), (datum_von, datum_bis))
    rows = cursor.fetchall()
    
    print(f'Indirekte Kosten gesamt: {indirekte_gesamt:,.2f} €')
    print(f'\n498001 Details:')
    total_498001 = 0
    for r in rows:
        rd = row_to_dict(r)
        wert = float(rd['wert'] or 0)
        total_498001 += wert
        print(f'  {rd["debit_or_credit"]}: {wert:,.2f} € ({rd["anzahl"]} Buchungen)')
    
    print(f'\n498001 Gesamt: {total_498001:,.2f} €')
    print(f'\nErwartung:')
    print(f'  Indirekte Kosten OHNE 498001: {indirekte_gesamt - total_498001:,.2f} €')
    print(f'  Indirekte Kosten MIT 498001: {indirekte_gesamt:,.2f} €')
    print(f'  (498001 reduziert Kosten um {abs(total_498001):,.2f} € wenn als HABEN gebucht)')
