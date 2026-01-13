#!/usr/bin/env python3
"""
Analysiere verbleibende Differenzen und identifiziere betroffene Konten
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.db_connection import get_db
from api.db_utils import row_to_dict
import psycopg2.extras

def analysiere_differenzen():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("=" * 80)
    print("ANALYSE: VERBLEIBENDE DIFFERENZEN")
    print("=" * 80)
    print()
    
    # 1. GESAMTBETRIEB EINSATZ YTD
    print("1. GESAMTBETRIEB EINSATZ YTD (Sep-Dez 2025)")
    print("-" * 80)
    print("DRIVE: 9.223.769,97 €")
    print("GlobalCube: 9.191.864,00 €")
    print("Differenz: +31.905,97 €")
    print()
    
    # Filter für Gesamtbetrieb Einsatz
    firma_filter_einsatz = """AND (
        ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
        OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
        OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
    )"""
    
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%G&V-Abschluss%')"
    
    # Top 20 Konten nach Wert (YTD)
    query = f"""
        SELECT 
            nominal_account_number,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= '2025-09-01' AND accounting_date < '2026-01-01'
          AND nominal_account_number BETWEEN 700000 AND 799999
          {firma_filter_einsatz}
          {guv_filter}
        GROUP BY nominal_account_number
        ORDER BY ABS(wert) DESC
        LIMIT 20;
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print("Top 20 Konten (nach Betrag):")
    total = 0
    for row in rows:
        konto = row['nominal_account_number']
        anzahl = row['anzahl']
        wert = row['wert']
        total += wert
        print(f"  {konto}: {anzahl:4d} Buchungen, {wert:>15,.2f} €")
    print(f"  Summe Top 20: {total:>15,.2f} €")
    print()
    
    # 2. LANDAU VARIABLE KOSTEN YTD
    print("2. LANDAU VARIABLE KOSTEN YTD (Sep-Dez 2025)")
    print("-" * 80)
    print("DRIVE: 25.905,53 €")
    print("GlobalCube: 39.162,00 €")
    print("Differenz: -13.256,47 €")
    print()
    
    # Filter für Landau Variable Kosten
    variable_kosten_filter = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
    
    variable_kosten_where = """
          AND (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR (nominal_account_number BETWEEN 455000 AND 456999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            OR (nominal_account_number BETWEEN 487000 AND 487099
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            OR nominal_account_number BETWEEN 491000 AND 497899
            OR nominal_account_number BETWEEN 891000 AND 891099
          )"""
    
    query2 = f"""
        SELECT 
            nominal_account_number,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= '2025-09-01' AND accounting_date < '2026-01-01'
          {variable_kosten_where}
          {variable_kosten_filter}
          {guv_filter}
        GROUP BY nominal_account_number
        ORDER BY ABS(wert) DESC
        LIMIT 20;
    """
    
    cursor.execute(query2)
    rows2 = cursor.fetchall()
    
    print("Top 20 Konten (nach Betrag):")
    total2 = 0
    for row in rows2:
        konto = row['nominal_account_number']
        anzahl = row['anzahl']
        wert = row['wert']
        total2 += wert
        print(f"  {konto}: {anzahl:4d} Buchungen, {wert:>15,.2f} €")
    print(f"  Summe Top 20: {total2:>15,.2f} €")
    print()
    
    # 3. Prüfe, welche Konten möglicherweise fehlen
    print("3. MÖGLICHE FEHLENDE KONTEN")
    print("-" * 80)
    print("Prüfe, ob es Konten gibt, die GlobalCube enthält, aber DRIVE nicht:")
    print()
    
    # Prüfe 8910xx für Landau (sollte enthalten sein)
    query3 = f"""
        SELECT 
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= '2025-09-01' AND accounting_date < '2026-01-01'
          AND nominal_account_number BETWEEN 891000 AND 891099
          AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'
          AND subsidiary_to_company_ref = 1
          {guv_filter};
    """
    
    cursor.execute(query3)
    result3 = cursor.fetchone()
    print(f"8910xx für Landau (6. Ziffer='2'): {result3['anzahl']} Buchungen, {result3['wert']:,.2f} €")
    print()
    
    conn.close()

if __name__ == '__main__':
    analysiere_differenzen()
