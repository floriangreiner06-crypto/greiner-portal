#!/usr/bin/env python3
"""
Analyse BWA Landau Dezember 2025 - Vergleich DRIVE vs. Globalcube
"""
import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import db_session, row_to_dict, get_guv_filter
from api.db_connection import convert_placeholders
from api.controlling_api import build_firma_standort_filter, KONTO_RANGES

# Globalcube Referenz-Werte (aus Screenshots)
GLOBALCUBE_LANDAU = {
    'monat': {
        'umsatz': 320121.00,
        'einsatz': 270455.00,
        'bruttoertrag': 49665.00,
        'variable_kosten': 7044.00,
        'bruttoertrag_ii': 42622.00,
        'direkte_kosten': 38724.00,
        'deckungsbeitrag': 3898.00,
        'indirekte_kosten': 40773.00,
        'betriebsergebnis': -36875.00,
        'neutrales_ergebnis': 0.00,
        'unternehmensergebnis': -36875.00
    },
    'kumuliert': {
        'umsatz': 1385360.00,
        'einsatz': 1133115.00,
        'bruttoertrag': 252245.00,
        'variable_kosten': 39162.00,
        'bruttoertrag_ii': 213083.00,
        'direkte_kosten': 140762.00,
        'deckungsbeitrag': 72321.00,
        'indirekte_kosten': 154541.00,
        'betriebsergebnis': -82219.00,
        'neutrales_ergebnis': 0.00,  # Globalcube zeigt 0, aber in anderen Screenshots -127
        'unternehmensergebnis': -82219.00
    }
}

def berechne_bwa_werte_direct(cursor, monat, jahr, firma, standort):
    """Berechnet BWA-Werte direkt ohne Flask-Import"""
    datum_von = f"{jahr}-{monat:02d}-01"
    if monat == 12:
        datum_bis = f"{jahr+1}-01-01"
    else:
        datum_bis = f"{jahr}-{monat+1:02d}-01"
    
    firma_filter_umsatz, firma_filter_einsatz, firma_filter_kosten, _ = build_firma_standort_filter(firma, standort)
    guv_filter = get_guv_filter()
    
    umsatz_range = KONTO_RANGES['umsatz']
    umsatz_sonder_range = KONTO_RANGES['umsatz_sonder']
    
    # Umsatz
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND ((nominal_account_number BETWEEN {umsatz_range[0]} AND {umsatz_range[1]})
               OR (nominal_account_number BETWEEN {umsatz_sonder_range[0]} AND {umsatz_sonder_range[1]}))
          {firma_filter_umsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    umsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Einsatz
    einsatz_range = KONTO_RANGES['einsatz']
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN {einsatz_range[0]} AND {einsatz_range[1]}
          {firma_filter_einsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    einsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Variable Kosten
    if standort == '2' and firma == '1':
        variable_kosten_filter = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
        variable_8910xx_include = True
    else:
        variable_kosten_filter = firma_filter_kosten
        variable_8910xx_include = True
    
    variable_kosten_where = """
          AND (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR (nominal_account_number BETWEEN 455000 AND 456999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            OR (nominal_account_number BETWEEN 487000 AND 487099
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            OR nominal_account_number BETWEEN 491000 AND 497899"""
    if variable_8910xx_include:
        variable_kosten_where += """
            OR nominal_account_number BETWEEN 891000 AND 891099"""
    variable_kosten_where += """
          )"""
    
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          {variable_kosten_where}
          {variable_kosten_filter}
          {guv_filter}
    """), (datum_von, datum_bis))
    variable = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Direkte Kosten
    if standort == '2' and firma == '1':
        direkte_kosten_filter = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
    else:
        direkte_kosten_filter = firma_filter_kosten
    
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          AND NOT (
            nominal_account_number = 410021
            OR nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 455000 AND 456999
            OR nominal_account_number BETWEEN 487000 AND 487099
            OR nominal_account_number BETWEEN 489000 AND 489999
            OR nominal_account_number BETWEEN 491000 AND 497999
          )
          {direkte_kosten_filter}
          {guv_filter}
    """), (datum_von, datum_bis))
    direkte = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Indirekte Kosten
    if standort == '2' and firma == '1':
        indirekte_kosten_filter = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
    else:
        indirekte_kosten_filter = firma_filter_kosten
    
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
          {indirekte_kosten_filter}
          {guv_filter}
    """), (datum_von, datum_bis))
    indirekte = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Neutrales Ergebnis
    neutral_range = KONTO_RANGES['neutral']
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN {neutral_range[0]} AND {neutral_range[1]}
          {firma_filter_umsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    neutral = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Berechnungen
    db1 = umsatz - einsatz
    db2 = db1 - variable
    db3 = db2 - direkte
    be = db3 - indirekte
    ue = be + neutral
    
    return {
        'umsatz': round(umsatz, 2),
        'einsatz': round(einsatz, 2),
        'db1': round(db1, 2),
        'variable': round(variable, 2),
        'db2': round(db2, 2),
        'direkte': round(direkte, 2),
        'db3': round(db3, 2),
        'indirekte': round(indirekte, 2),
        'betriebsergebnis': round(be, 2),
        'neutral': round(neutral, 2),
        'unternehmensergebnis': round(ue, 2)
    }

def berechne_bwa_ytd_direct(cursor, bis_monat, jahr, firma, standort):
    """Berechnet BWA YTD direkt ohne Flask-Import"""
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
    
    firma_filter_umsatz, firma_filter_einsatz, firma_filter_kosten, _ = build_firma_standort_filter(firma, standort)
    guv_filter = get_guv_filter()
    
    # Umsatz YTD
    umsatz_range_filter = "AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))"
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          {umsatz_range_filter}
          {firma_filter_umsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    umsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Einsatz YTD
    einsatz_range = KONTO_RANGES['einsatz']
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN {einsatz_range[0]} AND {einsatz_range[1]}
          {firma_filter_einsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    einsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Variable Kosten YTD
    if standort == '2' and firma == '1':
        variable_kosten_filter_ytd = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
        variable_8910xx_include_ytd = True
    else:
        variable_kosten_filter_ytd = firma_filter_kosten
        variable_8910xx_include_ytd = True
    
    variable_kosten_where_ytd = """
          AND (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR (nominal_account_number BETWEEN 455000 AND 456999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            OR (nominal_account_number BETWEEN 487000 AND 487099
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            OR nominal_account_number BETWEEN 491000 AND 497899"""
    if variable_8910xx_include_ytd:
        variable_kosten_where_ytd += """
            OR nominal_account_number BETWEEN 891000 AND 891099"""
    variable_kosten_where_ytd += """
          )"""
    
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          {variable_kosten_where_ytd}
          {variable_kosten_filter_ytd}
          {guv_filter}
    """), (datum_von, datum_bis))
    variable = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Direkte Kosten YTD
    if standort == '2' and firma == '1':
        direkte_kosten_filter_ytd = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
    else:
        direkte_kosten_filter_ytd = firma_filter_kosten
    
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          AND NOT (
            nominal_account_number = 410021
            OR nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 455000 AND 456999
            OR nominal_account_number BETWEEN 487000 AND 487099
            OR nominal_account_number BETWEEN 489000 AND 489999
            OR nominal_account_number BETWEEN 491000 AND 497999
          )
          {direkte_kosten_filter_ytd}
          {guv_filter}
    """), (datum_von, datum_bis))
    direkte = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Indirekte Kosten YTD
    if standort == '2' and firma == '1':
        indirekte_kosten_filter_ytd = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
    else:
        indirekte_kosten_filter_ytd = firma_filter_kosten
    
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
          {indirekte_kosten_filter_ytd}
          {guv_filter}
    """), (datum_von, datum_bis))
    indirekte = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Neutrales Ergebnis YTD
    neutral_range = KONTO_RANGES['neutral']
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN {neutral_range[0]} AND {neutral_range[1]}
          {firma_filter_umsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    neutral = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Berechnungen
    db1 = umsatz - einsatz
    db2 = db1 - variable
    db3 = db2 - direkte
    be = db3 - indirekte
    ue = be + neutral
    
    return {
        'umsatz': round(umsatz, 2),
        'einsatz': round(einsatz, 2),
        'db1': round(db1, 2),
        'variable': round(variable, 2),
        'db2': round(db2, 2),
        'direkte': round(direkte, 2),
        'db3': round(db3, 2),
        'indirekte': round(indirekte, 2),
        'betriebsergebnis': round(be, 2),
        'neutral': round(neutral, 2),
        'unternehmensergebnis': round(ue, 2)
    }

def main():
    print("=" * 80)
    print("BWA LANDAU DEZEMBER 2025 - VERGLEICH DRIVE vs. GLOBALCUBE")
    print("=" * 80)
    print()
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Monat Dezember 2025
        print("📊 MONAT DEZEMBER 2025")
        print("-" * 80)
        drive_monat = berechne_bwa_werte_direct(cursor, 12, 2025, '1', '2')
        
        if drive_monat:
            print(f"Umsatz:")
            print(f"  DRIVE:      {drive_monat['umsatz']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['monat']['umsatz']:>15,.2f} €")
            diff = drive_monat['umsatz'] - GLOBALCUBE_LANDAU['monat']['umsatz']
            print(f"  Differenz:  {diff:>15,.2f} € ({diff/GLOBALCUBE_LANDAU['monat']['umsatz']*100:+.2f}%)")
            print()
            
            print(f"Einsatz:")
            print(f"  DRIVE:      {drive_monat['einsatz']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['monat']['einsatz']:>15,.2f} €")
            diff = drive_monat['einsatz'] - GLOBALCUBE_LANDAU['monat']['einsatz']
            print(f"  Differenz:  {diff:>15,.2f} € ({diff/GLOBALCUBE_LANDAU['monat']['einsatz']*100:+.2f}%)")
            print()
            
            print(f"Bruttoertrag (DB1):")
            print(f"  DRIVE:      {drive_monat['db1']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['monat']['bruttoertrag']:>15,.2f} €")
            diff = drive_monat['db1'] - GLOBALCUBE_LANDAU['monat']['bruttoertrag']
            print(f"  Differenz:  {diff:>15,.2f} € ({diff/GLOBALCUBE_LANDAU['monat']['bruttoertrag']*100:+.2f}%)")
            print()
            
            print(f"Variable Kosten:")
            print(f"  DRIVE:      {drive_monat['variable']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['monat']['variable_kosten']:>15,.2f} €")
            diff = drive_monat['variable'] - GLOBALCUBE_LANDAU['monat']['variable_kosten']
            print(f"  Differenz:  {diff:>15,.2f} €")
            print()
            
            print(f"Bruttoertrag II (DB2):")
            print(f"  DRIVE:      {drive_monat['db2']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['monat']['bruttoertrag_ii']:>15,.2f} €")
            diff = drive_monat['db2'] - GLOBALCUBE_LANDAU['monat']['bruttoertrag_ii']
            print(f"  Differenz:  {diff:>15,.2f} €")
            print()
            
            print(f"Direkte Kosten:")
            print(f"  DRIVE:      {drive_monat['direkte']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['monat']['direkte_kosten']:>15,.2f} €")
            diff = drive_monat['direkte'] - GLOBALCUBE_LANDAU['monat']['direkte_kosten']
            print(f"  Differenz:  {diff:>15,.2f} €")
            print()
            
            print(f"Deckungsbeitrag (DB3):")
            print(f"  DRIVE:      {drive_monat['db3']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['monat']['deckungsbeitrag']:>15,.2f} €")
            diff = drive_monat['db3'] - GLOBALCUBE_LANDAU['monat']['deckungsbeitrag']
            print(f"  Differenz:  {diff:>15,.2f} €")
            print()
            
            print(f"Indirekte Kosten:")
            print(f"  DRIVE:      {drive_monat['indirekte']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['monat']['indirekte_kosten']:>15,.2f} €")
            diff = drive_monat['indirekte'] - GLOBALCUBE_LANDAU['monat']['indirekte_kosten']
            print(f"  Differenz:  {diff:>15,.2f} €")
            print()
            
            print(f"Betriebsergebnis:")
            print(f"  DRIVE:      {drive_monat['betriebsergebnis']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['monat']['betriebsergebnis']:>15,.2f} €")
            diff = drive_monat['betriebsergebnis'] - GLOBALCUBE_LANDAU['monat']['betriebsergebnis']
            print(f"  Differenz:  {diff:>15,.2f} €")
            if abs(diff) > 100:
                print(f"  ⚠️  ERHEBLICHE ABWEICHUNG!")
            print()
            
            print(f"Neutrales Ergebnis:")
            print(f"  DRIVE:      {drive_monat.get('neutrales', 0):>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['monat']['neutrales_ergebnis']:>15,.2f} €")
            diff = drive_monat.get('neutrales', 0) - GLOBALCUBE_LANDAU['monat']['neutrales_ergebnis']
            print(f"  Differenz:  {diff:>15,.2f} €")
            print()
            
            print(f"Unternehmensergebnis:")
            print(f"  DRIVE:      {drive_monat['unternehmensergebnis']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['monat']['unternehmensergebnis']:>15,.2f} €")
            diff = drive_monat['unternehmensergebnis'] - GLOBALCUBE_LANDAU['monat']['unternehmensergebnis']
            print(f"  Differenz:  {diff:>15,.2f} €")
            if abs(diff) > 100:
                print(f"  ⚠️  ERHEBLICHE ABWEICHUNG!")
            print()
        
        # YTD (Kumuliert Sep-Dez 2025)
        print("=" * 80)
        print("📊 KUMULIERT (YTD SEP-DEZ 2025)")
        print("-" * 80)
        drive_ytd = berechne_bwa_ytd_direct(cursor, 12, 2025, '1', '2')
        
        if drive_ytd:
            print(f"Umsatz:")
            print(f"  DRIVE:      {drive_ytd['umsatz']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['kumuliert']['umsatz']:>15,.2f} €")
            diff = drive_ytd['umsatz'] - GLOBALCUBE_LANDAU['kumuliert']['umsatz']
            print(f"  Differenz:  {diff:>15,.2f} € ({diff/GLOBALCUBE_LANDAU['kumuliert']['umsatz']*100:+.2f}%)")
            print()
            
            print(f"Einsatz:")
            print(f"  DRIVE:      {drive_ytd['einsatz']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['kumuliert']['einsatz']:>15,.2f} €")
            diff = drive_ytd['einsatz'] - GLOBALCUBE_LANDAU['kumuliert']['einsatz']
            print(f"  Differenz:  {diff:>15,.2f} € ({diff/GLOBALCUBE_LANDAU['kumuliert']['einsatz']*100:+.2f}%)")
            print()
            
            print(f"Bruttoertrag (DB1):")
            print(f"  DRIVE:      {drive_ytd['db1']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['kumuliert']['bruttoertrag']:>15,.2f} €")
            diff = drive_ytd['db1'] - GLOBALCUBE_LANDAU['kumuliert']['bruttoertrag']
            print(f"  Differenz:  {diff:>15,.2f} € ({diff/GLOBALCUBE_LANDAU['kumuliert']['bruttoertrag']*100:+.2f}%)")
            print()
            
            print(f"Variable Kosten:")
            print(f"  DRIVE:      {drive_ytd['variable']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['kumuliert']['variable_kosten']:>15,.2f} €")
            diff = drive_ytd['variable'] - GLOBALCUBE_LANDAU['kumuliert']['variable_kosten']
            print(f"  Differenz:  {diff:>15,.2f} €")
            print()
            
            print(f"Bruttoertrag II (DB2):")
            print(f"  DRIVE:      {drive_ytd['db2']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['kumuliert']['bruttoertrag_ii']:>15,.2f} €")
            diff = drive_ytd['db2'] - GLOBALCUBE_LANDAU['kumuliert']['bruttoertrag_ii']
            print(f"  Differenz:  {diff:>15,.2f} €")
            print()
            
            print(f"Direkte Kosten:")
            print(f"  DRIVE:      {drive_ytd['direkte']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['kumuliert']['direkte_kosten']:>15,.2f} €")
            diff = drive_ytd['direkte'] - GLOBALCUBE_LANDAU['kumuliert']['direkte_kosten']
            print(f"  Differenz:  {diff:>15,.2f} €")
            print()
            
            print(f"Deckungsbeitrag (DB3):")
            print(f"  DRIVE:      {drive_ytd['db3']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['kumuliert']['deckungsbeitrag']:>15,.2f} €")
            diff = drive_ytd['db3'] - GLOBALCUBE_LANDAU['kumuliert']['deckungsbeitrag']
            print(f"  Differenz:  {diff:>15,.2f} €")
            print()
            
            print(f"Indirekte Kosten:")
            print(f"  DRIVE:      {drive_ytd['indirekte']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['kumuliert']['indirekte_kosten']:>15,.2f} €")
            diff = drive_ytd['indirekte'] - GLOBALCUBE_LANDAU['kumuliert']['indirekte_kosten']
            print(f"  Differenz:  {diff:>15,.2f} €")
            print()
            
            print(f"Betriebsergebnis:")
            print(f"  DRIVE:      {drive_ytd['betriebsergebnis']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['kumuliert']['betriebsergebnis']:>15,.2f} €")
            diff = drive_ytd['betriebsergebnis'] - GLOBALCUBE_LANDAU['kumuliert']['betriebsergebnis']
            print(f"  Differenz:  {diff:>15,.2f} €")
            if abs(diff) > 1000:
                print(f"  ⚠️  ERHEBLICHE ABWEICHUNG!")
            print()
            
            print(f"Neutrales Ergebnis:")
            print(f"  DRIVE:      {drive_ytd.get('neutrales', 0):>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['kumuliert']['neutrales_ergebnis']:>15,.2f} €")
            diff = drive_ytd.get('neutrales', 0) - GLOBALCUBE_LANDAU['kumuliert']['neutrales_ergebnis']
            print(f"  Differenz:  {diff:>15,.2f} €")
            print()
            
            print(f"Unternehmensergebnis:")
            print(f"  DRIVE:      {drive_ytd['unternehmensergebnis']:>15,.2f} €")
            print(f"  Globalcube: {GLOBALCUBE_LANDAU['kumuliert']['unternehmensergebnis']:>15,.2f} €")
            diff = drive_ytd['unternehmensergebnis'] - GLOBALCUBE_LANDAU['kumuliert']['unternehmensergebnis']
            print(f"  Differenz:  {diff:>15,.2f} €")
            if abs(diff) > 1000:
                print(f"  ⚠️  ERHEBLICHE ABWEICHUNG!")
            print()

if __name__ == '__main__':
    main()
