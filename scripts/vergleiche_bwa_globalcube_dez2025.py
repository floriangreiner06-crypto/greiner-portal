#!/usr/bin/env python3
"""Vergleich BWA DRIVE vs. GlobalCube - Dezember 2025"""
import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session
from api.db_connection import convert_placeholders
import psycopg2.extras

# GlobalCube Referenz-Werte (aus Screenshot/Bericht)
GLOBALCUBE_REF = {
    'umsatz_monat': 2190826,
    'einsatz_monat': 1862668,
    'variable_monat': 69374,
    'direkte_monat': 189866,
    'indirekte_monat': 185058,
    'be_monat': -116140,
    'ue_monat': -83411,
    'umsatz_ytd': 10618507,
    'einsatz_ytd': 9191864,
    'variable_ytd': 304268,
    'direkte_ytd': 659229,
    'indirekte_ytd': 838944,
    'be_ytd': -375797,
    'ue_ytd': -245524,
}

with locosoft_session() as conn:
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print('=== BWA VERGLEICH: DRIVE vs. GLOBALCUBE ===\n')
    print('Zeitraum: Dezember 2025 (Monat) und Sep-Dez 2025 (YTD)\n')
    
    # Monat Dezember 2025
    datum_von_monat = '2025-12-01'
    datum_bis_monat = '2026-01-01'
    
    # YTD Sep-Dez 2025
    datum_von_ytd = '2025-09-01'
    datum_bis_ytd = '2026-01-01'
    
    # Umsatz Monat
    cursor.execute(convert_placeholders('''
        SELECT SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as wert
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND ((nominal_account_number BETWEEN 800000 AND 889999)
               OR (nominal_account_number BETWEEN 893200 AND 893299))
    '''), (datum_von_monat, datum_bis_monat))
    umsatz_monat = cursor.fetchone()['wert'] or 0
    
    # Einsatz Monat
    cursor.execute(convert_placeholders('''
        SELECT SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
    '''), (datum_von_monat, datum_bis_monat))
    einsatz_monat = cursor.fetchone()['wert'] or 0
    
    # Variable Kosten Monat
    cursor.execute(convert_placeholders('''
        SELECT SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR (nominal_account_number BETWEEN 455000 AND 456999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            OR (nominal_account_number BETWEEN 487000 AND 487099
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            OR nominal_account_number BETWEEN 491000 AND 497899
          )
    '''), (datum_von_monat, datum_bis_monat))
    variable_monat = cursor.fetchone()['wert'] or 0
    
    # Direkte Kosten Monat (mit Ausschlüssen)
    cursor.execute(convert_placeholders('''
        SELECT SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7')
          AND NOT (
            nominal_account_number = 410021
            OR nominal_account_number BETWEEN 411000 AND 411999
            OR nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 455000 AND 456999
            OR nominal_account_number BETWEEN 487000 AND 487099
            OR nominal_account_number BETWEEN 489000 AND 489999
            OR nominal_account_number BETWEEN 491000 AND 497999
          )
    '''), (datum_von_monat, datum_bis_monat))
    direkte_monat = cursor.fetchone()['wert'] or 0
    
    # Indirekte Kosten Monat (mit Ausschluss 8910xx)
    cursor.execute(convert_placeholders('''
        SELECT SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND (
            (nominal_account_number BETWEEN 400000 AND 499999
             AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
            OR nominal_account_number = 410021
            OR nominal_account_number BETWEEN 411000 AND 411999
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 489000 AND 489999
            OR nominal_account_number BETWEEN 498000 AND 499999
            OR (nominal_account_number BETWEEN 891000 AND 896999
                AND NOT (nominal_account_number BETWEEN 893200 AND 893299)
                AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
          )
    '''), (datum_von_monat, datum_bis_monat))
    indirekte_monat = cursor.fetchone()['wert'] or 0
    
    # Neutrales Ergebnis Monat
    cursor.execute(convert_placeholders('''
        SELECT SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as wert
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 200000 AND 299999
    '''), (datum_von_monat, datum_bis_monat))
    neutral_monat = cursor.fetchone()['wert'] or 0
    
    db1_monat = umsatz_monat - einsatz_monat
    db2_monat = db1_monat - variable_monat
    db3_monat = db2_monat - direkte_monat
    be_monat = db3_monat - indirekte_monat
    ue_monat = be_monat + neutral_monat
    
    print('=== MONAT DEZEMBER 2025 ===\n')
    print(f'{"Position":<25} {"DRIVE":>15} {"GlobalCube":>15} {"Differenz":>15} {"% Diff":>10}')
    print('-' * 80)
    
    for pos, drive, gc in [
        ('Umsatz', umsatz_monat, GLOBALCUBE_REF['umsatz_monat']),
        ('Einsatz', einsatz_monat, GLOBALCUBE_REF['einsatz_monat']),
        ('DB1', db1_monat, None),
        ('Variable Kosten', variable_monat, GLOBALCUBE_REF['variable_monat']),
        ('DB2', db2_monat, None),
        ('Direkte Kosten', direkte_monat, GLOBALCUBE_REF['direkte_monat']),
        ('DB3', db3_monat, None),
        ('Indirekte Kosten', indirekte_monat, GLOBALCUBE_REF['indirekte_monat']),
        ('Betriebsergebnis', be_monat, GLOBALCUBE_REF['be_monat']),
        ('Neutral', neutral_monat, None),
        ('Unternehmensergebnis', ue_monat, GLOBALCUBE_REF['ue_monat']),
    ]:
        if gc is not None:
            diff = drive - gc
            pct = (diff / abs(gc) * 100) if gc != 0 else 0
            print(f'{pos:<25} {drive:>15,.2f} {gc:>15,.2f} {diff:>15,.2f} {pct:>9.2f}%')
        else:
            print(f'{pos:<25} {drive:>15,.2f} {"":>15} {"":>15} {"":>10}')
    
    # YTD Werte
    cursor.execute(convert_placeholders('''
        SELECT SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as wert
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND ((nominal_account_number BETWEEN 800000 AND 889999)
               OR (nominal_account_number BETWEEN 893200 AND 893299))
    '''), (datum_von_ytd, datum_bis_ytd))
    umsatz_ytd = cursor.fetchone()['wert'] or 0
    
    cursor.execute(convert_placeholders('''
        SELECT SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
    '''), (datum_von_ytd, datum_bis_ytd))
    einsatz_ytd = cursor.fetchone()['wert'] or 0
    
    cursor.execute(convert_placeholders('''
        SELECT SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR (nominal_account_number BETWEEN 455000 AND 456999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            OR (nominal_account_number BETWEEN 487000 AND 487099
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            OR nominal_account_number BETWEEN 491000 AND 497899
          )
    '''), (datum_von_ytd, datum_bis_ytd))
    variable_ytd = cursor.fetchone()['wert'] or 0
    
    cursor.execute(convert_placeholders('''
        SELECT SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7')
          AND NOT (
            nominal_account_number = 410021
            OR nominal_account_number BETWEEN 411000 AND 411999
            OR nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 455000 AND 456999
            OR nominal_account_number BETWEEN 487000 AND 487099
            OR nominal_account_number BETWEEN 489000 AND 489999
            OR nominal_account_number BETWEEN 491000 AND 497999
          )
    '''), (datum_von_ytd, datum_bis_ytd))
    direkte_ytd = cursor.fetchone()['wert'] or 0
    
    cursor.execute(convert_placeholders('''
        SELECT SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND (
            (nominal_account_number BETWEEN 400000 AND 499999
             AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
            OR nominal_account_number = 410021
            OR nominal_account_number BETWEEN 411000 AND 411999
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 489000 AND 489999
            OR nominal_account_number BETWEEN 498000 AND 499999
            OR (nominal_account_number BETWEEN 891000 AND 896999
                AND NOT (nominal_account_number BETWEEN 893200 AND 893299)
                AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
          )
    '''), (datum_von_ytd, datum_bis_ytd))
    indirekte_ytd = cursor.fetchone()['wert'] or 0
    
    cursor.execute(convert_placeholders('''
        SELECT SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as wert
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 200000 AND 299999
    '''), (datum_von_ytd, datum_bis_ytd))
    neutral_ytd = cursor.fetchone()['wert'] or 0
    
    db1_ytd = umsatz_ytd - einsatz_ytd
    db2_ytd = db1_ytd - variable_ytd
    db3_ytd = db2_ytd - direkte_ytd
    be_ytd = db3_ytd - indirekte_ytd
    ue_ytd = be_ytd + neutral_ytd
    
    print('\n=== YTD (SEP-DEZ 2025) ===\n')
    print(f'{"Position":<25} {"DRIVE":>15} {"GlobalCube":>15} {"Differenz":>15} {"% Diff":>10}')
    print('-' * 80)
    
    for pos, drive, gc in [
        ('Umsatz', umsatz_ytd, GLOBALCUBE_REF['umsatz_ytd']),
        ('Einsatz', einsatz_ytd, GLOBALCUBE_REF['einsatz_ytd']),
        ('DB1', db1_ytd, None),
        ('Variable Kosten', variable_ytd, GLOBALCUBE_REF['variable_ytd']),
        ('DB2', db2_ytd, None),
        ('Direkte Kosten', direkte_ytd, GLOBALCUBE_REF['direkte_ytd']),
        ('DB3', db3_ytd, None),
        ('Indirekte Kosten', indirekte_ytd, GLOBALCUBE_REF['indirekte_ytd']),
        ('Betriebsergebnis', be_ytd, GLOBALCUBE_REF['be_ytd']),
        ('Neutral', neutral_ytd, None),
        ('Unternehmensergebnis', ue_ytd, GLOBALCUBE_REF['ue_ytd']),
    ]:
        if gc is not None:
            diff = drive - gc
            pct = (diff / abs(gc) * 100) if gc != 0 else 0
            print(f'{pos:<25} {drive:>15,.2f} {gc:>15,.2f} {diff:>15,.2f} {pct:>9.2f}%')
        else:
            print(f'{pos:<25} {drive:>15,.2f} {"":>15} {"":>15} {"":>10}')
