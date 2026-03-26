#!/usr/bin/env python3
"""
Findet die Zinskosten-Konten in loco_journal_accountings anhand der Banken:
Stellantis Bank, Santander Bank, Genobank (Belastungen/Zinsen).
Suchbegriffe in posting_text, contra_account_text, free_form_accounting_text.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.db_connection import get_db
from api.db_utils import get_guv_filter

# Geschäftsjahr 2024/25 für Auswertung
VON = "2024-09-01"
BIS = "2025-09-01"

BANK_SUCHBEGRIFFE = [
    "santander",
    "stellantis",
    "genobank",
    "genossenschaft",  # Genobank = Genossenschaftsbank
    "zins",
]

def main():
    guv = get_guv_filter()
    conn = get_db()
    cur = conn.cursor()

    # 1) Alle Buchungen, bei denen in Textfeldern eine der Banken/Zins vorkommt
    #    → gruppiert nach nominal_account_number, Summe SOLL (Aufwand)
    conds = " OR ".join([
        f"(posting_text ILIKE %s OR contra_account_text ILIKE %s OR COALESCE(free_form_accounting_text, '') ILIKE %s)"
        for _ in BANK_SUCHBEGRIFFE
    ])
    params = []
    for s in BANK_SUCHBEGRIFFE:
        params.extend([f"%{s}%", f"%{s}%", f"%{s}%"])

    sql = f"""
        SELECT
            nominal_account_number AS konto,
            COUNT(*) AS anzahl,
            SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 AS soll_eur,
            SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 AS haben_eur
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND ({conds})
          {guv}
        GROUP BY nominal_account_number
        ORDER BY nominal_account_number
    """
    cur.execute(sql, [VON, BIS] + params)
    rows = cur.fetchall()

    print("=" * 70)
    print("Zinskosten-Konten (Belastungen von Stellantis Bank, Santander, Genobank)")
    print("Suchbegriffe in posting_text / contra_account_text / free_form_accounting_text:")
    print("  " + ", ".join(BANK_SUCHBEGRIFFE))
    print(f"Zeitraum: {VON} bis {BIS}")
    print("=" * 70)

    if not rows:
        print("Keine Buchungen gefunden, die einen der Suchbegriffe enthalten.")
        # 2) Fallback: Alle Konten 89xxxx und 49xxxx mit Buchungen (SOLL) im Zeitraum anzeigen
        print("\n--- Alle Aufwands-Konten 89xxxx und 49xxxx mit Buchungen (VJ) ---")
        cur.execute(f"""
            SELECT
                nominal_account_number AS konto,
                COUNT(*) AS anzahl,
                SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 AS soll_eur
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND (nominal_account_number BETWEEN 890000 AND 899999
                   OR nominal_account_number BETWEEN 490000 AND 499999)
              {guv}
            GROUP BY nominal_account_number
            HAVING SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) > 0
            ORDER BY soll_eur DESC
            LIMIT 50
        """, (VON, BIS))
        fallback = cur.fetchall()
        for r in fallback:
            print(f"  Konto {r[0]}: {r[1]} Belege, SOLL summe = {r[2]:,.0f} €")
        conn.close()
        return

    gesamt_soll = 0.0
    for r in rows:
        konto, anzahl, soll_eur, haben_eur = r[0], r[1], float(r[2] or 0), float(r[3] or 0)
        gesamt_soll += soll_eur
        print(f"  Konto {konto}: {anzahl} Belege  |  SOLL (Aufwand): {soll_eur:,.0f} €  |  Haben: {haben_eur:,.0f} €")

    print("-" * 70)
    print(f"  Summe SOLL (Aufwand) über alle gefundenen Konten: {gesamt_soll:,.0f} €")

    # Nur Aufwandskonten (Zinskosten): 7xxxxx (5- oder 6-stellig), 89xxxx, 49xxxx
    def ist_aufwand(k):
        if k is None:
            return False
        k = int(k)
        if 70000 <= k <= 79999 or 700000 <= k <= 799999:
            return True   # Aufwand 7xx
        if 890000 <= k <= 899999:
            return True   # Zinsen und ähnliche Aufwendungen
        if 490000 <= k <= 499999:
            return True   # Umlagen (z. B. Zinsen)
        return False

    aufwand_rows = [r for r in rows if ist_aufwand(r[0])]
    summe_aufwand = sum(float(r[2] or 0) for r in aufwand_rows)
    print()
    print("--- Nur Aufwandskonten (7xxxx, 89xxxx, 49xxxx) = Zinskosten G&V ---")
    if aufwand_rows:
        for r in sorted(aufwand_rows, key=lambda x: -abs(float(x[2] or 0))):
            print(f"  Konto {r[0]}: {r[1]} Belege  |  SOLL: {float(r[2] or 0):,.0f} €")
        print(f"  → Summe Zinskosten (Aufwand): {summe_aufwand:,.0f} €")
    else:
        print("  Keine Buchungen auf Aufwandskonten mit diesen Suchbegriffen.")
    print()
    print("→ Diese Aufwandskonten für Zinskosten im Gewinnzone-Script verwenden.")
    conn.close()


if __name__ == "__main__":
    main()
