#!/usr/bin/env python3
"""
Analyse Werkstatt Einsatz/Umsatz Verhältnis
============================================
TAG 140: Berechnet rollierenden FIBU-Durchschnitt für kalkulatorischen Einsatz

Zweck: Statt der geschätzten 25-40% Formel den tatsächlichen
       FIBU-Durchschnitt der letzten 12 Monate verwenden.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db_connection import get_db
from api.db_utils import row_to_dict
from datetime import datetime, timedelta

def analyse_werkstatt_einsatz():
    """Analysiert historische Werkstatt Einsatz/Umsatz Quoten."""

    # Letzte 12 Monate
    heute = datetime.now()
    start = (heute - timedelta(days=365)).strftime('%Y-%m-%d')
    ende = heute.strftime('%Y-%m-%d')

    conn = get_db()
    cursor = conn.cursor()

    # Werkstatt-Konten: 74xxxx = Einsatz (Soll), 84xxxx = Umsatz (Haben)
    cursor.execute('''
        SELECT
            TO_CHAR(accounting_date, 'YYYY-MM') as monat,
            SUM(CASE WHEN nominal_account_number BETWEEN 740000 AND 749999
                     AND debit_or_credit = 'S' THEN posted_value
                     WHEN nominal_account_number BETWEEN 740000 AND 749999
                     AND debit_or_credit = 'H' THEN -posted_value
                     ELSE 0 END) / 100.0 as einsatz,
            SUM(CASE WHEN nominal_account_number BETWEEN 840000 AND 849999
                     AND debit_or_credit = 'H' THEN posted_value
                     WHEN nominal_account_number BETWEEN 840000 AND 849999
                     AND debit_or_credit = 'S' THEN -posted_value
                     ELSE 0 END) / 100.0 as umsatz
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
        GROUP BY TO_CHAR(accounting_date, 'YYYY-MM')
        ORDER BY monat DESC
    ''', (start, ende))

    print("=" * 65)
    print("WERKSTATT EINSATZ/UMSATZ ANALYSE - Letzte 12 Monate")
    print("=" * 65)
    print()
    print("Monat       | Einsatz       | Umsatz        | Einsatz%")
    print("-" * 65)

    total_einsatz = 0
    total_umsatz = 0
    monate = []

    for row in cursor.fetchall():
        r = row_to_dict(row)
        einsatz = float(r['einsatz'] or 0)
        umsatz = float(r['umsatz'] or 0)
        quote = (einsatz / umsatz * 100) if umsatz > 0 else 0

        monat = r['monat']
        print("{:12} | {:>12,.0f}€ | {:>12,.0f}€ | {:>6.1f}%".format(
            monat, einsatz, umsatz, quote
        ))

        total_einsatz += einsatz
        total_umsatz += umsatz
        monate.append({'monat': monat, 'einsatz': einsatz, 'umsatz': umsatz, 'quote': quote})

    avg_quote = (total_einsatz / total_umsatz * 100) if total_umsatz > 0 else 0

    print("-" * 65)
    print("{:12} | {:>12,.0f}€ | {:>12,.0f}€ | {:>6.1f}%".format(
        "GESAMT", total_einsatz, total_umsatz, avg_quote
    ))
    print()
    print("=" * 65)
    print("ERGEBNIS:")
    print("=" * 65)
    print()
    print("  Rollierender FIBU-Durchschnitt: {:.1f}% Einsatz vom Umsatz".format(avg_quote))
    print()
    print("  Aktuelle Formel: 25-40% (basierend auf Produktivität)")
    print("  Empfehlung: {:.0f}% als fixen Wert ODER dynamisch aus FIBU".format(avg_quote))
    print()

    # Zusätzlich: Aufschlüsselung nach Einsatz-Konten
    print("-" * 65)
    print("EINSATZ-AUFSCHLÜSSELUNG nach Konten:")
    print("-" * 65)

    cursor.execute('''
        SELECT
            nominal_account_number as konto,
            SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value
                     ELSE -posted_value END) / 100.0 as betrag
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 740000 AND 749999
        GROUP BY nominal_account_number
        ORDER BY betrag DESC
        LIMIT 15
    ''', (start, ende))

    print()
    print("Konto   | Betrag")
    print("-" * 35)
    for row in cursor.fetchall():
        r = row_to_dict(row)
        print("{:>6} | {:>12,.0f}€".format(r['konto'], float(r['betrag'] or 0)))

    conn.close()

    return {
        'avg_quote': avg_quote,
        'total_einsatz': total_einsatz,
        'total_umsatz': total_umsatz,
        'monate': monate
    }


def analyse_nur_2025():
    """Analysiert nur 2025 (ohne Dez 2024 Ausreißer)."""

    conn = get_db()
    cursor = conn.cursor()

    # Nur 2025
    cursor.execute('''
        SELECT
            SUM(CASE WHEN nominal_account_number BETWEEN 740000 AND 749999
                     AND debit_or_credit = 'S' THEN posted_value
                     WHEN nominal_account_number BETWEEN 740000 AND 749999
                     AND debit_or_credit = 'H' THEN -posted_value
                     ELSE 0 END) / 100.0 as einsatz,
            SUM(CASE WHEN nominal_account_number BETWEEN 840000 AND 849999
                     AND debit_or_credit = 'H' THEN posted_value
                     WHEN nominal_account_number BETWEEN 840000 AND 849999
                     AND debit_or_credit = 'S' THEN -posted_value
                     ELSE 0 END) / 100.0 as umsatz
        FROM loco_journal_accountings
        WHERE accounting_date >= '2025-01-01'
          AND accounting_date < '2025-12-28'
    ''')

    row = cursor.fetchone()
    r = row_to_dict(row)
    einsatz = float(r['einsatz'] or 0)
    umsatz = float(r['umsatz'] or 0)
    quote = (einsatz / umsatz * 100) if umsatz > 0 else 0

    print()
    print("=" * 65)
    print("WERKSTATT 2025 (Jan-Dez, ohne Dez 2024 Ausreißer):")
    print("=" * 65)
    print("  Einsatz: {:>12,.0f} €".format(einsatz))
    print("  Umsatz:  {:>12,.0f} €".format(umsatz))
    print("  Quote:   {:>12.1f}%".format(quote))
    print()

    # Aufschlüsselung Lohn vs Teile
    cursor.execute('''
        SELECT
            CASE
                WHEN nominal_account_number BETWEEN 740000 AND 742999 THEN 'Lohn'
                WHEN nominal_account_number BETWEEN 743000 AND 746999 THEN 'Teile'
                ELSE 'Sonstiges'
            END as kategorie,
            SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as betrag
        FROM loco_journal_accountings
        WHERE accounting_date >= '2025-01-01'
          AND accounting_date < '2025-12-28'
          AND nominal_account_number BETWEEN 740000 AND 749999
        GROUP BY 1
        ORDER BY betrag DESC
    ''')

    print("Aufschlüsselung Werkstatt-Einsatz 2025:")
    print("-" * 50)
    for row in cursor.fetchall():
        r = row_to_dict(row)
        betrag = float(r['betrag'] or 0)
        anteil = (betrag / umsatz * 100) if umsatz > 0 else 0
        print("  {:<12} {:>12,.0f} € ({:>5.1f}% vom Umsatz)".format(
            r['kategorie'], betrag, anteil
        ))

    conn.close()

    return {'quote': quote, 'einsatz': einsatz, 'umsatz': umsatz}


if __name__ == '__main__':
    result = analyse_werkstatt_einsatz()
    result_2025 = analyse_nur_2025()
