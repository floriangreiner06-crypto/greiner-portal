#!/usr/bin/env python3
"""
Debug: Warum zeigt API 728,41€ statt 181.216,91€ für Gesamtbetrieb?
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.db_connection import get_db, convert_placeholders
from api.db_utils import row_to_dict
import psycopg2.extras

def debug_direkte_kosten():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    datum_von = '2025-12-01'
    datum_bis = '2026-01-01'
    
    # Simuliere build_firma_standort_filter für Gesamtbetrieb
    firma = '0'
    standort = '0'
    
    if firma == '0' and standort == '0':
        firma_filter_kosten = "AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2)) OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1))"
    else:
        firma_filter_kosten = ""
    
    # Simuliere direkte_kosten_filter (wie in _berechne_bwa_werte)
    if standort == '2' and firma == '1':
        direkte_kosten_filter = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
    else:
        direkte_kosten_filter = firma_filter_kosten
    
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%G&V-Abschluss%')"
    
    print("=" * 80)
    print("DEBUG: DIREKTE KOSTEN GESAMTBETRIEB DEZEMBER 2025")
    print("=" * 80)
    print()
    print(f"firma: {firma}")
    print(f"standort: {standort}")
    print(f"firma_filter_kosten: {firma_filter_kosten[:100]}...")
    print(f"direkte_kosten_filter: {direkte_kosten_filter[:100]}...")
    print()
    
    # Query wie in _berechne_bwa_werte
    query = f"""
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
          {direkte_kosten_filter}
          {guv_filter}
    """
    
    print("Query (erste 500 Zeichen):")
    print(query[:500])
    print()
    
    # Konvertiere Placeholders
    query_converted = convert_placeholders(query)
    print("Query nach convert_placeholders (erste 500 Zeichen):")
    print(query_converted[:500])
    print()
    print(f"Anzahl %s in Query: {query_converted.count('%s')}")
    print()
    
    # Prüfe, ob es ein Problem mit % in guv_filter gibt
    # Escape % in guv_filter für f-String
    guv_filter_escaped = guv_filter.replace('%', '%%')
    query_escaped = f"""
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
          {direkte_kosten_filter}
          {guv_filter_escaped}
    """
    query_escaped_converted = convert_placeholders(query_escaped)
    print("Query mit escaped guv_filter (erste 500 Zeichen):")
    print(query_escaped_converted[:500])
    print()
    
    # Führe Query aus
    try:
        cursor.execute(query_converted, (datum_von, datum_bis))
        result = cursor.fetchone()
        wert = result['wert'] or 0
        print(f"Ergebnis: {wert:,.2f} €")
        print()
        print(f"Erwartet (SQL direkt): 181.216,91 €")
        print(f"API zeigt: 728,41 €")
        print(f"Differenz: {wert - 728.41:,.2f} €")
    except Exception as e:
        print(f"Fehler: {e}")
        import traceback
        traceback.print_exc()
    
    conn.close()

if __name__ == '__main__':
    debug_direkte_kosten()
