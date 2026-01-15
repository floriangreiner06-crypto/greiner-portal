#!/usr/bin/env python3
"""
BWA Betriebsergebnis-Probleme analysieren - TAG 188

Analysiert die Abweichungen zwischen DRIVE und GlobalCube:
- YTD Betriebsergebnis: -161.880,15 € Differenz
- Monat Betriebsergebnis: 100,63 € Differenz

Ziel: Identifiziere die Ursachen und korrigiere die BWA-Berechnung.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

def analysiere_monat_betriebsergebnis(jahr: int, monat: int):
    """Analysiert das Betriebsergebnis für einen Monat."""
    print(f"\n{'='*80}")
    print(f"ANALYSE: Monat {monat}/{jahr} - Betriebsergebnis")
    print(f"{'='*80}\n")
    
    datum_von = f"{jahr}-{monat:02d}-01"
    if monat == 12:
        datum_bis = f"{jahr+1}-01-01"
    else:
        datum_bis = f"{jahr}-{monat+1:02d}-01"
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        # G&V-Filter
        from api.db_utils import get_guv_filter
        guv_filter = get_guv_filter()
        
        # 1. Umsatz
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
        
        # 2. Einsatz
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
        
        # 3. Variable Kosten
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
        
        # 4. Direkte Kosten
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
        
        # 5. Indirekte Kosten
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
              AND (
                (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2))
                OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1)
              )
              {guv_filter}
        """), (datum_von, datum_bis))
        indirekte = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Indirekte Kosten: {indirekte:,.2f} €")
        
        # 6. Betriebsergebnis
        be = db3 - indirekte
        print(f"\n{'─'*80}")
        print(f"BETRIEBSERGEBNIS: {be:,.2f} €")
        print(f"{'─'*80}")
        
        # Vergleich mit GlobalCube
        print(f"\nGlobalCube Referenz: -116.248,00 €")
        print(f"DRIVE berechnet: {be:,.2f} €")
        differenz = be - (-116.248)
        print(f"Differenz: {differenz:,.2f} € ({'DRIVE zu hoch' if differenz > 0 else 'DRIVE zu niedrig'})")
        
        # Detail-Analyse: Prüfe ob es zusätzliche Kosten gibt
        print(f"\n{'='*80}")
        print("DETAIL-ANALYSE: Zusätzliche Kosten-Positionen")
        print(f"{'='*80}\n")
        
        # Prüfe alle Kosten-Konten die nicht in direkten/indirekten/variablen enthalten sind
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
            HAVING ABS(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0) > 100
            ORDER BY ABS(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0) DESC
            LIMIT 50
        """), (datum_von, datum_bis))
        
        print("Top 50 Kosten-Konten (nicht kategorisiert):")
        for row in cursor.fetchall():
            r = row_to_dict(row)
            print(f"  Konto {r['nominal_account_number']}: {r['summe']:,.2f} € ({r['anzahl']} Buchungen)")
        
        return {
            'umsatz': umsatz,
            'einsatz': einsatz,
            'db1': db1,
            'variable': variable,
            'db2': db2,
            'direkte': direkte,
            'db3': db3,
            'indirekte': indirekte,
            'betriebsergebnis': be
        }


def analysiere_ytd_betriebsergebnis(jahr: int, bis_monat: int):
    """Analysiert das YTD Betriebsergebnis."""
    print(f"\n{'='*80}")
    print(f"ANALYSE: YTD bis {bis_monat}/{jahr} - Betriebsergebnis")
    print(f"{'='*80}\n")
    
    # Wirtschaftsjahr: Start am 1. September
    WJ_START_MONAT = 9
    if bis_monat >= WJ_START_MONAT:
        wj_start_jahr = jahr
    else:
        wj_start_jahr = jahr - 1
    
    datum_von = f"{wj_start_jahr}-{WJ_START_MONAT:02d}-01"
    if bis_monat == 12:
        datum_bis = f"{jahr+1}-01-01"
    else:
        datum_bis = f"{jahr}-{bis_monat+1:02d}-01"
    
    print(f"Zeitraum: {datum_von} bis {datum_bis}")
    
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
        umsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Umsatz YTD: {umsatz:,.2f} €")
        
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
        einsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Einsatz YTD: {einsatz:,.2f} €")
        
        db1 = umsatz - einsatz
        print(f"DB1 YTD: {db1:,.2f} €")
        
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
        variable = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Variable Kosten YTD: {variable:,.2f} €")
        
        db2 = db1 - variable
        print(f"DB2 YTD: {db2:,.2f} €")
        
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
        direkte = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Direkte Kosten YTD: {direkte:,.2f} €")
        
        db3 = db2 - direkte
        print(f"DB3 YTD: {db3:,.2f} €")
        
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
              )
              AND (
                (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2))
                OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1)
              )
              {guv_filter}
        """), (datum_von, datum_bis))
        indirekte = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        print(f"Indirekte Kosten YTD: {indirekte:,.2f} €")
        
        # 6. Betriebsergebnis YTD
        be = db3 - indirekte
        print(f"\n{'─'*80}")
        print(f"BETRIEBSERGEBNIS YTD: {be:,.2f} €")
        print(f"{'─'*80}")
        
        # Vergleich mit GlobalCube
        print(f"\nGlobalCube Referenz: -245.733,00 €")
        print(f"DRIVE berechnet: {be:,.2f} €")
        print(f"Differenz: {be - (-245.733):,.2f} €")
        
        # Vergleich mit Summe der Monatswerte
        print(f"\n{'='*80}")
        print("VERGLEICH: YTD vs. Summe Monatswerte (Sep-Dez 2025)")
        print(f"{'='*80}\n")
        
        monatswerte_summe = {
            'umsatz': 0,
            'einsatz': 0,
            'variable': 0,
            'direkte': 0,
            'indirekte': 0,
            'betriebsergebnis': 0
        }
        
        for monat in [9, 10, 11, 12]:
            werte = analysiere_monat_betriebsergebnis(2025, monat)
            monatswerte_summe['umsatz'] += werte['umsatz']
            monatswerte_summe['einsatz'] += werte['einsatz']
            monatswerte_summe['variable'] += werte['variable']
            monatswerte_summe['direkte'] += werte['direkte']
            monatswerte_summe['indirekte'] += werte['indirekte']
            monatswerte_summe['betriebsergebnis'] += werte['betriebsergebnis']
        
        print(f"\nSumme Monatswerte (Sep-Dez):")
        print(f"  Umsatz: {monatswerte_summe['umsatz']:,.2f} €")
        print(f"  Einsatz: {monatswerte_summe['einsatz']:,.2f} €")
        print(f"  Variable Kosten: {monatswerte_summe['variable']:,.2f} €")
        print(f"  Direkte Kosten: {monatswerte_summe['direkte']:,.2f} €")
        print(f"  Indirekte Kosten: {monatswerte_summe['indirekte']:,.2f} €")
        print(f"  Betriebsergebnis: {monatswerte_summe['betriebsergebnis']:,.2f} €")
        
        print(f"\nYTD-Berechnung:")
        print(f"  Umsatz: {umsatz:,.2f} € (Diff: {umsatz - monatswerte_summe['umsatz']:,.2f} €)")
        print(f"  Einsatz: {einsatz:,.2f} € (Diff: {einsatz - monatswerte_summe['einsatz']:,.2f} €)")
        print(f"  Variable Kosten: {variable:,.2f} € (Diff: {variable - monatswerte_summe['variable']:,.2f} €)")
        print(f"  Direkte Kosten: {direkte:,.2f} € (Diff: {direkte - monatswerte_summe['direkte']:,.2f} €)")
        print(f"  Indirekte Kosten: {indirekte:,.2f} € (Diff: {indirekte - monatswerte_summe['indirekte']:,.2f} €)")
        print(f"  Betriebsergebnis: {be:,.2f} € (Diff: {be - monatswerte_summe['betriebsergebnis']:,.2f} €)")
        
        return {
            'umsatz': umsatz,
            'einsatz': einsatz,
            'db1': db1,
            'variable': variable,
            'db2': db2,
            'direkte': direkte,
            'db3': db3,
            'indirekte': indirekte,
            'betriebsergebnis': be,
            'monatswerte_summe': monatswerte_summe
        }


if __name__ == '__main__':
    print("="*80)
    print("BWA BETRIEBSERGEBNIS-ANALYSE - TAG 188")
    print("="*80)
    
    # 1. Monat Dezember 2025 analysieren
    print("\n" + "="*80)
    print("TEIL 1: MONAT DEZEMBER 2025")
    print("="*80)
    monat_werte = analysiere_monat_betriebsergebnis(2025, 12)
    
    # 2. YTD bis Dezember 2025 analysieren
    print("\n" + "="*80)
    print("TEIL 2: YTD BIS DEZEMBER 2025")
    print("="*80)
    ytd_werte = analysiere_ytd_betriebsergebnis(2025, 12)
    
    print("\n" + "="*80)
    print("ANALYSE ABGESCHLOSSEN")
    print("="*80)
