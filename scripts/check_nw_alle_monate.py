#!/usr/bin/env python3
"""
Prüft NW-Buchungen in allen Monaten (Dez 2025, Jan 2026, Feb 2026)
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.db_utils import locosoft_session
import psycopg2.extras

def main():
    print(f"\n{'='*60}")
    print(f"NW-BUCHUNGEN ALLE MONATE")
    print(f"{'='*60}\n")
    
    monate = [
        ('2025-12-01', '2026-01-01', 'Dezember 2025'),
        ('2026-01-01', '2026-02-01', 'Januar 2026'),
        ('2026-02-01', '2026-03-01', 'Februar 2026'),
    ]
    
    with locosoft_session() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        for von, bis, name in monate:
            cur.execute("""
                SELECT 
                    COUNT(*) as anzahl_buchungen,
                    SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz,
                    COUNT(DISTINCT vehicle_reference) FILTER (WHERE vehicle_reference IS NOT NULL AND vehicle_reference != '') as stueck_mit_ref,
                    COUNT(*) FILTER (WHERE nominal_account_number IN (817051, 827051, 837051, 847051)) as umlage_buchungen
                FROM journal_accountings
                WHERE accounting_date >= %s
                  AND accounting_date < %s
                  AND nominal_account_number BETWEEN 810000 AND 819999
            """, (von, bis))
            row = cur.fetchone()
            
            print(f"{name}:")
            print(f"   {row['anzahl_buchungen'] or 0} Buchungen, {row['umsatz'] or 0:,.2f} EUR Umsatz")
            print(f"   {row['stueck_mit_ref'] or 0} Stück mit vehicle_reference")
            print(f"   {row['umlage_buchungen'] or 0} Umlage-Buchungen (817051, etc.)")
            
            # Top 5 Konten
            cur.execute("""
                SELECT 
                    nominal_account_number,
                    COUNT(*) as buchungen,
                    SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
                FROM journal_accountings
                WHERE accounting_date >= %s
                  AND accounting_date < %s
                  AND nominal_account_number BETWEEN 810000 AND 819999
                GROUP BY nominal_account_number
                ORDER BY ABS(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END)) DESC
                LIMIT 5
            """, (von, bis))
            rows = cur.fetchall()
            if rows:
                print(f"   Top Konten:")
                for r in rows:
                    print(f"      {r['nominal_account_number']}: {r['buchungen']} Buchungen, {r['umsatz']:,.2f} EUR")
            print()
        
        cur.close()
    
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()

