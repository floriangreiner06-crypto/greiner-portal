#!/usr/bin/env python3
"""
Detail-Analyse: Betriebsergebnis-Abweichung - Komponenten-Vergleich
====================================================================
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

# Globalcube Werte aus CSV (Zeile 34, 36, 46)
# Jahr per Aug./2025:
# - Deckungsbeitrag (DB3): 2.801.501,76 €
# - Indirekte Kosten: 2.479.617,08 €
# - Betriebsergebnis: 321.884,68 €

globalcube_jahr = {
    'db3': 2801501.76,
    'indirekte': 2479617.08,
    'be': 321884.68
}

print("=" * 100)
print("DETAIL-ANALYSE: Betriebsergebnis Jahr per Aug./2025")
print("=" * 100)

jahr = 2025
monat = 8
datum_von = "2024-09-01"  # WJ-Start
datum_bis = "2025-09-01"  # Bis Ende August

firma_filter_umsatz = ''
firma_filter_einsatz = ''
firma_filter_kosten = ''
guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"

with db_session() as conn:
    cursor = conn.cursor()
    
    # DB3 (Deckungsbeitrag 3) = DB2 - Direkte Kosten
    # DB2 = DB1 - Variable Kosten
    # DB1 = Umsatz - Einsatz
    
    # Umsatz
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND ((nominal_account_number BETWEEN 800000 AND 889999)
               OR (nominal_account_number BETWEEN 893200 AND 893299))
          {firma_filter_umsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    umsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Einsatz
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          {firma_filter_einsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    einsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
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
          )
          {firma_filter_kosten}
          {guv_filter}
    """), (datum_von, datum_bis))
    variable = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
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
            OR nominal_account_number BETWEEN 491000 AND 497999
          )
          {firma_filter_kosten}
          {guv_filter}
    """), (datum_von, datum_bis))
    direkte = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Indirekte Kosten - DETAILLIERT
    print(f"\nIndirekte Kosten - Komponenten:")
    print(f"  Zeitraum: {datum_von} - {datum_bis}")
    
    # 1. KST 0 (5. Ziffer = '0')
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0'
          {firma_filter_kosten}
          {guv_filter}
    """), (datum_von, datum_bis))
    kst0 = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    print(f"  KST 0 (4xxxx0):        {kst0:>15,.2f} €")
    
    # 2. 424xx mit KST 1-7
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 424000 AND 424999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7')
          {firma_filter_kosten}
          {guv_filter}
    """), (datum_von, datum_bis))
    ind424 = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    print(f"  424xx KST 1-7:         {ind424:>15,.2f} €")
    
    # 3. 438xx mit KST 1-7
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 438000 AND 438999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7')
          {firma_filter_kosten}
          {guv_filter}
    """), (datum_von, datum_bis))
    ind438 = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    print(f"  438xx KST 1-7:         {ind438:>15,.2f} €")
    
    # 4. 498xx
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 498000 AND 499999
          {firma_filter_kosten}
          {guv_filter}
    """), (datum_von, datum_bis))
    ind498 = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    print(f"  498xx:                 {ind498:>15,.2f} €")
    
    # 5. 89xxxx (OHNE 8932xx)
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 891000 AND 896999
          AND NOT (nominal_account_number BETWEEN 893200 AND 893299)
          {firma_filter_kosten}
          {guv_filter}
    """), (datum_von, datum_bis))
    ind89 = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    print(f"  89xxxx (ohne 8932xx):  {ind89:>15,.2f} €")
    
    indirekte_gesamt = kst0 + ind424 + ind438 + ind498 + ind89
    print(f"  SUMME Indirekte:       {indirekte_gesamt:>15,.2f} €")
    print(f"  Globalcube Indirekte: {globalcube_jahr['indirekte']:>15,.2f} €")
    diff_indirekte = indirekte_gesamt - globalcube_jahr['indirekte']
    print(f"  Differenz:             {diff_indirekte:>15,.2f} € ({diff_indirekte/globalcube_jahr['indirekte']*100:+.2f}%)")
    
    # Berechnung
    db1 = umsatz - einsatz
    db2 = db1 - variable
    db3 = db2 - direkte
    be = db3 - indirekte_gesamt
    
    print(f"\n" + "=" * 100)
    print("Berechnung:")
    print("=" * 100)
    print(f"Umsatz:              {umsatz:>15,.2f} €")
    print(f"Einsatz:             {einsatz:>15,.2f} €")
    print(f"DB1:                 {db1:>15,.2f} €")
    print(f"Variable Kosten:     {variable:>15,.2f} €")
    print(f"DB2:                 {db2:>15,.2f} €")
    print(f"Direkte Kosten:      {direkte:>15,.2f} €")
    print(f"DB3:                 {db3:>15,.2f} €")
    print(f"  Globalcube DB3:    {globalcube_jahr['db3']:>15,.2f} €")
    diff_db3 = db3 - globalcube_jahr['db3']
    print(f"  Differenz DB3:      {diff_db3:>15,.2f} € ({diff_db3/globalcube_jahr['db3']*100:+.2f}%)")
    print(f"Indirekte Kosten:    {indirekte_gesamt:>15,.2f} €")
    print(f"Betriebsergebnis:    {be:>15,.2f} €")
    print(f"  Globalcube BE:     {globalcube_jahr['be']:>15,.2f} €")
    diff_be = be - globalcube_jahr['be']
    print(f"  Differenz BE:       {diff_be:>15,.2f} € ({diff_be/globalcube_jahr['be']*100:+.2f}%)")
