#!/usr/bin/env python3
"""
Detaillierte Analyse der direkten Kosten für Gesamtbetrieb Dezember 2025
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.db_connection import get_db, convert_placeholders
from api.db_utils import row_to_dict
import psycopg2.extras

def analysiere_direkte_kosten():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Monat Dezember 2025
    datum_von = '2025-12-01'
    datum_bis = '2026-01-01'
    
    # YTD Sep-Dez 2025
    ytd_datum_von = '2025-09-01'
    ytd_datum_bis = '2026-01-01'
    
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%G&V-Abschluss%')"
    
    print("=" * 80)
    print("DETAILLIERTE ANALYSE: DIREKTE KOSTEN GESAMTBETRIEB")
    print("=" * 80)
    print()
    
    # Filter für Gesamtbetrieb
    firma_filter_kosten = "AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2)) OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1))"
    
    # 1. Gesamtbetrieb mit TAG 177 Logik (411xxx + 489xxx + 410021 ausgeschlossen)
    query_tag177 = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
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
          {firma_filter_kosten}
          {guv_filter}
    """
    
    cursor.execute(convert_placeholders(query_tag177), (datum_von, datum_bis))
    monat_tag177 = cursor.fetchone()['wert'] or 0
    
    cursor.execute(convert_placeholders(query_tag177), (ytd_datum_von, ytd_datum_bis))
    ytd_tag177 = cursor.fetchone()['wert'] or 0
    
    print("1. TAG 177 Logik (411xxx + 489xxx + 410021 ausgeschlossen):")
    print(f"   Monat Dezember 2025: {monat_tag177:,.2f} €")
    print(f"   YTD Sep-Dez 2025:    {ytd_tag177:,.2f} €")
    print()
    
    # 2. Ohne Ausschluss von 411xxx + 410021 (nur 489xxx ausgeschlossen)
    query_tag182 = f"""
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
    
    cursor.execute(convert_placeholders(query_tag182), (datum_von, datum_bis))
    monat_tag182 = cursor.fetchone()['wert'] or 0
    
    cursor.execute(convert_placeholders(query_tag182), (ytd_datum_von, ytd_datum_bis))
    ytd_tag182 = cursor.fetchone()['wert'] or 0
    
    print("2. TAG 182 Logik (nur 489xxx ausgeschlossen, 411xxx + 410021 enthalten):")
    print(f"   Monat Dezember 2025: {monat_tag182:,.2f} €")
    print(f"   YTD Sep-Dez 2025:    {ytd_tag182:,.2f} €")
    print()
    
    # 3. Ausgeschlossene Konten analysieren
    query_411xxx = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 411000 AND 411999
          {firma_filter_kosten}
          {guv_filter}
    """
    
    cursor.execute(convert_placeholders(query_411xxx), (datum_von, datum_bis))
    monat_411xxx = cursor.fetchone()['wert'] or 0
    
    cursor.execute(convert_placeholders(query_411xxx), (ytd_datum_von, ytd_datum_bis))
    ytd_411xxx = cursor.fetchone()['wert'] or 0
    
    query_410021 = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number = 410021
          {firma_filter_kosten}
          {guv_filter}
    """
    
    cursor.execute(convert_placeholders(query_410021), (datum_von, datum_bis))
    monat_410021 = cursor.fetchone()['wert'] or 0
    
    cursor.execute(convert_placeholders(query_410021), (ytd_datum_von, ytd_datum_bis))
    ytd_410021 = cursor.fetchone()['wert'] or 0
    
    query_489xxx = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 489000 AND 489999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          {firma_filter_kosten}
          {guv_filter}
    """
    
    cursor.execute(convert_placeholders(query_489xxx), (datum_von, datum_bis))
    monat_489xxx = cursor.fetchone()['wert'] or 0
    
    cursor.execute(convert_placeholders(query_489xxx), (ytd_datum_von, ytd_datum_bis))
    ytd_489xxx = cursor.fetchone()['wert'] or 0
    
    print("3. Ausgeschlossene Konten (TAG 177):")
    print(f"   411xxx (Monat): {monat_411xxx:,.2f} €")
    print(f"   411xxx (YTD):   {ytd_411xxx:,.2f} €")
    print(f"   410021 (Monat): {monat_410021:,.2f} €")
    print(f"   410021 (YTD):   {ytd_410021:,.2f} €")
    print(f"   489xxx (Monat): {monat_489xxx:,.2f} €")
    print(f"   489xxx (YTD):   {ytd_489xxx:,.2f} €")
    print(f"   Summe (Monat):  {monat_411xxx + monat_410021 + monat_489xxx:,.2f} €")
    print(f"   Summe (YTD):    {ytd_411xxx + ytd_410021 + ytd_489xxx:,.2f} €")
    print()
    
    # 4. Vergleich mit GlobalCube
    print("4. Vergleich mit GlobalCube:")
    print()
    print("   Monat Dezember 2025:")
    print(f"   DRIVE (TAG 177): {monat_tag177:,.2f} €")
    print(f"   DRIVE (TAG 182): {monat_tag182:,.2f} €")
    print(f"   GlobalCube:      189.866,00 €")
    print(f"   Differenz TAG 177: {monat_tag177 - 189866.00:,.2f} € ({((monat_tag177 - 189866.00) / 189866.00 * 100):+.2f}%)")
    print(f"   Differenz TAG 182: {monat_tag182 - 189866.00:,.2f} € ({((monat_tag182 - 189866.00) / 189866.00 * 100):+.2f}%)")
    print()
    print("   YTD Sep-Dez 2025:")
    print(f"   DRIVE (TAG 177): {ytd_tag177:,.2f} €")
    print(f"   DRIVE (TAG 182): {ytd_tag182:,.2f} €")
    print(f"   GlobalCube:      659.229,00 €")
    print(f"   Differenz TAG 177: {ytd_tag177 - 659229.00:,.2f} € ({((ytd_tag177 - 659229.00) / 659229.00 * 100):+.2f}%)")
    print(f"   Differenz TAG 182: {ytd_tag182 - 659229.00:,.2f} € ({((ytd_tag182 - 659229.00) / 659229.00 * 100):+.2f}%)")
    print()
    
    # 5. Berechnung: Welche Logik ist korrekt?
    print("5. Analyse:")
    print()
    monat_diff_tag177 = abs(monat_tag177 - 189866.00)
    monat_diff_tag182 = abs(monat_tag182 - 189866.00)
    ytd_diff_tag177 = abs(ytd_tag177 - 659229.00)
    ytd_diff_tag182 = abs(ytd_tag182 - 659229.00)
    
    print(f"   Monat - TAG 177 Differenz: {monat_diff_tag177:,.2f} €")
    print(f"   Monat - TAG 182 Differenz: {monat_diff_tag182:,.2f} €")
    if monat_diff_tag177 < monat_diff_tag182:
        print(f"   → TAG 177 ist näher an GlobalCube (um {monat_diff_tag182 - monat_diff_tag177:,.2f} €)")
    else:
        print(f"   → TAG 182 ist näher an GlobalCube (um {monat_diff_tag177 - monat_diff_tag182:,.2f} €)")
    print()
    print(f"   YTD - TAG 177 Differenz: {ytd_diff_tag177:,.2f} €")
    print(f"   YTD - TAG 182 Differenz: {ytd_diff_tag182:,.2f} €")
    if ytd_diff_tag177 < ytd_diff_tag182:
        print(f"   → TAG 177 ist näher an GlobalCube (um {ytd_diff_tag182 - ytd_diff_tag177:,.2f} €)")
    else:
        print(f"   → TAG 182 ist näher an GlobalCube (um {ytd_diff_tag177 - ytd_diff_tag182:,.2f} €)")
    print()
    
    conn.close()

if __name__ == '__main__':
    analysiere_direkte_kosten()
