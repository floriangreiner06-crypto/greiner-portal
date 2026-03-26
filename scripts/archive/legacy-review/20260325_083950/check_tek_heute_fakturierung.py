#!/usr/bin/env python3
"""
Diagnose: Tägliche Fakturierungen (TEK Heute/Vortag) – warum null?
Prüft ob NW/GW-Umsatz für Heute und Vortag in Locosoft und Spiegel vorhanden ist.
"""
import sys
import os
sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')

from datetime import date, timedelta

def main():
    heute = date.today()
    vortag = heute - timedelta(days=1)
    heute_str = heute.isoformat()
    vortag_str = vortag.isoformat()
    morgen_str = (heute + timedelta(days=1)).isoformat()

    print("=" * 60)
    print("TEK Heute/Vortag – Datenquellen-Check (NW/GW)")
    print("=" * 60)
    print(f"Heute:  {heute_str} (Buchungsdatum)")
    print(f"Vortag: {vortag_str}")
    print()

    # 1) Locosoft direkt (journal_accountings) – das nutzt die TEK-API für Heute/Vortag
    print("[1] Locosoft direkt (journal_accountings) – Quelle für TEK Heute/Vortag")
    try:
        from api.db_utils import locosoft_session
        import psycopg2.extras
        with locosoft_session() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            for label, von, bis in [
                ("Heute", heute_str, morgen_str),
                ("Vortag", vortag_str, heute_str),
            ]:
                cur.execute("""
                    SELECT
                        COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz_nw,
                        COALESCE(SUM(CASE WHEN nominal_account_number BETWEEN 820000 AND 829999 AND debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz_gw
                    FROM journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND nominal_account_number BETWEEN 810000 AND 819999
                """, (von, bis))
                r_nw = cur.fetchone()
                cur.execute("""
                    SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz_gw
                    FROM journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND nominal_account_number BETWEEN 820000 AND 829999
                """, (von, bis))
                r_gw = cur.fetchone()
                umsatz_nw = float(r_nw['umsatz_nw'] or 0)
                umsatz_gw = float(r_gw['umsatz_gw'] or 0)
                print(f"  {label}: NW={umsatz_nw:,.2f} €, GW={umsatz_gw:,.2f} €")
            # Anzahl Buchungen pro Tag
            cur.execute("""
                SELECT accounting_date::date as d, COUNT(*) as n
                FROM journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND (nominal_account_number BETWEEN 810000 AND 819999 OR nominal_account_number BETWEEN 820000 AND 829999)
                GROUP BY accounting_date::date
                ORDER BY d
            """, (vortag_str, morgen_str))
            rows = cur.fetchall()
            print("  Buchungsanzahl NW+GW pro Tag:", [f"{r['d']}: {r['n']}" for r in rows] if rows else "keine")
    except Exception as e:
        print(f"  Fehler: {e}")
        import traceback
        traceback.print_exc()

    # 2) Spiegel drive_portal (loco_journal_accountings)
    print()
    print("[2] Portal-Spiegel (loco_journal_accountings) – gleicher Zeitraum")
    try:
        from api.db_connection import get_db
        from api.db_utils import row_to_dict
        conn = get_db()
        cur = conn.cursor()
        for label, von, bis in [
            ("Heute", heute_str, morgen_str),
            ("Vortag", vortag_str, heute_str),
        ]:
            cur.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz_nw
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 810000 AND 819999
            """, (von, bis))
            r_nw = cur.fetchone()
            cur.execute("""
                SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz_gw
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 820000 AND 829999
            """, (von, bis))
            r_gw = cur.fetchone()
            umsatz_nw = float((r_nw[0] if r_nw else 0) or 0)
            umsatz_gw = float((r_gw[0] if r_gw else 0) or 0)
            print(f"  {label}: NW={umsatz_nw:,.2f} €, GW={umsatz_gw:,.2f} €")
        conn.close()
    except Exception as e:
        print(f"  Fehler: {e}")
        import traceback
        traceback.print_exc()

    # 3) Rechnungen (invoices) – Fakturierung im Sinne Kundenzentrale
    print()
    print("[3] Fakturierung (invoices) – Rechnungsdatum NW/GW (invoice_type 7,8)")
    try:
        from api.db_utils import locosoft_session
        import psycopg2.extras
        with locosoft_session() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT DATE(invoice_date) as d,
                       SUM(CASE WHEN invoice_type IN (7, 8) THEN total_gross ELSE 0 END) as verkauf,
                       COUNT(*) FILTER (WHERE invoice_type IN (7, 8)) as anzahl
                FROM invoices
                WHERE invoice_date >= %s AND invoice_date < %s
                  AND is_canceled = false AND total_gross > 0
                GROUP BY DATE(invoice_date)
                ORDER BY d
            """, (vortag_str, morgen_str))
            rows = cur.fetchall()
            for r in rows:
                print(f"  {r['d']}: Verkauf (7,8) = {float(r['verkauf'] or 0):,.2f} €, Anzahl Rechnungen = {r['anzahl'] or 0}")
            if not rows:
                print("  Keine Rechnungen mit Typ 7/8 in dem Zeitraum.")
    except Exception as e:
        print(f"  Fehler: {e}")

    print()
    print("Fazit: Wenn [1] Heute/Vortag = 0, liefert die TEK-API null (Buchungen fehlen in Locosoft oder erst mit Verzögerung).")
    print("       Wenn [2] Werte hat, aber [1] nicht: Heute-Daten könnten aus Spiegel genutzt werden (Fallback).")

if __name__ == "__main__":
    main()
