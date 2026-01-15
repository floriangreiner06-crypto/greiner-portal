#!/usr/bin/env python3
"""
KOMPLETTE BWA-ANALYSE für Gesamtbetrieb
Analysiert ALLE Positionen systematisch, nicht nur Einsatzwerte!
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_connection import get_db
from decimal import Decimal
from collections import defaultdict

# GlobalCube Referenzwerte (Dezember 2025, YTD Sep-Dez 2025)
GLOBALCUBE_MONAT = {
    'umsatz': 2190718.00,
    'einsatz': 1862668.00,
    'db1': 328050.00,
    'variable_kosten': 69374.00,
    'db2': 258676.00,
    'direkte_kosten': 189866.00,
    'db3': 68810.00,
    'indirekte_kosten': 185058.00,
    'betriebsergebnis': -116248.00,
    'neutrales_ergebnis': 32629.00,
    'unternehmensergebnis': -83619.00
}

GLOBALCUBE_YTD = {
    'umsatz': 10618400.00,
    'einsatz': 9191864.00,
    'db1': 1426536.00,
    'variable_kosten': 304268.00,
    'db2': 1222268.00,
    'direkte_kosten': 659229.00,
    'db3': 463039.00,
    'indirekte_kosten': 838944.00,
    'betriebsergebnis': -375905.00,
    'neutrales_ergebnis': 130172.00,
    'unternehmensergebnis': -245733.00
}

def analyse_position(cursor, position_name, query, datum_von, datum_bis, globalcube_wert_monat, globalcube_wert_ytd):
    """Analysiert eine einzelne BWA-Position detailliert"""
    print(f"\n{'='*100}")
    print(f"POSITION: {position_name.upper()}")
    print(f"{'='*100}")
    
    # Monatswert
    cursor.execute(query, (datum_von, datum_bis))
    monat_wert = Decimal(str(cursor.fetchone()[0] or 0))
    monat_diff = monat_wert - Decimal(str(globalcube_wert_monat))
    monat_diff_pct = (monat_diff / Decimal(str(globalcube_wert_monat)) * 100) if globalcube_wert_monat != 0 else 0
    
    # YTD-Wert
    datum_von_ytd = '2025-09-01'
    cursor.execute(query, (datum_von_ytd, datum_bis))
    ytd_wert = Decimal(str(cursor.fetchone()[0] or 0))
    ytd_diff = ytd_wert - Decimal(str(globalcube_wert_ytd))
    ytd_diff_pct = (ytd_diff / Decimal(str(globalcube_wert_ytd)) * 100) if globalcube_wert_ytd != 0 else 0
    
    print(f"\nMONAT (Dezember 2025):")
    print(f"  DRIVE:      {monat_wert:>15,.2f} €")
    print(f"  GlobalCube: {globalcube_wert_monat:>15,.2f} €")
    print(f"  Differenz:  {monat_diff:>15,.2f} € ({monat_diff_pct:>6.2f}%)")
    
    print(f"\nYTD (Sep-Dez 2025):")
    print(f"  DRIVE:      {ytd_wert:>15,.2f} €")
    print(f"  GlobalCube: {globalcube_wert_ytd:>15,.2f} €")
    print(f"  Differenz:  {ytd_diff:>15,.2f} € ({ytd_diff_pct:>6.2f}%)")
    
    # Status
    if abs(monat_diff) < 100 and abs(ytd_diff) < 1000:
        status = "✅ OK"
    elif abs(monat_diff) < 1000 and abs(ytd_diff) < 10000:
        status = "⚠️ WARNUNG"
    else:
        status = "🚨 FEHLER"
    
    print(f"\n  Status: {status}")
    
    return {
        'position': position_name,
        'monat_wert': monat_wert,
        'monat_diff': monat_diff,
        'ytd_wert': ytd_wert,
        'ytd_diff': ytd_diff,
        'status': status
    }

def main():
    conn = get_db()
    cursor = conn.cursor()
    
    print("="*100)
    print("KOMPLETTE BWA-ANALYSE: GESAMTBETRIEB")
    print("="*100)
    print("\nAnalysiert ALLE Positionen systematisch:")
    print("  1. Umsatz")
    print("  2. Einsatz")
    print("  3. Variable Kosten")
    print("  4. Direkte Kosten")
    print("  5. Indirekte Kosten")
    print("  6. Neutrales Ergebnis")
    print("  7. Berechnete Werte (DB1, DB2, DB3, BE, UE)")
    
    datum_von = '2025-12-01'
    datum_bis = '2026-01-01'
    
    # Filter für Gesamtbetrieb (firma=0, standort=0) - direkt implementiert
    # Umsatz: Deggendorf (branch=1, subsidiary=1) + Hyundai (branch=2, subsidiary=2) + Landau (branch=3, subsidiary=1)
    firma_filter_umsatz = "AND ((branch_number = 1 AND subsidiary_to_company_ref = 1) OR (branch_number = 2 AND subsidiary_to_company_ref = 2) OR (branch_number = 3 AND subsidiary_to_company_ref = 1))"
    # Einsatz: Deggendorf (6. Ziffer='1' OR (74xxxx AND branch=1)) AND subsidiary=1 AND branch != 3) + Landau (branch=3 AND subsidiary=1) + Hyundai (6. Ziffer='1' AND subsidiary=2)
    firma_filter_einsatz = """AND (
            ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
            OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
            OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
        )"""
    # Kosten: Deggendorf (6. Ziffer='1', subsidiary=1) + Hyundai (6. Ziffer='1', subsidiary=2) + Landau (6. Ziffer='2', subsidiary=1)
    firma_filter_kosten = "AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2)) OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1))"
    
    # G&V-Filter
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    
    results = []
    
    # 1. UMSATZ
    umsatz_query = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
          {firma_filter_umsatz}
          {guv_filter}
    """
    results.append(analyse_position(
        cursor, 'Umsatz', umsatz_query, datum_von, datum_bis,
        GLOBALCUBE_MONAT['umsatz'], GLOBALCUBE_YTD['umsatz']
    ))
    
    # 2. EINSATZ
    einsatz_query = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          {firma_filter_einsatz}
          {guv_filter}
    """
    results.append(analyse_position(
        cursor, 'Einsatz', einsatz_query, datum_von, datum_bis,
        GLOBALCUBE_MONAT['einsatz'], GLOBALCUBE_YTD['einsatz']
    ))
    
    # 3. VARIABLE KOSTEN
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
          {firma_filter_kosten}
          {guv_filter}
    """
    results.append(analyse_position(
        cursor, 'Variable Kosten', variable_query, datum_von, datum_bis,
        GLOBALCUBE_MONAT['variable_kosten'], GLOBALCUBE_YTD['variable_kosten']
    ))
    
    # 4. DIREKTE KOSTEN
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
    results.append(analyse_position(
        cursor, 'Direkte Kosten', direkte_query, datum_von, datum_bis,
        GLOBALCUBE_MONAT['direkte_kosten'], GLOBALCUBE_YTD['direkte_kosten']
    ))
    
    # 5. INDIREKTE KOSTEN
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
    results.append(analyse_position(
        cursor, 'Indirekte Kosten', indirekte_query, datum_von, datum_bis,
        GLOBALCUBE_MONAT['indirekte_kosten'], GLOBALCUBE_YTD['indirekte_kosten']
    ))
    
    # 6. NEUTRALES ERGEBNIS
    neutral_query = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 200000 AND 299999
          {firma_filter_umsatz}
          {guv_filter}
    """
    results.append(analyse_position(
        cursor, 'Neutrales Ergebnis', neutral_query, datum_von, datum_bis,
        GLOBALCUBE_MONAT['neutrales_ergebnis'], GLOBALCUBE_YTD['neutrales_ergebnis']
    ))
    
    # ZUSAMMENFASSUNG
    print(f"\n{'='*100}")
    print("ZUSAMMENFASSUNG")
    print(f"{'='*100}")
    print(f"\n{'Position':<25} {'Monat Diff':>15} {'YTD Diff':>15} {'Status':<10}")
    print("-" * 100)
    
    for r in results:
        print(f"{r['position']:<25} {r['monat_diff']:>15,.2f} € {r['ytd_diff']:>15,.2f} € {r['status']:<10}")
    
    # Berechnete Werte
    print(f"\n{'='*100}")
    print("BERECHNETE WERTE")
    print(f"{'='*100}")
    
    umsatz = next(r for r in results if r['position'] == 'Umsatz')
    einsatz = next(r for r in results if r['position'] == 'Einsatz')
    variable = next(r for r in results if r['position'] == 'Variable Kosten')
    direkte = next(r for r in results if r['position'] == 'Direkte Kosten')
    indirekte = next(r for r in results if r['position'] == 'Indirekte Kosten')
    neutral = next(r for r in results if r['position'] == 'Neutrales Ergebnis')
    
    # Monat
    db1_monat = umsatz['monat_wert'] - einsatz['monat_wert']
    db2_monat = db1_monat - variable['monat_wert']
    db3_monat = db2_monat - direkte['monat_wert']
    be_monat = db3_monat - indirekte['monat_wert']
    ue_monat = be_monat + neutral['monat_wert']
    
    print(f"\nMONAT (Dezember 2025):")
    print(f"  DB1 (Bruttoertrag):     {db1_monat:>15,.2f} € (GlobalCube: {GLOBALCUBE_MONAT['db1']:>15,.2f} €, Diff: {db1_monat - Decimal(str(GLOBALCUBE_MONAT['db1'])):>15,.2f} €)")
    print(f"  DB2:                     {db2_monat:>15,.2f} € (GlobalCube: {GLOBALCUBE_MONAT['db2']:>15,.2f} €, Diff: {db2_monat - Decimal(str(GLOBALCUBE_MONAT['db2'])):>15,.2f} €)")
    print(f"  DB3:                     {db3_monat:>15,.2f} € (GlobalCube: {GLOBALCUBE_MONAT['db3']:>15,.2f} €, Diff: {db3_monat - Decimal(str(GLOBALCUBE_MONAT['db3'])):>15,.2f} €)")
    print(f"  Betriebsergebnis:        {be_monat:>15,.2f} € (GlobalCube: {GLOBALCUBE_MONAT['betriebsergebnis']:>15,.2f} €, Diff: {be_monat - Decimal(str(GLOBALCUBE_MONAT['betriebsergebnis'])):>15,.2f} €)")
    print(f"  Unternehmensergebnis:    {ue_monat:>15,.2f} € (GlobalCube: {GLOBALCUBE_MONAT['unternehmensergebnis']:>15,.2f} €, Diff: {ue_monat - Decimal(str(GLOBALCUBE_MONAT['unternehmensergebnis'])):>15,.2f} €)")
    
    # YTD
    db1_ytd = umsatz['ytd_wert'] - einsatz['ytd_wert']
    db2_ytd = db1_ytd - variable['ytd_wert']
    db3_ytd = db2_ytd - direkte['ytd_wert']
    be_ytd = db3_ytd - indirekte['ytd_wert']
    ue_ytd = be_ytd + neutral['ytd_wert']
    
    print(f"\nYTD (Sep-Dez 2025):")
    print(f"  DB1 (Bruttoertrag):     {db1_ytd:>15,.2f} € (GlobalCube: {GLOBALCUBE_YTD['db1']:>15,.2f} €, Diff: {db1_ytd - Decimal(str(GLOBALCUBE_YTD['db1'])):>15,.2f} €)")
    print(f"  DB2:                     {db2_ytd:>15,.2f} € (GlobalCube: {GLOBALCUBE_YTD['db2']:>15,.2f} €, Diff: {db2_ytd - Decimal(str(GLOBALCUBE_YTD['db2'])):>15,.2f} €)")
    print(f"  DB3:                     {db3_ytd:>15,.2f} € (GlobalCube: {GLOBALCUBE_YTD['db3']:>15,.2f} €, Diff: {db3_ytd - Decimal(str(GLOBALCUBE_YTD['db3'])):>15,.2f} €)")
    print(f"  Betriebsergebnis:        {be_ytd:>15,.2f} € (GlobalCube: {GLOBALCUBE_YTD['betriebsergebnis']:>15,.2f} €, Diff: {be_ytd - Decimal(str(GLOBALCUBE_YTD['betriebsergebnis'])):>15,.2f} €)")
    print(f"  Unternehmensergebnis:    {ue_ytd:>15,.2f} € (GlobalCube: {GLOBALCUBE_YTD['unternehmensergebnis']:>15,.2f} €, Diff: {ue_ytd - Decimal(str(GLOBALCUBE_YTD['unternehmensergebnis'])):>15,.2f} €)")
    
    conn.close()

if __name__ == '__main__':
    main()
