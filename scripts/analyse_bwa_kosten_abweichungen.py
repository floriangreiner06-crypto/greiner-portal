"""
Analyse: BWA Kosten-Abweichungen zwischen DRIVE und Global Cube
Vergleich: Deggendorf Stellantis und Landau - Dezember 2025
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

# Kopie der Funktion (ohne Flask-Abhängigkeit)
def build_firma_standort_filter(firma: str, standort: str):
    firma_filter_umsatz = ""
    firma_filter_einsatz = ""
    firma_filter_kosten = ""
    standort_name = "Alle"

    if firma == '0' and standort == '2':
        firma = '1'
    elif firma == '0' and standort == '1':
        standort = 'deg-both'

    if standort == 'deg-both':
        firma_filter_umsatz = "AND ((branch_number = 1 AND subsidiary_to_company_ref = 1) OR (branch_number = 2 AND subsidiary_to_company_ref = 2))"
        firma_filter_einsatz = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2)"
        firma_filter_kosten = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2)"
        standort_name = "Deggendorf (Stellantis+Hyundai)"
    elif firma == '1':
        firma_filter_umsatz = "AND subsidiary_to_company_ref = 1"
        firma_filter_einsatz = "AND subsidiary_to_company_ref = 1"
        firma_filter_kosten = "AND subsidiary_to_company_ref = 1"
        standort_name = "Stellantis (DEG+LAN)"
        if standort == '1':
            firma_filter_umsatz += " AND branch_number = 1"
            firma_filter_einsatz += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
            # TAG171: Fix - Kosten nach branch_number filtern, nicht nach 6. Ziffer!
            firma_filter_kosten += " AND branch_number = 1"
            standort_name = "Deggendorf"
        elif standort == '2':
            firma_filter_umsatz += " AND branch_number = 3"
            firma_filter_einsatz += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
            # TAG171: Fix - Kosten nach branch_number filtern, nicht nach 6. Ziffer!
            firma_filter_kosten += " AND branch_number = 3"
            standort_name = "Landau"
    elif firma == '2':
        firma_filter_umsatz = "AND subsidiary_to_company_ref = 2"
        firma_filter_einsatz = "AND subsidiary_to_company_ref = 2"
        firma_filter_kosten = "AND subsidiary_to_company_ref = 2"
        standort_name = "Hyundai"

    return firma_filter_umsatz, firma_filter_einsatz, firma_filter_kosten, standort_name

print("=" * 100)
print("ANALYSE: BWA Kosten-Abweichungen - Deggendorf Stellantis vs. Landau")
print("Zeitraum: Dezember 2025")
print("=" * 100)

# Zeitraum: Dezember 2025
monat = 12
jahr = 2025
datum_von = f"{jahr}-{monat:02d}-01"
datum_bis = f"{jahr+1}-01-01"

guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"

with db_session() as conn:
    cursor = conn.cursor()
    
    # 1. Deggendorf Stellantis
    print("\n" + "=" * 100)
    print("1. DEGGENDORF STELLANTIS")
    print("=" * 100)
    
    firma_filter_umsatz, firma_filter_einsatz, firma_filter_kosten, standort_name = build_firma_standort_filter('1', '1')
    print(f"\nFilter: {standort_name}")
    print(f"Umsatz-Filter: {firma_filter_umsatz}")
    print(f"Einsatz-Filter: {firma_filter_einsatz}")
    print(f"Kosten-Filter: {firma_filter_kosten}")
    
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
    variable_deg = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
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
    direkte_deg = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
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
    indirekte_deg = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    print(f"\nKosten-Positionen (DRIVE):")
    print(f"  Variable Kosten: {variable_deg:,.2f} €")
    print(f"  Direkte Kosten: {direkte_deg:,.2f} €")
    print(f"  Indirekte Kosten: {indirekte_deg:,.2f} €")
    print(f"  Summe Kosten: {variable_deg + direkte_deg + indirekte_deg:,.2f} €")
    
    # 2. Landau
    print("\n" + "=" * 100)
    print("2. LANDAU")
    print("=" * 100)
    
    firma_filter_umsatz, firma_filter_einsatz, firma_filter_kosten, standort_name = build_firma_standort_filter('1', '2')
    print(f"\nFilter: {standort_name}")
    print(f"Umsatz-Filter: {firma_filter_umsatz}")
    print(f"Einsatz-Filter: {firma_filter_einsatz}")
    print(f"Kosten-Filter: {firma_filter_kosten}")
    
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
    variable_lan = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
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
    direkte_lan = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
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
    indirekte_lan = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    print(f"\nKosten-Positionen (DRIVE):")
    print(f"  Variable Kosten: {variable_lan:,.2f} €")
    print(f"  Direkte Kosten: {direkte_lan:,.2f} €")
    print(f"  Indirekte Kosten: {indirekte_lan:,.2f} €")
    print(f"  Summe Kosten: {variable_lan + direkte_lan + indirekte_lan:,.2f} €")
    
    # Vergleich mit Screenshots
    print("\n" + "=" * 100)
    print("VERGLEICH MIT SCREENSHOTS")
    print("=" * 100)
    
    # Global Cube Werte (aus Screenshots)
    gc_deg_variable = -42934  # Aus Screenshot
    gc_deg_direkte = -140392
    gc_deg_indirekte = -66054
    gc_deg_summe = gc_deg_variable + gc_deg_direkte + gc_deg_indirekte
    
    gc_lan_variable = -5706
    gc_lan_direkte = -38724
    gc_lan_indirekte = -33758
    gc_lan_summe = gc_lan_variable + gc_lan_direkte + gc_lan_indirekte
    
    print(f"\nDeggendorf Stellantis:")
    print(f"  Variable Kosten:")
    print(f"    DRIVE: {variable_deg:,.2f} €")
    print(f"    Global Cube: {gc_deg_variable:,.2f} €")
    print(f"    Differenz: {variable_deg - gc_deg_variable:,.2f} €")
    
    print(f"  Direkte Kosten:")
    print(f"    DRIVE: {direkte_deg:,.2f} €")
    print(f"    Global Cube: {gc_deg_direkte:,.2f} €")
    print(f"    Differenz: {direkte_deg - gc_deg_direkte:,.2f} €")
    
    print(f"  Indirekte Kosten:")
    print(f"    DRIVE: {indirekte_deg:,.2f} €")
    print(f"    Global Cube: {gc_deg_indirekte:,.2f} €")
    print(f"    Differenz: {indirekte_deg - gc_deg_indirekte:,.2f} €")
    
    print(f"\nLandau:")
    print(f"  Variable Kosten:")
    print(f"    DRIVE: {variable_lan:,.2f} €")
    print(f"    Global Cube: {gc_lan_variable:,.2f} €")
    print(f"    Differenz: {variable_lan - gc_lan_variable:,.2f} €")
    
    print(f"  Direkte Kosten:")
    print(f"    DRIVE: {direkte_lan:,.2f} €")
    print(f"    Global Cube: {gc_lan_direkte:,.2f} €")
    print(f"    Differenz: {direkte_lan - gc_lan_direkte:,.2f} €")
    
    print(f"  Indirekte Kosten:")
    print(f"    DRIVE: {indirekte_lan:,.2f} €")
    print(f"    Global Cube: {gc_lan_indirekte:,.2f} €")
    print(f"    Differenz: {indirekte_lan - gc_lan_indirekte:,.2f} €")
    
    # Prüfe, ob Kosten falsch zugeordnet werden
    print("\n" + "=" * 100)
    print("ANALYSE: Mögliche Fehlzuordnungen")
    print("=" * 100)
    
    # Prüfe Konten, die möglicherweise falsch gefiltert werden
    print("\nPrüfe Konten mit 6. Ziffer '1' und '2' für Deggendorf/Landau:")
    
    # Deggendorf: Sollte 6. Ziffer '1' haben
    cursor.execute(convert_placeholders(f"""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 6, 1) as ziffer_6,
            COUNT(*) as anzahl,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as summe
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND subsidiary_to_company_ref = 1
          {guv_filter}
        GROUP BY substr(CAST(nominal_account_number AS TEXT), 6, 1)
        ORDER BY ziffer_6
    """), (datum_von, datum_bis))
    
    print("\nStellantis Kosten nach 6. Ziffer:")
    for row in cursor.fetchall():
        r = row_to_dict(row)
        print(f"  6. Ziffer '{r['ziffer_6']}': {r['anzahl']} Buchungen, Summe: {r['summe']:,.2f} €")

