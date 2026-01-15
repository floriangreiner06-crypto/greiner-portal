#!/usr/bin/env python3
"""
Detaillierte Analyse: Einsatz und Variable Kosten
Identifiziert die genauen Ursachen der Differenzen
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_connection import get_db
from decimal import Decimal
from collections import defaultdict

def main():
    conn = get_db()
    cursor = conn.cursor()
    
    print("="*100)
    print("DETAILLIERTE ANALYSE: EINSATZ UND VARIABLE KOSTEN")
    print("="*100)
    
    datum_von_ytd = '2025-09-01'
    datum_bis = '2026-01-01'
    
    # Filter für Gesamtbetrieb
    firma_filter_einsatz = """AND (
            ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
            OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
            OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
        )"""
    
    firma_filter_kosten = "AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2)) OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1))"
    
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    
    # 1. EINSATZ - Aufschlüsselung nach Standort/Firma
    print("\n" + "="*100)
    print("1. EINSATZ - AUFSCHLÜSSELUNG")
    print("="*100)
    
    # Deggendorf Stellantis
    query_deg_stellantis = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
          {guv_filter}
    """
    cursor.execute(query_deg_stellantis, (datum_von_ytd, datum_bis))
    deg_stellantis = Decimal(str(cursor.fetchone()[0] or 0))
    
    # Landau
    query_landau = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND (branch_number = 3 AND subsidiary_to_company_ref = 1)
          {guv_filter}
    """
    cursor.execute(query_landau, (datum_von_ytd, datum_bis))
    landau = Decimal(str(cursor.fetchone()[0] or 0))
    
    # Hyundai
    query_hyundai = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
          {guv_filter}
    """
    cursor.execute(query_hyundai, (datum_von_ytd, datum_bis))
    hyundai = Decimal(str(cursor.fetchone()[0] or 0))
    
    gesamt = deg_stellantis + landau + hyundai
    
    print(f"\nDeggendorf Stellantis: {deg_stellantis:>15,.2f} €")
    print(f"Landau:                 {landau:>15,.2f} €")
    print(f"Hyundai:               {hyundai:>15,.2f} €")
    print(f"{'='*50}")
    print(f"GESAMT:                {gesamt:>15,.2f} €")
    print(f"GlobalCube:            {9191864.00:>15,.2f} €")
    print(f"Differenz:             {gesamt - Decimal('9191864.00'):>15,.2f} €")
    
    # 2. EINSATZ - Top Konten
    print("\n" + "="*100)
    print("2. EINSATZ - TOP 20 KONTEN (nach Betrag)")
    print("="*100)
    
    query_top_konten = f"""
        SELECT 
            nominal_account_number,
            COUNT(*) as anzahl,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) / 100.0 as wert,
            subsidiary_to_company_ref,
            branch_number
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          {firma_filter_einsatz}
          {guv_filter}
        GROUP BY nominal_account_number, subsidiary_to_company_ref, branch_number
        ORDER BY ABS(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)) DESC
        LIMIT 20
    """
    cursor.execute(query_top_konten, (datum_von_ytd, datum_bis))
    top_konten = cursor.fetchall()
    
    print(f"\n{'Konto':<10} {'Wert':>15} {'Anzahl':>8} {'Subs':>5} {'Branch':>7}")
    print("-" * 50)
    for row in top_konten:
        konto = row[0]
        wert = Decimal(str(row[2] or 0))
        anzahl = row[1]
        subs = row[3]
        branch = row[4]
        print(f"{konto:<10} {wert:>15,.2f} {anzahl:>8} {subs:>5} {branch:>7}")
    
    # 3. VARIABLE KOSTEN - Aufschlüsselung
    print("\n" + "="*100)
    print("3. VARIABLE KOSTEN - AUFSCHLÜSSELUNG")
    print("="*100)
    
    query_variable = f"""
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
    cursor.execute(query_variable, (datum_von_ytd, datum_bis))
    variable_gesamt = Decimal(str(cursor.fetchone()[0] or 0))
    
    print(f"\nDRIVE Variable Kosten:  {variable_gesamt:>15,.2f} €")
    print(f"GlobalCube:              {304268.00:>15,.2f} €")
    print(f"Differenz:               {variable_gesamt - Decimal('304268.00'):>15,.2f} €")
    
    # Variable Kosten nach Kontenbereichen
    print("\n" + "="*100)
    print("4. VARIABLE KOSTEN - NACH KONTENBEREICHEN")
    print("="*100)
    
    bereiche = [
        ('415100-415199', 415100, 415199),
        ('435500-435599', 435500, 435599),
        ('455000-456999 (KST!=0)', 455000, 456999, True),  # Mit KST-Filter
        ('487000-487099 (KST!=0)', 487000, 487099, True),  # Mit KST-Filter
        ('491000-497899', 491000, 497899),
        ('891000-891099', 891000, 891099),
    ]
    
    print(f"\n{'Bereich':<30} {'Wert':>15}")
    print("-" * 50)
    summe = Decimal('0')
    for bereich_info in bereiche:
        if len(bereich_info) == 3:
            name, von, bis = bereich_info
            kst_filter = ""
        else:
            name, von, bis, _ = bereich_info
            kst_filter = "AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0'"
        
        query_bereich = f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN {von} AND {bis}
              {kst_filter}
              {firma_filter_kosten}
              {guv_filter}
        """
        cursor.execute(query_bereich, (datum_von_ytd, datum_bis))
        wert = Decimal(str(cursor.fetchone()[0] or 0))
        summe += wert
        print(f"{name:<30} {wert:>15,.2f} €")
    
    print("-" * 50)
    print(f"{'GESAMT':<30} {summe:>15,.2f} €")
    
    conn.close()

if __name__ == '__main__':
    main()
