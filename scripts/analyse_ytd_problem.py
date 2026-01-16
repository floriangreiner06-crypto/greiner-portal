#!/usr/bin/env python3
"""
YTD Problem-Analyse
===================
TAG 196: Identifiziert die Ursache der YTD-Differenz
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

# YTD: Sep 2024 - Dez 2025
datum_von = '2024-09-01'
datum_bis = '2026-01-01'

firma_filter_kosten = "AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2)) OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1))"
guv_filter = "AND NOT ((nominal_account_number BETWEEN 890000 AND 899999 AND substr(CAST(nominal_account_number AS TEXT), 4, 1) = '9') OR (nominal_account_number BETWEEN 490000 AND 499999 AND substr(CAST(nominal_account_number AS TEXT), 4, 1) = '9'))"

print("="*80)
print("YTD PROBLEM-ANALYSE")
print("="*80)

with db_session() as conn:
    cursor = conn.cursor()
    
    # Indirekte Kosten YTD (aktuelle Logik)
    query_aktuell = f"""
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
            OR (nominal_account_number BETWEEN 489000 AND 489999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
          )
          AND NOT (
            nominal_account_number = 410021
            OR nominal_account_number BETWEEN 411000 AND 411999
            OR (nominal_account_number BETWEEN 489000 AND 489999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
          )
          {firma_filter_kosten}
          {guv_filter}
    """
    cursor.execute(convert_placeholders(query_aktuell), (datum_von, datum_bis))
    indirekte_aktuell = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Indirekte Kosten OHNE 498001
    query_ohne_498001 = f"""
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
            OR (nominal_account_number BETWEEN 498000 AND 499999
                AND NOT (nominal_account_number = 498001))
            OR (nominal_account_number BETWEEN 891000 AND 896999
                AND NOT (nominal_account_number BETWEEN 893200 AND 893299)
                AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
            OR (nominal_account_number BETWEEN 489000 AND 489999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
          )
          AND NOT (
            nominal_account_number = 410021
            OR nominal_account_number BETWEEN 411000 AND 411999
            OR (nominal_account_number BETWEEN 489000 AND 489999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
          )
          {firma_filter_kosten}
          {guv_filter}
    """
    cursor.execute(convert_placeholders(query_ohne_498001), (datum_von, datum_bis))
    indirekte_ohne_498001 = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # 498001 separat
    query_498001 = f"""
        SELECT 
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number = 498001
          {firma_filter_kosten}
          {guv_filter}
    """
    cursor.execute(convert_placeholders(query_498001), (datum_von, datum_bis))
    wert_498001 = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    print(f"\nIndirekte Kosten YTD (aktuell): {indirekte_aktuell:,.2f} €")
    print(f"Indirekte Kosten YTD (ohne 498001): {indirekte_ohne_498001:,.2f} €")
    print(f"498001 YTD: {wert_498001:,.2f} €")
    print(f"\nGlobalCube Referenz: 838.944,00 €")
    print(f"\nDifferenz aktuell: {indirekte_aktuell - 838944.00:,.2f} €")
    print(f"Differenz ohne 498001: {indirekte_ohne_498001 - 838944.00:,.2f} €")
    
    # Betriebsergebnis berechnen
    # Vereinfacht: DB3 - Indirekte
    # DB3 sollte ähnlich sein, nehmen wir an DB3 = 433.073,96 € (aus vorheriger Analyse)
    db3 = 433073.96
    be_aktuell = db3 - indirekte_aktuell
    be_ohne_498001 = db3 - indirekte_ohne_498001
    
    print(f"\n{'='*80}")
    print("BETRIEBSERGEBNIS YTD")
    print(f"{'='*80}")
    print(f"DB3 YTD: {db3:,.2f} €")
    print(f"Indirekte Kosten YTD (aktuell): {indirekte_aktuell:,.2f} €")
    print(f"Betriebsergebnis YTD (aktuell): {be_aktuell:,.2f} €")
    print(f"\nIndirekte Kosten YTD (ohne 498001): {indirekte_ohne_498001:,.2f} €")
    print(f"Betriebsergebnis YTD (ohne 498001): {be_ohne_498001:,.2f} €")
    print(f"\nGlobalCube Referenz: -245.733,00 €")
    print(f"\nDifferenz aktuell: {be_aktuell - (-245733.00):,.2f} €")
    print(f"Differenz ohne 498001: {be_ohne_498001 - (-245733.00):,.2f} €")
    
    print(f"\n{'='*80}")
    print("ERKENNTNIS")
    print(f"{'='*80}")
    print(f"498001 erhöht indirekte Kosten um {wert_498001:,.2f} € (als SOLL gebucht)")
    print(f"Wenn 498001 ausgeschlossen würde:")
    print(f"  Indirekte Kosten: {indirekte_ohne_498001:,.2f} €")
    print(f"  Betriebsergebnis: {be_ohne_498001:,.2f} €")
    print(f"  Differenz zu GlobalCube: {be_ohne_498001 - (-245733.00):,.2f} €")
