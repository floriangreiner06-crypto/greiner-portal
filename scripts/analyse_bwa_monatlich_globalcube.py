#!/usr/bin/env python3
"""
Monat-für-Monat-Vergleich: DRIVE BWA vs. Globalcube
====================================================
Identifiziert in welchen Monaten die Abweichungen entstehen.
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders
from datetime import datetime, timedelta
import calendar

# Globalcube Werte aus CSV (manuell eintragen)
# Format: {monat: {'db3': wert, 'indirekte': wert, 'be': wert}}
globalcube_werte = {
    # Jahr per Aug./2025 (kumuliert)
    8: {
        'db3': 2801501.76,
        'indirekte': 2479617.08,
        'be': 321884.68
    },
    # Monat Aug./2025
    'aug_2025': {
        'db3': None,  # TODO: Aus CSV extrahieren
        'indirekte': None,
        'be': 689679.69
    }
}

def berechne_bwa_monat(conn, jahr: int, monat: int, kumuliert: bool = False):
    """Berechnet BWA-Werte für einen Monat oder kumuliert."""
    cursor = conn.cursor()
    
    if kumuliert:
        # Kumuliert: Von Sept. Vorjahr bis Ende Monat
        datum_von = f"{jahr-1}-09-01"
        datum_bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"
    else:
        # Nur Monat
        datum_von = f"{jahr}-{monat:02d}-01"
        if monat == 12:
            datum_bis = f"{jahr+1}-01-01"
        else:
            datum_bis = f"{jahr}-{monat+1:02d}-01"
    
    firma_filter_umsatz = ''
    firma_filter_einsatz = ''
    firma_filter_kosten = ''
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    
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
                AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
          )
          {firma_filter_kosten}
          {guv_filter}
    """), (datum_von, datum_bis))
    indirekte = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Berechnungen
    db1 = umsatz - einsatz
    db2 = db1 - variable
    db3 = db2 - direkte
    be = db3 - indirekte
    
    return {
        'umsatz': umsatz,
        'einsatz': einsatz,
        'db1': db1,
        'variable': variable,
        'db2': db2,
        'direkte': direkte,
        'db3': db3,
        'indirekte': indirekte,
        'be': be,
        'datum_von': datum_von,
        'datum_bis': datum_bis
    }

def analysiere_direkte_kosten_detailed(conn, datum_von: str, datum_bis: str):
    """Analysiert direkte Kosten nach Kontenbereichen."""
    cursor = conn.cursor()
    
    firma_filter_kosten = ''
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    
    # Direkte Kosten nach Kontenbereichen
    kontenbereiche = [
        ('4100x-4110x', '410000', '411099'),
        ('4150x (ohne 4151xx)', '415000', '415099'),
        ('4300x-4320x', '430000', '432099'),
        ('4360x', '436000', '436099'),
        ('4690x', '469000', '469099'),
        ('4890x', '489000', '489099'),
        ('Sonstige 40xxxx-48xxxx', None, None)  # Wird separat berechnet
    ]
    
    print(f"\n  Direkte Kosten - Detailliert:")
    print(f"  {'Kontenbereich':<30} {'Wert':>15} {'%':>8}")
    
    gesamt_direkte = 0
    for name, von_konto, bis_konto in kontenbereiche:
        if von_konto and bis_konto:
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN %s AND %s
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
            """), (datum_von, datum_bis, von_konto, bis_konto))
        else:
            # Gesamt direkte Kosten
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
            wert = float(row_to_dict(cursor.fetchone())['wert'] or 0)
            gesamt_direkte = wert
            print(f"  {'GESAMT':<30} {wert:>15,.2f} € {'100.0':>8}%")
            continue
        
        wert = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        if gesamt_direkte > 0:
            prozent = (wert / gesamt_direkte) * 100
        else:
            prozent = 0
        print(f"  {name:<30} {wert:>15,.2f} € {prozent:>7.2f}%")
    
    return gesamt_direkte

print("=" * 120)
print("MONAT-FÜR-MONAT-VERGLEICH: DRIVE BWA vs. Globalcube")
print("=" * 120)

jahr = 2025
monate = list(range(9, 13)) + list(range(1, 9))  # Sep 2024 - Aug 2025

with db_session() as conn:
    print(f"\n{'Monat':<12} {'DB3 DRIVE':>15} {'DB3 GC':>15} {'Diff DB3':>15} {'Ind. DRIVE':>15} {'Ind. GC':>15} {'Diff Ind.':>15} {'BE DRIVE':>15} {'BE GC':>15} {'Diff BE':>15}")
    print("-" * 120)
    
    kumuliert_drive = {'db3': 0, 'indirekte': 0, 'be': 0}
    kumuliert_gc = {'db3': 0, 'indirekte': 0, 'be': 0}
    
    for monat in monate:
        jahr_aktuell = jahr if monat >= 1 else jahr - 1
        
        # Monatswert
        monat_wert = berechne_bwa_monat(conn, jahr_aktuell, monat, kumuliert=False)
        
        # Kumulierter Wert
        kum_wert = berechne_bwa_monat(conn, jahr, 8 if monat == 8 else monat, kumuliert=True)
        
        monat_name = calendar.month_abbr[monat]
        print(f"{monat_name} {jahr_aktuell:<4} "
              f"{monat_wert['db3']:>15,.2f} {'':>15} "
              f"{monat_wert['indirekte']:>15,.2f} {'':>15} "
              f"{monat_wert['be']:>15,.2f} {'':>15}")
        
        # Kumuliert (nur für Aug. 2025)
        if monat == 8:
            print(f"  KUMULIERT:   "
                  f"{kum_wert['db3']:>15,.2f} {globalcube_werte[8]['db3']:>15,.2f} "
                  f"{kum_wert['db3'] - globalcube_werte[8]['db3']:>15,.2f} "
                  f"{kum_wert['indirekte']:>15,.2f} {globalcube_werte[8]['indirekte']:>15,.2f} "
                  f"{kum_wert['indirekte'] - globalcube_werte[8]['indirekte']:>15,.2f} "
                  f"{kum_wert['be']:>15,.2f} {globalcube_werte[8]['be']:>15,.2f} "
                  f"{kum_wert['be'] - globalcube_werte[8]['be']:>15,.2f}")
            
            # Detaillierte Analyse für kumulierten Zeitraum
            print(f"\n{'='*120}")
            print("DETAILLIERTE ANALYSE: Jahr per Aug./2025 (kumuliert)")
            print(f"{'='*120}")
            print(f"Zeitraum: {kum_wert['datum_von']} - {kum_wert['datum_bis']}")
            print(f"\nKomponenten:")
            print(f"  Umsatz:              {kum_wert['umsatz']:>15,.2f} €")
            print(f"  Einsatz:             {kum_wert['einsatz']:>15,.2f} €")
            print(f"  DB1:                 {kum_wert['db1']:>15,.2f} €")
            print(f"  Variable Kosten:     {kum_wert['variable']:>15,.2f} €")
            print(f"  DB2:                 {kum_wert['db2']:>15,.2f} €")
            print(f"  Direkte Kosten:      {kum_wert['direkte']:>15,.2f} €")
            print(f"  DB3:                 {kum_wert['db3']:>15,.2f} €")
            print(f"    Globalcube DB3:    {globalcube_werte[8]['db3']:>15,.2f} €")
            diff_db3 = kum_wert['db3'] - globalcube_werte[8]['db3']
            print(f"    Differenz DB3:      {diff_db3:>15,.2f} € ({diff_db3/globalcube_werte[8]['db3']*100:+.2f}%)")
            print(f"  Indirekte Kosten:    {kum_wert['indirekte']:>15,.2f} €")
            print(f"    Globalcube Ind.:    {globalcube_werte[8]['indirekte']:>15,.2f} €")
            diff_ind = kum_wert['indirekte'] - globalcube_werte[8]['indirekte']
            print(f"    Differenz Ind.:      {diff_ind:>15,.2f} € ({diff_ind/globalcube_werte[8]['indirekte']*100:+.2f}%)")
            print(f"  Betriebsergebnis:    {kum_wert['be']:>15,.2f} €")
            print(f"    Globalcube BE:      {globalcube_werte[8]['be']:>15,.2f} €")
            diff_be = kum_wert['be'] - globalcube_werte[8]['be']
            print(f"    Differenz BE:        {diff_be:>15,.2f} € ({diff_be/globalcube_werte[8]['be']*100:+.2f}%)")
            
            # Detaillierte Analyse direkte Kosten
            analysiere_direkte_kosten_detailed(conn, kum_wert['datum_von'], kum_wert['datum_bis'])

print(f"\n{'='*120}")
print("HINWEIS: Globalcube-Werte müssen manuell aus CSV extrahiert werden!")
print("CSV-Datei: /opt/greiner-portal/docs/F.03 BWA Vorjahres-Vergleich (17).csv")
print(f"{'='*120}")
