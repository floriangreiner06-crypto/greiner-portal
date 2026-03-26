#!/usr/bin/env python3
"""
Vergleich: Locosoft (Quelle) vs. Portal-Spiegel (loco_journal_accountings) für Februar 2026.
Datenquelle soll identisch sein – prüft 743002, Einsatz gesamt, G&V-Buchungen.

Aufruf: cd /opt/greiner-portal && venv/bin/python3 scripts/vergleiche_tek_locosoft_vs_portal_feb2026.py
"""
import sys
import os
sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')

from datetime import date
from dotenv import load_dotenv
load_dotenv('/opt/greiner-portal/config/.env', override=True)

# Februar 2026
jahr, monat = 2026, 2
von = f"{jahr}-{monat:02d}-01"
bis = f"{jahr}-{monat+1:02d}-01"

# %% damit in execute() kein Placeholder für % entsteht
guv_where = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"

def run_portal_queries(cursor):
    """Portal: loco_journal_accountings (Spiegel)."""
    out = {}
    # 743002
    cursor.execute("""
        SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as wert,
               COUNT(*) as anzahl
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number = 743002
    """, (von, bis))
    row = cursor.fetchone()
    out['743002_wert'] = float(row[0] or 0) if row else 0
    out['743002_anzahl'] = int(row[1] or 0) if row else 0

    # Einsatz 70-79 gesamt (ohne Filter)
    cursor.execute("""
        SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
    """, (von, bis))
    row = cursor.fetchone()
    out['einsatz_70_79'] = float(row[0] or 0) if row else 0

    # Einsatz 70-79 ohne 743002
    cursor.execute("""
        SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND nominal_account_number != 743002
    """, (von, bis))
    row = cursor.fetchone()
    out['einsatz_70_79_ohne_743002'] = float(row[0] or 0) if row else 0

    # Einsatz 70-79 mit G&V-Filter
    cursor.execute(f"""
        SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          {guv_where}
    """, (von, bis))
    row = cursor.fetchone()
    out['einsatz_70_79_mit_guv'] = float(row[0] or 0) if row else 0

    # Umsatz 80-88 (Kern)
    cursor.execute("""
        SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
    """, (von, bis))
    row = cursor.fetchone()
    out['umsatz_80_88'] = float(row[0] or 0) if row else 0

    # Anzahl Zeilen Einsatz im Monat
    cursor.execute("""
        SELECT COUNT(*) FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
    """, (von, bis))
    out['einsatz_zeilen'] = cursor.fetchone()[0] or 0

    return out

def run_locosoft_queries(cursor):
    """Locosoft: journal_accountings (Original-Quelle)."""
    out = {}
    # 743002
    cursor.execute("""
        SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as wert,
               COUNT(*) as anzahl
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number = 743002
    """, (von, bis))
    row = cursor.fetchone()
    out['743002_wert'] = float(row[0] or 0) if row else 0
    out['743002_anzahl'] = int(row[1] or 0) if row else 0

    # Einsatz 70-79 gesamt
    cursor.execute("""
        SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as wert
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
    """, (von, bis))
    row = cursor.fetchone()
    out['einsatz_70_79'] = float(row[0] or 0) if row else 0

    # Einsatz 70-79 ohne 743002
    cursor.execute("""
        SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as wert
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND nominal_account_number != 743002
    """, (von, bis))
    row = cursor.fetchone()
    out['einsatz_70_79_ohne_743002'] = float(row[0] or 0) if row else 0

    # Einsatz 70-79 mit G&V-Filter
    cursor.execute(f"""
        SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as wert
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          {guv_where}
    """, (von, bis))
    row = cursor.fetchone()
    out['einsatz_70_79_mit_guv'] = float(row[0] or 0) if row else 0

    # Umsatz 80-88
    cursor.execute("""
        SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as wert
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
    """, (von, bis))
    row = cursor.fetchone()
    out['umsatz_80_88'] = float(row[0] or 0) if row else 0

    cursor.execute("""
        SELECT COUNT(*) FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
    """, (von, bis))
    out['einsatz_zeilen'] = cursor.fetchone()[0] or 0

    return out

def main():
    from api.db_utils import db_session, locosoft_session

    print("=" * 70)
    print(f"Vergleich Locosoft (Quelle) vs. Portal-Spiegel – Februar 2026 ({von} bis {bis})")
    print("=" * 70)

    portal_data = {}
    try:
        with db_session() as conn:
            cur = conn.cursor()
            portal_data = run_portal_queries(cur)
    except Exception as e:
        print(f"Portal-Fehler: {e}")
        import traceback
        traceback.print_exc()
        return

    loco_data = {}
    try:
        with locosoft_session() as conn:
            cur = conn.cursor()
            loco_data = run_locosoft_queries(cur)
    except Exception as e:
        print(f"Locosoft-Fehler: {e}")
        import traceback
        traceback.print_exc()
        return

    # Tabelle
    print()
    print(f"{'Kennzahl':<35} {'Locosoft':>18} {'Portal':>18} {'Diff':>12}")
    print("-" * 85)

    for key, label in [
        ('743002_wert', '743002 Saldo (€)'),
        ('743002_anzahl', '743002 Buchungsanzahl'),
        ('einsatz_70_79', 'Einsatz 70-79 gesamt (€)'),
        ('einsatz_70_79_ohne_743002', 'Einsatz ohne 743002 (€)'),
        ('einsatz_70_79_mit_guv', 'Einsatz mit G&V-Filter (€)'),
        ('umsatz_80_88', 'Umsatz 80-88/8932 (€)'),
        ('einsatz_zeilen', 'Einsatz Zeilenanzahl'),
    ]:
        lv = loco_data.get(key, 0)
        pv = portal_data.get(key, 0)
        if isinstance(lv, float) and isinstance(pv, float):
            diff = lv - pv
            print(f"{label:<35} {lv:>17,.2f} {pv:>17,.2f} {diff:>+11,.2f}")
        else:
            diff = (lv or 0) - (pv or 0)
            print(f"{label:<35} {lv:>18} {pv:>18} {diff:>+12}")

    # DB1 (Umsatz - Einsatz ohne 743002, mit G&V wie TEK)
    umsatz_l = loco_data.get('umsatz_80_88', 0)
    umsatz_p = portal_data.get('umsatz_80_88', 0)
    einsatz_l = loco_data.get('einsatz_70_79_ohne_743002', 0)
    einsatz_p = portal_data.get('einsatz_70_79_ohne_743002', 0)
    # G&V auch auf Einsatz anwenden für fairen Vergleich
    einsatz_guv_l = loco_data.get('einsatz_70_79_mit_guv', 0)
    einsatz_guv_p = portal_data.get('einsatz_70_79_mit_guv', 0)
    db1_l = umsatz_l - einsatz_guv_l
    db1_p = umsatz_p - einsatz_guv_p
    print("-" * 85)
    print(f"{'DB1 (Umsatz - Einsatz mit G&V) (€)':<35} {db1_l:>17,.2f} {db1_p:>17,.2f} {db1_l - db1_p:>+11,.2f}")

    print()
    if abs(portal_data.get('743002_wert', 0)) < 0.01 and abs(loco_data.get('743002_wert', 0)) > 0.01:
        print(">>> Auffällig: In Locosoft gibt es 743002-Buchungen im Februar, im Portal-Spiegel nicht.")
        print("   → Spiegel könnte unvollständig oder zeitverzögert sein.")
    elif abs(portal_data.get('743002_wert', 0) - loco_data.get('743002_wert', 0)) > 0.01:
        print(">>> 743002 weicht zwischen Locosoft und Portal ab.")
    else:
        print(">>> 743002 in beiden Quellen gleich (inkl. 0).")

    if abs(portal_data.get('einsatz_70_79', 0) - loco_data.get('einsatz_70_79', 0)) > 1:
        print(">>> Einsatz gesamt weicht ab – Datenquelle nicht identisch oder Filter unterschiedlich.")
    else:
        print(">>> Einsatz gesamt stimmt überein (Datenquelle identisch).")

if __name__ == '__main__':
    main()
