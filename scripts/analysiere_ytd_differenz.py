#!/usr/bin/env python3
"""
YTD-Differenz analysieren - TAG 188

Analysiert die YTD-Betriebsergebnis-Differenz:
- DRIVE: -391.157,71 €
- GlobalCube: -245.733,00 €
- Differenz: -145.424,71 €

Ziel: Identifiziere die Ursachen der Differenz.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

def analysiere_ytd_detailed():
    """Analysiert YTD-Berechnung detailliert."""
    print("="*80)
    print("YTD-DIFFERENZ-ANALYSE - TAG 188")
    print("="*80)
    
    # YTD-Zeitraum: 2025-09-01 bis 2026-01-01
    datum_von = "2025-09-01"
    datum_bis = "2026-01-01"
    
    print(f"\nZeitraum: {datum_von} bis {datum_bis}")
    print(f"\n{'='*80}")
    print("TEIL 1: YTD-BERECHNUNG (direkt)")
    print(f"{'='*80}\n")
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        # G&V-Filter
        from api.db_utils import get_guv_filter
        guv_filter = get_guv_filter()
        
        # 1. Umsatz YTD
        cursor.execute(convert_placeholders(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND (
                ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
                OR ((nominal_account_number BETWEEN 800000 AND 899999) AND NOT (nominal_account_number BETWEEN 893200 AND 893299) AND branch_number = 2 AND subsidiary_to_company_ref = 2)
              )
              {guv_filter}
        """), (datum_von, datum_bis))
        umsatz_ytd = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Umsatz YTD: {umsatz_ytd:,.2f} €")
        
        # 2. Einsatz YTD
        cursor.execute(convert_placeholders(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 700000 AND 799999
              AND nominal_account_number != 743002
              AND (
                (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2))
                OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1)
              )
              {guv_filter}
        """), (datum_von, datum_bis))
        einsatz_ytd = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Einsatz YTD: {einsatz_ytd:,.2f} €")
        
        db1_ytd = umsatz_ytd - einsatz_ytd
        print(f"DB1 YTD: {db1_ytd:,.2f} €")
        
        # 3. Variable Kosten YTD
        cursor.execute(convert_placeholders(f"""
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
        """), (datum_von, datum_bis))
        variable_ytd = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Variable Kosten YTD: {variable_ytd:,.2f} €")
        
        db2_ytd = db1_ytd - variable_ytd
        print(f"DB2 YTD: {db2_ytd:,.2f} €")
        
        # 4. Direkte Kosten YTD
        cursor.execute(convert_placeholders(f"""
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
              AND (
                (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2))
                OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1)
              )
              {guv_filter}
        """), (datum_von, datum_bis))
        direkte_ytd = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Direkte Kosten YTD: {direkte_ytd:,.2f} €")
        
        db3_ytd = db2_ytd - direkte_ytd
        print(f"DB3 YTD: {db3_ytd:,.2f} €")
        
        # 5. Indirekte Kosten YTD
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
                OR nominal_account_number = 498001
              )
              AND (
                (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2))
                OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1)
              )
              {guv_filter}
        """), (datum_von, datum_bis))
        indirekte_ytd = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Indirekte Kosten YTD: {indirekte_ytd:,.2f} €")
        
        be_ytd = db3_ytd - indirekte_ytd
        print(f"\n{'─'*80}")
        print(f"BETRIEBSERGEBNIS YTD: {be_ytd:,.2f} €")
        print(f"{'─'*80}")
        
        # Vergleich mit GlobalCube
        print(f"\nGlobalCube Referenz: -245.733,00 €")
        print(f"DRIVE berechnet: {be_ytd:,.2f} €")
        differenz = be_ytd - (-245.733)
        print(f"Differenz: {differenz:,.2f} €")
        
        # Summe der Monatswerte berechnen
        print(f"\n{'='*80}")
        print("TEIL 2: SUMME DER MONATSWERTE (Sep-Dez 2025)")
        print(f"{'='*80}\n")
        
        monatswerte = {
            'umsatz': 0,
            'einsatz': 0,
            'variable': 0,
            'direkte': 0,
            'indirekte': 0,
            'be': 0
        }
        
        for monat in [9, 10, 11, 12]:
            datum_von_monat = f"2025-{monat:02d}-01"
            if monat == 12:
                datum_bis_monat = "2026-01-01"
            else:
                datum_bis_monat = f"2025-{monat+1:02d}-01"
            
            # Umsatz Monat
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND ((nominal_account_number BETWEEN 800000 AND 889999)
                       OR (nominal_account_number BETWEEN 893200 AND 893299))
                  {guv_filter}
            """), (datum_von_monat, datum_bis_monat))
            umsatz_monat = float(row_to_dict(cursor.fetchone())['wert'] or 0)
            
            # Einsatz Monat
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 700000 AND 799999
                  AND nominal_account_number != 743002
                  {guv_filter}
            """), (datum_von_monat, datum_bis_monat))
            einsatz_monat = float(row_to_dict(cursor.fetchone())['wert'] or 0)
            
            # Variable Kosten Monat
            cursor.execute(convert_placeholders(f"""
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
            """), (datum_von_monat, datum_bis_monat))
            variable_monat = float(row_to_dict(cursor.fetchone())['wert'] or 0)
            
            # Direkte Kosten Monat
            cursor.execute(convert_placeholders(f"""
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
                  AND (
                    (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2))
                    OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1)
                  )
                  {guv_filter}
            """), (datum_von_monat, datum_bis_monat))
            direkte_monat = float(row_to_dict(cursor.fetchone())['wert'] or 0)
            
            # Indirekte Kosten Monat
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
                        AND NOT (nominal_account_number BETWEEN 893200 AND 893299)
                        AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
                  )
                  AND NOT (nominal_account_number = 498001)
                  AND (
                    (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2))
                    OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1)
                  )
                  {guv_filter}
            """), (datum_von_monat, datum_bis_monat))
            indirekte_monat = float(row_to_dict(cursor.fetchone())['wert'] or 0)
            
            db1_monat = umsatz_monat - einsatz_monat
            db2_monat = db1_monat - variable_monat
            db3_monat = db2_monat - direkte_monat
            be_monat = db3_monat - indirekte_monat
            
            print(f"Monat {monat}/2025:")
            print(f"  Umsatz: {umsatz_monat:,.2f} €")
            print(f"  Einsatz: {einsatz_monat:,.2f} €")
            print(f"  Variable: {variable_monat:,.2f} €")
            print(f"  Direkte: {direkte_monat:,.2f} €")
            print(f"  Indirekte: {indirekte_monat:,.2f} €")
            print(f"  BE: {be_monat:,.2f} €")
            print()
            
            monatswerte['umsatz'] += umsatz_monat
            monatswerte['einsatz'] += einsatz_monat
            monatswerte['variable'] += variable_monat
            monatswerte['direkte'] += direkte_monat
            monatswerte['indirekte'] += indirekte_monat
            monatswerte['be'] += be_monat
        
        print(f"{'─'*80}")
        print(f"SUMME MONATSWERTE (Sep-Dez):")
        print(f"  Umsatz: {monatswerte['umsatz']:,.2f} €")
        print(f"  Einsatz: {monatswerte['einsatz']:,.2f} €")
        print(f"  Variable: {monatswerte['variable']:,.2f} €")
        print(f"  Direkte: {monatswerte['direkte']:,.2f} €")
        print(f"  Indirekte: {monatswerte['indirekte']:,.2f} €")
        print(f"  BE: {monatswerte['be']:,.2f} €")
        print(f"{'─'*80}")
        
        # Vergleich YTD vs. Summe Monatswerte
        print(f"\n{'='*80}")
        print("TEIL 3: VERGLEICH YTD vs. SUMME MONATSWERTE")
        print(f"{'='*80}\n")
        
        print(f"Umsatz:")
        print(f"  YTD: {umsatz_ytd:,.2f} €")
        print(f"  Summe Monate: {monatswerte['umsatz']:,.2f} €")
        print(f"  Differenz: {umsatz_ytd - monatswerte['umsatz']:,.2f} €")
        print()
        
        print(f"Einsatz:")
        print(f"  YTD: {einsatz_ytd:,.2f} €")
        print(f"  Summe Monate: {monatswerte['einsatz']:,.2f} €")
        print(f"  Differenz: {einsatz_ytd - monatswerte['einsatz']:,.2f} €")
        print()
        
        print(f"Variable Kosten:")
        print(f"  YTD: {variable_ytd:,.2f} €")
        print(f"  Summe Monate: {monatswerte['variable']:,.2f} €")
        print(f"  Differenz: {variable_ytd - monatswerte['variable']:,.2f} €")
        print()
        
        print(f"Direkte Kosten:")
        print(f"  YTD: {direkte_ytd:,.2f} €")
        print(f"  Summe Monate: {monatswerte['direkte']:,.2f} €")
        print(f"  Differenz: {direkte_ytd - monatswerte['direkte']:,.2f} €")
        print()
        
        print(f"Indirekte Kosten:")
        print(f"  YTD: {indirekte_ytd:,.2f} €")
        print(f"  Summe Monate: {monatswerte['indirekte']:,.2f} €")
        print(f"  Differenz: {indirekte_ytd - monatswerte['indirekte']:,.2f} €")
        print()
        
        print(f"Betriebsergebnis:")
        print(f"  YTD: {be_ytd:,.2f} €")
        print(f"  Summe Monate: {monatswerte['be']:,.2f} €")
        print(f"  Differenz: {be_ytd - monatswerte['be']:,.2f} €")
        print()
        
        # Analyse der Umsatz-Differenz
        if abs(umsatz_ytd - monatswerte['umsatz']) > 100:
            print(f"\n{'='*80}")
            print("TEIL 4: UMLSATZ-DIFFERENZ ANALYSIEREN")
            print(f"{'='*80}\n")
            
            # Prüfe welche Konten in YTD aber nicht in Monatssumme sind
            cursor.execute(convert_placeholders(f"""
                SELECT 
                    nominal_account_number,
                    SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as summe
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND (
                    ((nominal_account_number BETWEEN 800000 AND 899999) AND NOT (nominal_account_number BETWEEN 893200 AND 893299) AND branch_number = 2 AND subsidiary_to_company_ref = 2)
                  )
                  {guv_filter}
                GROUP BY nominal_account_number
                HAVING ABS(SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0) > 100
                ORDER BY ABS(summe) DESC
                LIMIT 20
            """), (datum_von, datum_bis))
            
            print("Hyundai 89xxxx Konten (nur in YTD, nicht in Monatssumme):")
            for row in cursor.fetchall():
                r = row_to_dict(row)
                print(f"  Konto {r['nominal_account_number']}: {r['summe']:,.2f} €")


if __name__ == '__main__':
    analysiere_ytd_detailed()
