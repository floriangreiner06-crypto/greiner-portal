#!/usr/bin/env python3
"""
BWA YTD Analyse - Dezember 2025
===============================
TAG 196: Analysiert YTD-Werte bis Dezember 2025
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

# GlobalCube Referenzwerte (aus Dokumentation TAG 188)
GLOBALCUBE_YTD_DEZEMBER_2025 = {
    'direkte': 659229.00,
    'indirekte': 838944.00,
    'betriebsergebnis': -245733.00,
}


def format_currency(value):
    """Formatiert Betrag als Währung"""
    if value is None:
        return "N/A"
    return f"{value:,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.')


def main():
    """Hauptfunktion"""
    print("="*80)
    print("BWA YTD ANALYSE - BIS DEZEMBER 2025")
    print("TAG 196")
    print("="*80)
    
    # YTD: Wirtschaftsjahr Sep 2024 - Dez 2025
    jahr = 2025
    bis_monat = 12
    
    # Wirtschaftsjahr-Start: September
    WJ_START_MONAT = 9
    if bis_monat >= WJ_START_MONAT:
        datum_von = f"{jahr}-{WJ_START_MONAT:02d}-01"
    else:
        datum_von = f"{jahr-1}-{WJ_START_MONAT:02d}-01"
    
    datum_bis = f"{jahr+1}-01-01"  # Bis Ende Dezember 2025
    
    print(f"\nYTD-Zeitraum: {datum_von} bis {datum_bis}")
    print(f"Filter: Alle Firmen, Alle Standorte")
    
    # G&V-Filter
    guv_filter = """AND NOT (
        (nominal_account_number BETWEEN 890000 AND 899999 AND substr(CAST(nominal_account_number AS TEXT), 4, 1) = '9')
        OR (nominal_account_number BETWEEN 490000 AND 499999 AND substr(CAST(nominal_account_number AS TEXT), 4, 1) = '9')
    )"""
    
    # Gesamtsumme Filter
    firma_filter_umsatz = "AND ((branch_number = 1 AND subsidiary_to_company_ref = 1) OR (branch_number = 2 AND subsidiary_to_company_ref = 2) OR (branch_number = 3 AND subsidiary_to_company_ref = 1))"
    firma_filter_einsatz = """AND (
        ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
        OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
        OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
    )"""
    firma_filter_kosten = "AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2)) OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1))"
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        print(f"\n{'='*80}")
        print("YTD BWA WERTE (SEP 2024 - DEZ 2025)")
        print(f"{'='*80}")
        
        # Umsatz YTD
        umsatz_query = f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND ((nominal_account_number BETWEEN 800000 AND 889999)
                   OR (nominal_account_number BETWEEN 893200 AND 893299))
              {firma_filter_umsatz}
              {guv_filter}
        """
        cursor.execute(convert_placeholders(umsatz_query), (datum_von, datum_bis))
        umsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Umsatz YTD: {format_currency(umsatz)}")
        
        # Einsatz YTD
        einsatz_query = f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 700000 AND 799999
              AND nominal_account_number != 743002
              {firma_filter_einsatz}
              {guv_filter}
        """
        cursor.execute(convert_placeholders(einsatz_query), (datum_von, datum_bis))
        einsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Einsatz YTD: {format_currency(einsatz)}")
        
        db1 = umsatz - einsatz
        print(f"DB1 YTD: {format_currency(db1)}")
        
        # Variable Kosten YTD
        variable_query = f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND (
                nominal_account_number BETWEEN 415100 AND 415199
                OR nominal_account_number BETWEEN 435500 AND 435599
                OR (nominal_account_number BETWEEN 455000 AND 456999
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                OR (nominal_account_number BETWEEN 487000 AND 487099
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                OR nominal_account_number BETWEEN 491000 AND 497899
                OR nominal_account_number BETWEEN 891000 AND 891099
              )
              AND (
                (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 1)
                OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1)
                OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2 AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
              )
              {guv_filter}
        """
        cursor.execute(convert_placeholders(variable_query), (datum_von, datum_bis))
        variable = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Variable Kosten YTD: {format_currency(variable)}")
        
        db2 = db1 - variable
        print(f"DB2 YTD: {format_currency(db2)}")
        
        # Direkte Kosten YTD
        direkte_query = f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 400000 AND 489999
              AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
              AND NOT (
                nominal_account_number BETWEEN 415100 AND 415199
                OR nominal_account_number BETWEEN 424000 AND 424999
                OR nominal_account_number BETWEEN 435500 AND 435599
                OR nominal_account_number BETWEEN 438000 AND 438999
                OR nominal_account_number BETWEEN 455000 AND 456999
                OR nominal_account_number BETWEEN 487000 AND 487099
                OR nominal_account_number BETWEEN 489000 AND 489999
                OR nominal_account_number BETWEEN 491000 AND 497999
              )
              {firma_filter_kosten}
              {guv_filter}
        """
        cursor.execute(convert_placeholders(direkte_query), (datum_von, datum_bis))
        direkte = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Direkte Kosten YTD: {format_currency(direkte)}")
        print(f"GlobalCube Referenz: {format_currency(GLOBALCUBE_YTD_DEZEMBER_2025.get('direkte'))}")
        direkte_diff = direkte - GLOBALCUBE_YTD_DEZEMBER_2025.get('direkte', 0)
        print(f"Differenz: {format_currency(direkte_diff)}")
        
        db3 = db2 - direkte
        print(f"DB3 YTD: {format_currency(db3)}")
        
        # Indirekte Kosten YTD
        indirekte_query = f"""
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
        cursor.execute(convert_placeholders(indirekte_query), (datum_von, datum_bis))
        indirekte = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Indirekte Kosten YTD: {format_currency(indirekte)}")
        print(f"GlobalCube Referenz: {format_currency(GLOBALCUBE_YTD_DEZEMBER_2025.get('indirekte'))}")
        indirekte_diff = indirekte - GLOBALCUBE_YTD_DEZEMBER_2025.get('indirekte', 0)
        print(f"Differenz: {format_currency(indirekte_diff)}")
        
        be = db3 - indirekte
        print(f"\nBetriebsergebnis YTD: {format_currency(be)}")
        print(f"GlobalCube Referenz: {format_currency(GLOBALCUBE_YTD_DEZEMBER_2025.get('betriebsergebnis'))}")
        be_diff = be - GLOBALCUBE_YTD_DEZEMBER_2025.get('betriebsergebnis', 0)
        print(f"Differenz: {format_currency(be_diff)}")
        
        # 498001 YTD prüfen
        print(f"\n{'='*80}")
        print("498001 YTD PRÜFUNG")
        print(f"{'='*80}")
        
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
        
        total_498001 = 0
        for r in rows:
            rd = row_to_dict(r)
            wert = float(rd['wert'] or 0)
            total_498001 += wert
            print(f"  {rd['debit_or_credit']}: {format_currency(wert)} ({rd['anzahl']} Buchungen)")
        
        print(f"\n498001 YTD Gesamt: {format_currency(total_498001)}")
        print(f"Erwartung (4 Monate × 50.000 €): {format_currency(4 * 50000)}")
        
        print(f"\n{'='*80}")
        print("ANALYSE ABGESCHLOSSEN")
        print(f"{'='*80}")


if __name__ == '__main__':
    main()
