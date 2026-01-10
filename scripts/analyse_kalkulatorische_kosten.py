#!/usr/bin/env python3
"""
Prüft kalkulatorische Kosten (29xxxx) in indirekten Kosten
===========================================================
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

datum_von = "2024-09-01"
datum_bis = "2025-09-01"

firma_filter_kosten = ''
guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"

print("=" * 100)
print("ANALYSE: Kalkulatorische Kosten (29xxxx) in indirekten Kosten")
print("=" * 100)
print(f"Zeitraum: {datum_von} - {datum_bis}\n")

with db_session() as conn:
    cursor = conn.cursor()
    
    # Kalkulatorische Kosten (29xxxx)
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 290000 AND 299999
          {firma_filter_kosten}
          {guv_filter}
    """), (datum_von, datum_bis))
    kalk = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    print(f"Kalkulatorische Kosten (29xxxx): {kalk:>15,.2f} €")
    
    # Indirekte Kosten OHNE kalkulatorische Kosten
    cursor.execute(convert_placeholders(f"""
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
                AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
          )
          AND NOT (nominal_account_number BETWEEN 290000 AND 299999)
          {firma_filter_kosten}
          {guv_filter}
    """), (datum_von, datum_bis))
    indirekte_ohne_kalk = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    print(f"Indirekte Kosten (ohne 29xxxx):   {indirekte_ohne_kalk:>15,.2f} €")
    
    # Indirekte Kosten MIT kalkulatorischen Kosten (aktuell)
    cursor.execute(convert_placeholders(f"""
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
                AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
          )
          {firma_filter_kosten}
          {guv_filter}
    """), (datum_von, datum_bis))
    indirekte_mit_kalk = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    print(f"Indirekte Kosten (mit 29xxxx):    {indirekte_mit_kalk:>15,.2f} €")
    
    print(f"\nGlobalcube Indirekte Kosten:     2,479,617.08 €")
    print(f"\nVergleich:")
    print(f"  Ohne 29xxxx: {indirekte_ohne_kalk:>15,.2f} € (Diff: {indirekte_ohne_kalk - 2479617.08:>15,.2f} €)")
    print(f"  Mit 29xxxx:  {indirekte_mit_kalk:>15,.2f} € (Diff: {indirekte_mit_kalk - 2479617.08:>15,.2f} €)")
