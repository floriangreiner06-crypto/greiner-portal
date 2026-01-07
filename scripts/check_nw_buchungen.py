#!/usr/bin/env python3
"""
Prüft NW-Buchungen in journal_accountings (mit/ohne vehicle_reference)
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
    print(f"NW-BUCHUNGEN ANALYSE - {von} bis {bis}")
    print(f"{'='*60}\n")
    
    with locosoft_session() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # 1. Gesamt NW-Buchungen
        cur.execute("""
            SELECT 
                COUNT(*) as anzahl_buchungen,
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
            FROM journal_accountings
            WHERE accounting_date >= %s
              AND accounting_date < %s
              AND nominal_account_number BETWEEN 810000 AND 819999
        """, (von, bis))
        row = cur.fetchone()
        print(f"[1] Gesamt NW-Buchungen:")
        print(f"   {row['anzahl_buchungen'] or 0} Buchungen, {row['umsatz'] or 0:,.2f} EUR Umsatz")
        
        # 2. Mit/ohne vehicle_reference
        cur.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE vehicle_reference IS NOT NULL AND vehicle_reference != '') as mit_ref,
                COUNT(*) FILTER (WHERE vehicle_reference IS NULL OR vehicle_reference = '') as ohne_ref,
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) FILTER 
                    (WHERE vehicle_reference IS NOT NULL AND vehicle_reference != '') / 100.0 as umsatz_mit_ref,
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) FILTER 
                    (WHERE vehicle_reference IS NULL OR vehicle_reference = '') / 100.0 as umsatz_ohne_ref
            FROM journal_accountings
            WHERE accounting_date >= %s
              AND accounting_date < %s
              AND nominal_account_number BETWEEN 810000 AND 819999
        """, (von, bis))
        row = cur.fetchone()
        print(f"\n[2] Aufschlüsselung:")
        print(f"   Mit vehicle_reference: {row['mit_ref'] or 0} Buchungen, {row['umsatz_mit_ref'] or 0:,.2f} EUR")
        print(f"   Ohne vehicle_reference: {row['ohne_ref'] or 0} Buchungen, {row['umsatz_ohne_ref'] or 0:,.2f} EUR")
        
        # 3. Top 10 Buchungen nach Datum
        cur.execute("""
            SELECT 
                accounting_date,
                COUNT(*) as buchungen,
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz,
                COUNT(DISTINCT vehicle_reference) FILTER (WHERE vehicle_reference IS NOT NULL AND vehicle_reference != '') as stueck_mit_ref
            FROM journal_accountings
            WHERE accounting_date >= %s
              AND accounting_date < %s
              AND nominal_account_number BETWEEN 810000 AND 819999
            GROUP BY accounting_date
            ORDER BY accounting_date
            LIMIT 10
        """, (von, bis))
        rows = cur.fetchall()
        print(f"\n[3] Top 10 Tage (nach Datum):")
        for r in rows:
            print(f"   {r['accounting_date']}: {r['buchungen']} Buchungen, {r['umsatz']:,.2f} EUR, {r['stueck_mit_ref'] or 0} Stück mit Ref")
        
        # 4. Beispiel-Buchungen (erste 5)
        cur.execute("""
            SELECT 
                accounting_date,
                nominal_account_number,
                vehicle_reference,
                posting_text,
                CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END / 100.0 as betrag
            FROM journal_accountings
            WHERE accounting_date >= %s
              AND accounting_date < %s
              AND nominal_account_number BETWEEN 810000 AND 819999
            ORDER BY accounting_date, document_number
            LIMIT 5
        """, (von, bis))
        rows = cur.fetchall()
        print(f"\n[4] Beispiel-Buchungen (erste 5):")
        for r in rows:
            ref = r['vehicle_reference'] or '(kein Ref)'
            print(f"   {r['accounting_date']} | Konto {r['nominal_account_number']} | {ref} | {r['betrag']:,.2f} EUR | {r['posting_text'][:50]}")
        
        cur.close()
    
    print(f"\n{'='*60}\n")

if __name__ == '__main__':
    main()

