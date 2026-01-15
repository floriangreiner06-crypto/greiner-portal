#!/usr/bin/env python3
"""
Analysiere HABEN-Buchungen (einsatzmindernd) für Gesamtbetrieb Einsatz
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.db_connection import get_db
from api.db_utils import convert_placeholders
import psycopg2.extras

def analysiere_haben_buchungen():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("=" * 80)
    print("ANALYSE: HABEN-BUCHUNGEN (EINSATZMINDERND) - GESAMTBETRIEB EINSATZ")
    print("=" * 80)
    print()
    
    # Top 30 Konten mit HABEN-Buchungen
    query = """
        SELECT 
            nominal_account_number,
            subsidiary_to_company_ref,
            COUNT(*) as anzahl,
            COUNT(CASE WHEN debit_or_credit='H' THEN 1 END) as anzahl_haben,
            COUNT(CASE WHEN debit_or_credit='S' THEN 1 END) as anzahl_soll,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as netto_wert,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='H' THEN posted_value ELSE 0 END
            )/100.0, 0) as haben_wert,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE 0 END
            )/100.0, 0) as soll_wert
        FROM loco_journal_accountings
        WHERE accounting_date >= '2025-09-01' AND accounting_date < '2026-01-01'
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND (
            ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
            OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
            OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
          )
          AND (posting_text IS NULL OR posting_text NOT LIKE '%G&V-Abschluss%')
        GROUP BY nominal_account_number, subsidiary_to_company_ref
        HAVING COUNT(CASE WHEN debit_or_credit='H' THEN 1 END) > 0
        ORDER BY ABS(COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE 0 END
        )/100.0, 0)) DESC
        LIMIT 30;
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print("Top 30 Konten mit HABEN-Buchungen (einsatzmindernd):")
    print("-" * 80)
    print(f"{'Konto':<10} {'Sub':<5} {'HABEN':>15} {'SOLL':>15} {'NETTO':>15} {'Bezeichnung':<50}")
    print("-" * 80)
    
    total_haben = 0
    total_soll = 0
    total_netto = 0
    
    for row in rows:
        konto = row['nominal_account_number']
        subsidiary = row['subsidiary_to_company_ref']
        haben_wert = row['haben_wert']
        soll_wert = row['soll_wert']
        netto_wert = row['netto_wert']
        
        # Kontobezeichnung holen
        cursor2 = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor2.execute(convert_placeholders("""
            SELECT account_description
            FROM loco_nominal_accounts
            WHERE nominal_account_number = %s
              AND subsidiary_to_company_ref = %s
            LIMIT 1
        """), (konto, subsidiary))
        result2 = cursor2.fetchone()
        bezeichnung = result2['account_description'] if result2 and result2.get('account_description') else None
        
        if not bezeichnung:
            # Fallback: Versuche andere subsidiary
            cursor2.execute(convert_placeholders("""
                SELECT account_description
                FROM loco_nominal_accounts
                WHERE nominal_account_number = %s
                LIMIT 1
            """), (konto,))
            result2 = cursor2.fetchone()
            bezeichnung = result2['account_description'] if result2 and result2.get('account_description') else f"Konto {konto}"
        
        total_haben += haben_wert
        total_soll += soll_wert
        total_netto += netto_wert
        
        print(f"{konto:<10} {subsidiary:<5} {haben_wert:>15,.2f} {soll_wert:>15,.2f} {netto_wert:>15,.2f} {bezeichnung[:50]:<50}")
    
    print("-" * 80)
    print(f"{'SUMME':<10} {'':<5} {total_haben:>15,.2f} {total_soll:>15,.2f} {total_netto:>15,.2f}")
    print()
    
    # Gesamtbetrieb Einsatz: Summe aller HABEN-Buchungen
    query2 = """
        SELECT 
            'HABEN-Buchungen (einsatzmindernd)' as typ,
            COUNT(*) as anzahl_buchungen,
            COUNT(DISTINCT nominal_account_number) as anzahl_konten,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='H' THEN posted_value ELSE 0 END
            )/100.0, 0) as haben_wert,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE 0 END
            )/100.0, 0) as soll_wert,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as netto_wert
        FROM loco_journal_accountings
        WHERE accounting_date >= '2025-09-01' AND accounting_date < '2026-01-01'
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND (
            ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
            OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
            OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
          )
          AND (posting_text IS NULL OR posting_text NOT LIKE '%G&V-Abschluss%');
    """
    
    cursor.execute(query2)
    result = cursor.fetchone()
    
    print("=" * 80)
    print("ZUSAMMENFASSUNG:")
    print("=" * 80)
    print(f"Anzahl Buchungen: {result['anzahl_buchungen']:,}")
    print(f"Anzahl Konten: {result['anzahl_konten']}")
    print(f"HABEN-Wert (einsatzmindernd): {result['haben_wert']:,.2f} €")
    print(f"SOLL-Wert (einsatzerhöhend): {result['soll_wert']:,.2f} €")
    print(f"NETTO-Wert (Einsatz): {result['netto_wert']:,.2f} €")
    print()
    netto_wert = float(result['netto_wert'])
    soll_wert = float(result['soll_wert'])
    haben_wert = float(result['haben_wert'])
    globalcube_wert = 9191864.0
    
    print(f"DRIVE Gesamtbetrieb Einsatz: {netto_wert:,.2f} €")
    print(f"GlobalCube Gesamtbetrieb Einsatz: {globalcube_wert:,.2f} €")
    print(f"Differenz: {netto_wert - globalcube_wert:,.2f} €")
    print()
    
    # Prüfe: Wenn HABEN-Buchungen ausgeschlossen werden sollten
    print("=" * 80)
    print("HYPOTHESE: Hersteller-Boni (einsatzmindernd)")
    print("=" * 80)
    print("Wenn HABEN-Buchungen Hersteller-Boni sind, die ausgeschlossen werden sollten:")
    print(f"Einsatz OHNE HABEN-Buchungen (nur SOLL): {soll_wert:,.2f} €")
    print(f"GlobalCube: {globalcube_wert:,.2f} €")
    print(f"Differenz: {soll_wert - globalcube_wert:,.2f} €")
    print()
    print(f"Wenn HABEN-Buchungen Teil des Einsatzes sind (aktuell):")
    print(f"Einsatz MIT HABEN-Buchungen (SOLL - HABEN): {netto_wert:,.2f} €")
    print(f"GlobalCube: {globalcube_wert:,.2f} €")
    print(f"Differenz: {netto_wert - globalcube_wert:,.2f} €")
    print()
    
    conn.close()

if __name__ == '__main__':
    analysiere_haben_buchungen()
