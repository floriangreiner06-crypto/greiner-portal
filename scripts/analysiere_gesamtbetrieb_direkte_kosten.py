#!/usr/bin/env python3
"""
Analysiere direkte Kosten für Gesamtbetrieb Dezember 2025
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.db_connection import get_db
from api.db_utils import row_to_dict
import psycopg2.extras

def analysiere_direkte_kosten():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    datum_von = '2025-12-01'
    datum_bis = '2026-01-01'
    
    # Filter für Gesamtbetrieb (firma='0', standort='0')
    # Aus build_firma_standort_filter:
    firma_filter_kosten = "AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2)) OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1))"
    
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%G&V-Abschluss%')"
    
    print("=" * 80)
    print("ANALYSE: DIREKTE KOSTEN GESAMTBETRIEB DEZEMBER 2025")
    print("=" * 80)
    print()
    
    # 1. Gesamtbetrieb mit Filter
    query = """
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
          """ + firma_filter_kosten + """
          """ + guv_filter
    cursor.execute(query, (datum_von, datum_bis))
    result = cursor.fetchone()
    wert_gesamt = result['wert'] or 0
    print(f"1. Gesamtbetrieb (mit Filter): {wert_gesamt:,.2f} €")
    print()
    
    # 2. Aufschlüsselung nach Standort/Firma
    # Deggendorf Stellantis (6. Ziffer='1', subsidiary=1)
    query = """
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
          AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'
          AND subsidiary_to_company_ref = 1
          """ + guv_filter
    cursor.execute(query, (datum_von, datum_bis))
    result = cursor.fetchone()
    wert_deg_stellantis = result['wert'] or 0
    print(f"2. Deggendorf Stellantis (6. Ziffer='1', subsidiary=1): {wert_deg_stellantis:,.2f} €")
    
    # Deggendorf Hyundai (6. Ziffer='1', subsidiary=2)
    query = """
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
          AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'
          AND subsidiary_to_company_ref = 2
          """ + guv_filter
    cursor.execute(query, (datum_von, datum_bis))
    result = cursor.fetchone()
    wert_deg_hyundai = result['wert'] or 0
    print(f"3. Deggendorf Hyundai (6. Ziffer='1', subsidiary=2): {wert_deg_hyundai:,.2f} €")
    
    # Landau (6. Ziffer='2', subsidiary=1)
    query = """
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
          AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'
          AND subsidiary_to_company_ref = 1
          """ + guv_filter
    cursor.execute(query, (datum_von, datum_bis))
    result = cursor.fetchone()
    wert_landau = result['wert'] or 0
    print(f"4. Landau (6. Ziffer='2', subsidiary=1): {wert_landau:,.2f} €")
    print()
    
    summe_einzel = wert_deg_stellantis + wert_deg_hyundai + wert_landau
    print(f"5. Summe Einzelbetriebe: {summe_einzel:,.2f} €")
    print(f"   (Deggendorf Stellantis + Deggendorf Hyundai + Landau)")
    print()
    print(f"6. Vergleich:")
    print(f"   Gesamtbetrieb (mit Filter): {wert_gesamt:,.2f} €")
    print(f"   Summe Einzelbetriebe:       {summe_einzel:,.2f} €")
    print(f"   Differenz:                  {wert_gesamt - summe_einzel:,.2f} €")
    print()
    
    # 7. GlobalCube Referenz
    print("7. GlobalCube Referenz (Dezember 2025): 189.866,00 €")
    print(f"   DRIVE Gesamtbetrieb:        {wert_gesamt:,.2f} €")
    print(f"   Differenz:                  {wert_gesamt - 189866.00:,.2f} €")
    print()
    
    # 8. Prüfe, ob es Konten gibt, die nicht erfasst werden
    query = """
        SELECT COUNT(*) as anzahl, 
               COALESCE(SUM(
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
          AND NOT (
            (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2))
            OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1)
          )
          """ + guv_filter
    cursor.execute(query, (datum_von, datum_bis))
    result = cursor.fetchone()
    wert_nicht_erfasst = result['wert'] or 0
    anzahl_nicht_erfasst = result['anzahl'] or 0
    print(f"8. Nicht erfasste Konten (außerhalb Filter):")
    print(f"   Anzahl: {anzahl_nicht_erfasst}")
    print(f"   Wert:   {wert_nicht_erfasst:,.2f} €")
    print()
    
    conn.close()

if __name__ == '__main__':
    analysiere_direkte_kosten()
