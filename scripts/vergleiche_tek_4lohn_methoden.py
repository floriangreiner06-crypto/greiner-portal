#!/usr/bin/env python3
"""
Vergleich: 4-Lohn Werkstatt – zwei Methoden für laufenden Monat

- Method A: Nur Lohn 740xxx, rollierend 6 Monate → Lohnanteil; Einsatz = FIBU-Einsatz (aktuell) + (Umsatz × Lohnanteil)
- Method B: Gesamter Einsatz 74xxxx, rollierend 6 Monate → Einsatz/Umsatz-Quote; Einsatz = Umsatz_aktuell × Quote
  (einfacher: ein Verhältnis, kein Aufteilen in Lohn/Teile/FL)

Verwendet dieselben Filter wie TEK (loco_journal_accountings, BWA-Filter firma=0).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

# BWA-Filter Gesamtsumme (firma=0, standort=0) wie in controlling_api.build_firma_standort_filter
FIRMA_FILTER_UMSATZ = "AND ((branch_number = 1 AND subsidiary_to_company_ref = 1) OR (branch_number = 2 AND subsidiary_to_company_ref = 2) OR (branch_number = 3 AND subsidiary_to_company_ref = 1))"
FIRMA_FILTER_EINSATZ = """AND (
    ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
    OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
    OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
)"""


def main():
    heute = datetime.now()
    # Letzter abgeschlossener Monat (z.B. 1. bis letzter Tag)
    ende_letzter = heute.replace(day=1) - timedelta(days=1)
    von_letzter = ende_letzter.replace(day=1)
    # 6 abgeschlossene Vormonate (für rollierenden Schnitt)
    von_6m = (von_letzter - timedelta(days=180)).replace(day=1)
    bis_6m = von_letzter  # exklusiv: bis 1. des letzten Monats = Ende des 6. Vormonats? Nein.
    # 6 Monate rückwärts: wenn wir im Feb 2026 sind, letzter = Jan 2026; 6 Monate = Aug 2025 - Jan 2026
    von_6m = (von_letzter.replace(day=1) - timedelta(days=1)).replace(day=1)  # Aug 2025
    for _ in range(4):
        von_6m = (von_6m - timedelta(days=1)).replace(day=1)
    # Einfacher: 6 Kalendermonate vor dem aktuellen
    aktueller_monat_start = heute.replace(day=1)
    von_6m = (aktueller_monat_start - timedelta(days=1)).replace(day=1)
    for _ in range(5):
        von_6m = (von_6m - timedelta(days=1)).replace(day=1)
    bis_6m = aktueller_monat_start  # exklusiv

    with db_session() as conn:
        cursor = conn.cursor()

        # 6 Monate: Umsatz 84xxxx (Umsatz-Filter), Einsatz 74xxxx + Lohn 740xxx (Einsatz-Filter)
        cursor.execute(convert_placeholders("""
            SELECT SUM(CASE WHEN nominal_account_number BETWEEN 840000 AND 849999 AND debit_or_credit = 'H' THEN posted_value
                           WHEN nominal_account_number BETWEEN 840000 AND 849999 AND debit_or_credit = 'S' THEN -posted_value ELSE 0 END) / 100.0 as umsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
            """ + FIRMA_FILTER_UMSATZ), (von_6m.strftime('%Y-%m-%d'), bis_6m.strftime('%Y-%m-%d')))
        umsatz_6m = float((row_to_dict(cursor.fetchone(), cursor) or {}).get('umsatz') or 0)

        cursor.execute(convert_placeholders("""
            SELECT
                SUM(CASE WHEN nominal_account_number BETWEEN 740000 AND 749999 AND debit_or_credit = 'S' THEN posted_value
                         WHEN nominal_account_number BETWEEN 740000 AND 749999 AND debit_or_credit = 'H' THEN -posted_value ELSE 0 END) / 100.0 as einsatz,
                SUM(CASE WHEN nominal_account_number BETWEEN 740000 AND 742999 AND debit_or_credit = 'S' THEN posted_value
                         WHEN nominal_account_number BETWEEN 740000 AND 742999 AND debit_or_credit = 'H' THEN -posted_value ELSE 0 END) / 100.0 as lohn
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
            """ + FIRMA_FILTER_EINSATZ), (von_6m.strftime('%Y-%m-%d'), bis_6m.strftime('%Y-%m-%d')))
        r6 = row_to_dict(cursor.fetchone(), cursor)
        einsatz_6m = float(r6.get('einsatz') or 0)
        lohn_6m = float(r6.get('lohn') or 0)

        # Aktueller Monat (laufend): Umsatz + FIBU-Einsatz
        von_akt = aktueller_monat_start
        bis_akt = (heute + timedelta(days=1)).strftime('%Y-%m-%d')

        cursor.execute(convert_placeholders("""
            SELECT SUM(CASE WHEN nominal_account_number BETWEEN 840000 AND 849999 AND debit_or_credit = 'H' THEN posted_value
                           WHEN nominal_account_number BETWEEN 840000 AND 849999 AND debit_or_credit = 'S' THEN -posted_value ELSE 0 END) / 100.0 as umsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
            """ + FIRMA_FILTER_UMSATZ), (von_akt.strftime('%Y-%m-%d'), bis_akt))
        umsatz_akt = float((row_to_dict(cursor.fetchone(), cursor) or {}).get('umsatz') or 0)

        cursor.execute(convert_placeholders("""
            SELECT SUM(CASE WHEN nominal_account_number BETWEEN 740000 AND 749999 AND debit_or_credit = 'S' THEN posted_value
                           WHEN nominal_account_number BETWEEN 740000 AND 749999 AND debit_or_credit = 'H' THEN -posted_value ELSE 0 END) / 100.0 as einsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
            """ + FIRMA_FILTER_EINSATZ), (von_akt.strftime('%Y-%m-%d'), bis_akt))
        einsatz_fibu_akt = float((row_to_dict(cursor.fetchone(), cursor) or {}).get('einsatz') or 0)

        # Letzter abgeschlossener Monat (Vergleich mit Ist)
        von_vm = von_letzter
        bis_vm = (ende_letzter + timedelta(days=1)).strftime('%Y-%m-%d')
        cursor.execute(convert_placeholders("""
            SELECT SUM(CASE WHEN nominal_account_number BETWEEN 840000 AND 849999 AND debit_or_credit = 'H' THEN posted_value
                           WHEN nominal_account_number BETWEEN 840000 AND 849999 AND debit_or_credit = 'S' THEN -posted_value ELSE 0 END) / 100.0 as umsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
            """ + FIRMA_FILTER_UMSATZ), (von_vm.strftime('%Y-%m-%d'), bis_vm))
        umsatz_vm = float((row_to_dict(cursor.fetchone(), cursor) or {}).get('umsatz') or 0)
        cursor.execute(convert_placeholders("""
            SELECT SUM(CASE WHEN nominal_account_number BETWEEN 740000 AND 749999 AND debit_or_credit = 'S' THEN posted_value
                           WHEN nominal_account_number BETWEEN 740000 AND 749999 AND debit_or_credit = 'H' THEN -posted_value ELSE 0 END) / 100.0 as einsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
            """ + FIRMA_FILTER_EINSATZ), (von_vm.strftime('%Y-%m-%d'), bis_vm))
        einsatz_vm = float((row_to_dict(cursor.fetchone(), cursor) or {}).get('einsatz') or 0)

    # Quoten
    lohn_quote_6m = (lohn_6m / umsatz_6m) if umsatz_6m > 0 else 0
    einsatz_quote_6m = (einsatz_6m / umsatz_6m) if umsatz_6m > 0 else 0

    # Method A: FIBU aktuell + (Umsatz_akt * Lohn_6M/Umsatz_6M)
    einsatz_method_a = einsatz_fibu_akt + (umsatz_akt * lohn_quote_6m)
    # Method B: Umsatz_akt * (Einsatz_6M / Umsatz_6M)
    einsatz_method_b = umsatz_akt * einsatz_quote_6m

    db1_a = umsatz_akt - einsatz_method_a
    db1_b = umsatz_akt - einsatz_method_b
    marge_a = (db1_a / umsatz_akt * 100) if umsatz_akt > 0 else 0
    marge_b = (db1_b / umsatz_akt * 100) if umsatz_akt > 0 else 0

    print("=" * 70)
    print("4-LOHN WERKSTATT: Vergleich Method A (nur Lohn 6M) vs Method B (Einsatz 6M Quote)")
    print("=" * 70)
    print()
    print("Rollierender 6-Monats-Zeitraum (abgeschlossen): {} bis {}".format(von_6m.strftime('%Y-%m-%d'), bis_6m.strftime('%Y-%m-%d')))
    print("  Umsatz 84xxxx:  {:>14,.0f} €".format(umsatz_6m))
    print("  Einsatz 74xxxx: {:>14,.0f} €".format(einsatz_6m))
    print("  Lohn 740xxx:    {:>14,.0f} €".format(lohn_6m))
    print("  Quote Einsatz/Umsatz: {:.1f}%".format(einsatz_quote_6m * 100))
    print("  Quote Lohn/Umsatz:    {:.1f}%".format(lohn_quote_6m * 100))
    print()
    print("Aktueller Monat (bis {}): {}".format(bis_akt, von_akt.strftime('%Y-%m')))
    print("  Umsatz:         {:>14,.0f} €".format(umsatz_akt))
    print("  FIBU-Einsatz:   {:>14,.0f} €".format(einsatz_fibu_akt))
    print()
    print("Method A (nur Lohn 6M): Einsatz = FIBU + (Umsatz × Lohnquote)")
    print("  Einsatz kalk:   {:>14,.0f} €  → DB1: {:>12,.0f} €  Marge: {:>5.1f}%".format(einsatz_method_a, db1_a, marge_a))
    print()
    print("Method B (Einsatz 6M):  Einsatz = Umsatz × (Einsatz/Umsatz)_6M")
    print("  Einsatz kalk:   {:>14,.0f} €  → DB1: {:>12,.0f} €  Marge: {:>5.1f}%".format(einsatz_method_b, db1_b, marge_b))
    print()
    print("Vergleich letzter abgeschlossener Monat ({}):".format(von_vm.strftime('%Y-%m')))
    print("  Umsatz:         {:>14,.0f} €".format(umsatz_vm))
    print("  FIBU-Einsatz:   {:>14,.0f} €  (Ist)".format(einsatz_vm))
    print("  Method B (Umsatz × Quote_6M): {:>14,.0f} €".format(umsatz_vm * einsatz_quote_6m))
    abw_b = (umsatz_vm * einsatz_quote_6m) - einsatz_vm
    print("  ==> Abweichung Method B zu Ist: {:>10,.0f} € ({:+.1f}%)".format(abw_b, (abw_b / einsatz_vm * 100) if einsatz_vm else 0))
    print()
    print("Fazit: Method B ist einfacher (ein Verhältnis Einsatz/Umsatz). Werte oben vergleichen.")
    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
