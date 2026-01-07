#!/usr/bin/env python3
"""
Debug-Script: Prüft NW-Umsatz in FIBU vs. Locosoft Stückzahlen
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

def main():
    monat = 1  # Januar
    jahr = 2026
    von = f"{jahr}-{monat:02d}-01"
    bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"
    
    print(f"\n{'='*60}")
    print(f"NW-UMSATZ DEBUG - {von} bis {bis}")
    print(f"{'='*60}\n")
    
    # 1. Prüfe NW-Umsatz OHNE Filter
    print("[1] NW-Umsatz OHNE Filter (alle Firmen/Standorte):")
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(convert_placeholders("""
            SELECT 
                COUNT(*) as anzahl_buchungen,
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz,
                MIN(accounting_date) as min_datum,
                MAX(accounting_date) as max_datum
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 810000 AND 819999
        """), (von, bis))
        row = cursor.fetchone()
        if row:
            r = row_to_dict(row)
            print(f"   Buchungen: {r.get('anzahl_buchungen', 0)}")
            print(f"   Umsatz: {r.get('umsatz', 0):,.2f} EUR")
            print(f"   Datum-Spanne: {r.get('min_datum')} bis {r.get('max_datum')}")
    
    # 2. Prüfe NW-Umsatz MIT subsidiary_to_company_ref Filter
    print("\n[2] NW-Umsatz MIT subsidiary_to_company_ref = 1 (Stellantis):")
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(convert_placeholders("""
            SELECT 
                COUNT(*) as anzahl_buchungen,
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz,
                COUNT(DISTINCT branch_number) as anzahl_branches
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 810000 AND 819999
              AND subsidiary_to_company_ref = 1
        """), (von, bis))
        row = cursor.fetchone()
        if row:
            r = row_to_dict(row)
            print(f"   Buchungen: {r.get('anzahl_buchungen', 0)}")
            print(f"   Umsatz: {r.get('umsatz', 0):,.2f} EUR")
            print(f"   Branch-Nummern: {r.get('anzahl_branches', 0)}")
    
    # 3. Prüfe nach branch_number
    print("\n[3] NW-Umsatz nach branch_number aufgeschlüsselt:")
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(convert_placeholders("""
            SELECT 
                branch_number,
                COUNT(*) as anzahl_buchungen,
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 810000 AND 819999
              AND subsidiary_to_company_ref = 1
            GROUP BY branch_number
            ORDER BY branch_number
        """), (von, bis))
        rows = cursor.fetchall()
        for row in rows:
            r = row_to_dict(row)
            print(f"   Branch {r.get('branch_number')}: {r.get('anzahl_buchungen', 0)} Buchungen, {r.get('umsatz', 0):,.2f} EUR")
    
    # 4. Prüfe nach Konten (erste 10)
    print("\n[4] Top 10 NW-Konten (nach Umsatz):")
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(convert_placeholders("""
            SELECT 
                nominal_account_number as konto,
                COUNT(*) as anzahl_buchungen,
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 810000 AND 819999
            GROUP BY nominal_account_number
            ORDER BY ABS(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END)) DESC
            LIMIT 10
        """), (von, bis))
        rows = cursor.fetchall()
        for row in rows:
            r = row_to_dict(row)
            print(f"   Konto {r.get('konto')}: {r.get('anzahl_buchungen', 0)} Buchungen, {r.get('umsatz', 0):,.2f} EUR")
    
    # 5. Prüfe Umlage-Konten
    print("\n[5] Umlage-Konten (817051, 827051, etc.):")
    umlage_konten = [817051, 827051, 837051, 847051]
    umlage_konten_str = ','.join(map(str, umlage_konten))
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(convert_placeholders(f"""
            SELECT 
                nominal_account_number as konto,
                COUNT(*) as anzahl_buchungen,
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number IN ({umlage_konten_str})
            GROUP BY nominal_account_number
        """), (von, bis))
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                r = row_to_dict(row)
                print(f"   Konto {r.get('konto')}: {r.get('anzahl_buchungen', 0)} Buchungen, {r.get('umsatz', 0):,.2f} EUR")
        else:
            print("   Keine Umlage-Buchungen gefunden")
    
    # 6. Prüfe ob Buchungen in anderen Monaten sind
    print("\n[6] NW-Umsatz in anderen Monaten (Dez 2025, Feb 2026):")
    for test_monat, test_jahr in [(12, 2025), (2, 2026)]:
        test_von = f"{test_jahr}-{test_monat:02d}-01"
        test_bis = f"{test_jahr}-{test_monat+1:02d}-01" if test_monat < 12 else f"{test_jahr+1}-01-01"
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_placeholders("""
                SELECT 
                    COUNT(*) as anzahl_buchungen,
                    SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND nominal_account_number BETWEEN 810000 AND 819999
                  AND nominal_account_number NOT IN (817051, 827051, 837051, 847051)
            """), (test_von, test_bis))
            row = cursor.fetchone()
            if row:
                r = row_to_dict(row)
                if r.get('anzahl_buchungen', 0) > 0:
                    print(f"   {test_monat}/{test_jahr}: {r.get('anzahl_buchungen', 0)} Buchungen, {r.get('umsatz', 0):,.2f} EUR")
    
    print(f"\n{'='*60}\n")

if __name__ == '__main__':
    main()

