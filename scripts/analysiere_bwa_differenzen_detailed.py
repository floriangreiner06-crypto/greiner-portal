#!/usr/bin/env python3
"""
Detaillierte BWA-Differenz-Analyse - TAG 188

Analysiert alle verbleibenden Differenzen zwischen DRIVE und GlobalCube:
1. Monat Dezember 2025: 100,63 € Differenz
2. YTD bis Dezember 2025: 86.481,12 € Differenz (nach 498001-Korrektur)

Ziel: Identifiziere alle Ursachen der Differenzen.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

def analysiere_monat_differenz():
    """Analysiert die Monats-Differenz von 100,63 €."""
    print("="*80)
    print("MONAT DEZEMBER 2025 - DIFFERENZ-ANALYSE")
    print("="*80)
    
    datum_von = "2025-12-01"
    datum_bis = "2026-01-01"
    
    print(f"\nZeitraum: {datum_von} bis {datum_bis}")
    print(f"GlobalCube BE: -116.248,00 €")
    print(f"DRIVE BE: -116.147,37 €")
    print(f"Differenz: 100,63 €")
    print()
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        from api.db_utils import get_guv_filter
        guv_filter = get_guv_filter()
        
        # Alle Positionen einzeln berechnen
        print("Positionen-Detail:")
        print("-"*80)
        
        # Umsatz
        cursor.execute(convert_placeholders(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND ((nominal_account_number BETWEEN 800000 AND 889999)
                   OR (nominal_account_number BETWEEN 893200 AND 893299))
              {guv_filter}
        """), (datum_von, datum_bis))
        umsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Umsatz: {umsatz:,.2f} €")
        
        # Einsatz
        cursor.execute(convert_placeholders(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 700000 AND 799999
              AND nominal_account_number != 743002
              {guv_filter}
        """), (datum_von, datum_bis))
        einsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Einsatz: {einsatz:,.2f} €")
        
        db1 = umsatz - einsatz
        print(f"DB1: {db1:,.2f} €")
        
        # Variable Kosten
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
        variable = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Variable Kosten: {variable:,.2f} €")
        
        db2 = db1 - variable
        print(f"DB2: {db2:,.2f} €")
        
        # Direkte Kosten
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
        direkte = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Direkte Kosten: {direkte:,.2f} €")
        
        db3 = db2 - direkte
        print(f"DB3: {db3:,.2f} €")
        
        # Indirekte Kosten
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
        """), (datum_von, datum_bis))
        indirekte = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Indirekte Kosten: {indirekte:,.2f} €")
        
        be = db3 - indirekte
        print(f"\n{'='*80}")
        print(f"BETRIEBSERGEBNIS: {be:,.2f} €")
        print(f"GlobalCube: -116.248,00 €")
        print(f"Differenz: {be - (-116.248):,.2f} €")
        print(f"{'='*80}")
        
        # Prüfe ob es weitere Konten gibt, die ausgeschlossen werden sollten
        print(f"\n{'='*80}")
        print("ANALYSE: Weitere Konten die möglicherweise ausgeschlossen werden sollten")
        print(f"{'='*80}\n")
        
        # Prüfe alle Kosten-Konten die nicht kategorisiert sind
        cursor.execute(convert_placeholders(f"""
            SELECT 
                nominal_account_number,
                COUNT(*) as anzahl,
                SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as summe
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 400000 AND 499999
              AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
              AND (
                (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2))
                OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1)
              )
            GROUP BY nominal_account_number
            HAVING ABS(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0) > 50
            ORDER BY ABS(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0) DESC
            LIMIT 100
        """), (datum_von, datum_bis))
        
        print("Top 100 Kosten-Konten (alle):")
        konten_liste = []
        for row in cursor.fetchall():
            r = row_to_dict(row)
            konten_liste.append((r['nominal_account_number'], r['summe'], r['anzahl']))
            if abs(r['summe']) > 100:
                print(f"  Konto {r['nominal_account_number']}: {r['summe']:,.2f} € ({r['anzahl']} Buchungen)")
        
        return be, indirekte, konten_liste


def analysiere_ytd_differenz():
    """Analysiert die YTD-Differenz von 86.481,12 €."""
    print(f"\n\n{'='*80}")
    print("YTD BIS DEZEMBER 2025 - DIFFERENZ-ANALYSE")
    print("="*80)
    
    datum_von = "2025-09-01"
    datum_bis = "2026-01-01"
    
    print(f"\nZeitraum: {datum_von} bis {datum_bis}")
    print(f"GlobalCube BE: -245.733,00 €")
    print(f"DRIVE BE (korrigiert): -159.251,88 €")
    print(f"Differenz: 86.481,12 €")
    print()
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        from api.db_utils import get_guv_filter
        guv_filter = get_guv_filter()
        
        # Alle Positionen einzeln berechnen
        print("Positionen-Detail:")
        print("-"*80)
        
        # Umsatz YTD
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
        
        # Einsatz YTD
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
        
        # Variable Kosten YTD
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
        
        # Direkte Kosten YTD
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
        
        # Indirekte Kosten YTD
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
        print(f"\n{'='*80}")
        print(f"BETRIEBSERGEBNIS YTD: {be_ytd:,.2f} €")
        print(f"GlobalCube: -245.733,00 €")
        print(f"Differenz: {be_ytd - (-245.733):,.2f} €")
        print(f"{'='*80}")
        
        # Vergleich mit Summe Monatswerte
        print(f"\n{'='*80}")
        print("VERGLEICH: YTD vs. Summe Monatswerte")
        print(f"{'='*80}\n")
        
        monatswerte_summe = {
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
            
            # Vereinfachte Berechnung für Monatssumme
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as umsatz,
                COALESCE(SUM(CASE WHEN nominal_account_number BETWEEN 700000 AND 799999 AND nominal_account_number != 743002 AND debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0, 0) as einsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
                  {guv_filter}
            """), (datum_von_monat, datum_bis_monat))
            row = row_to_dict(cursor.fetchone())
            umsatz_monat = row['umsatz'] or 0
            einsatz_monat = row['einsatz'] or 0
            
            monatswerte_summe['umsatz'] += umsatz_monat
            monatswerte_summe['einsatz'] += einsatz_monat
        
        print(f"Umsatz:")
        print(f"  YTD: {umsatz_ytd:,.2f} €")
        print(f"  Summe Monate: {monatswerte_summe['umsatz']:,.2f} €")
        print(f"  Differenz: {umsatz_ytd - monatswerte_summe['umsatz']:,.2f} €")
        print(f"  → Diese Differenz kommt von Hyundai 89xxxx Konten (nur in YTD)")
        
        return be_ytd, indirekte_ytd


if __name__ == '__main__':
    be_monat, indirekte_monat, konten = analysiere_monat_differenz()
    be_ytd, indirekte_ytd = analysiere_ytd_differenz()
    
    print(f"\n\n{'='*80}")
    print("ZUSAMMENFASSUNG")
    print("="*80)
    print(f"\nMonat Dezember 2025:")
    print(f"  DRIVE BE: {be_monat:,.2f} €")
    print(f"  GlobalCube BE: -116.248,00 €")
    print(f"  Differenz: {be_monat - (-116.248):,.2f} €")
    print(f"\nYTD bis Dezember 2025:")
    print(f"  DRIVE BE: {be_ytd:,.2f} €")
    print(f"  GlobalCube BE: -245.733,00 €")
    print(f"  Differenz: {be_ytd - (-245.733):,.2f} €")
