#!/usr/bin/env python3
"""
Debug-Script: Prüft NW-Umsatz direkt in Locosoft
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.db_utils import locosoft_session
import psycopg2.extras

def main():
    monat = 1  # Januar
    jahr = 2026
    von = f"{jahr}-{monat:02d}-01"
    bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"
    
    print(f"\n{'='*60}")
    print(f"NW-UMSATZ DEBUG LOCOSOFT - {von} bis {bis}")
    print(f"{'='*60}\n")
    
    # Prüfe direkt in Locosoft
    with locosoft_session() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # NW-Umsatz OHNE Filter
        cur.execute("""
            SELECT 
                COUNT(*) as anzahl_buchungen,
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz,
                MIN(accounting_date) as min_datum,
                MAX(accounting_date) as max_datum
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 810000 AND 819999
        """, (von, bis))
        row = cur.fetchone()
        print(f"[1] NW-Umsatz in Locosoft (OHNE Filter):")
        print(f"   Buchungen: {row['anzahl_buchungen']}")
        umsatz = row['umsatz'] or 0
        print(f"   Umsatz: {umsatz:,.2f} EUR")
        if row['min_datum']:
            print(f"   Datum-Spanne: {row['min_datum']} bis {row['max_datum']}")
        else:
            print(f"   Keine Buchungen gefunden!")
        
        # NW-Umsatz OHNE Umlage-Konten
        cur.execute("""
            SELECT 
                COUNT(*) as anzahl_buchungen,
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 810000 AND 819999
              AND nominal_account_number NOT IN (817051, 827051, 837051, 847051)
        """, (von, bis))
        row = cur.fetchone()
        print(f"\n[2] NW-Umsatz OHNE Umlage-Konten:")
        print(f"   Buchungen: {row['anzahl_buchungen']}")
        umsatz = row['umsatz'] or 0
        print(f"   Umsatz: {umsatz:,.2f} EUR")
        
        # Top 10 NW-Konten
        cur.execute("""
            SELECT 
                nominal_account_number as konto,
                COUNT(*) as anzahl_buchungen,
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 810000 AND 819999
              AND nominal_account_number NOT IN (817051, 827051, 837051, 847051)
            GROUP BY nominal_account_number
            ORDER BY ABS(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END)) DESC
            LIMIT 10
        """, (von, bis))
        rows = cur.fetchall()
        print(f"\n[3] Top 10 NW-Konten (OHNE Umlage):")
        for r in rows:
            print(f"   Konto {r['konto']}: {r['anzahl_buchungen']} Buchungen, {r['umsatz']:,.2f} EUR")
        
        # Prüfe ob Buchungen in anderen Monaten sind
        print(f"\n[4] NW-Umsatz in anderen Monaten (Dez 2025, Feb 2026):")
        for test_monat, test_jahr in [(12, 2025), (2, 2026)]:
            test_von = f"{test_jahr}-{test_monat:02d}-01"
            test_bis = f"{test_jahr}-{test_monat+1:02d}-01" if test_monat < 12 else f"{test_jahr+1}-01-01"
            cur.execute("""
                SELECT 
                    COUNT(*) as anzahl_buchungen,
                    SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
                FROM journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 810000 AND 819999
                  AND nominal_account_number NOT IN (817051, 827051, 837051, 847051)
            """, (test_von, test_bis))
            row = cur.fetchone()
            if row and row['anzahl_buchungen'] > 0:
                umsatz = row['umsatz'] or 0
                print(f"   {test_monat}/{test_jahr}: {row['anzahl_buchungen']} Buchungen, {umsatz:,.2f} EUR")
        
        cur.close()
    
    print(f"\n{'='*60}\n")

if __name__ == '__main__':
    main()

