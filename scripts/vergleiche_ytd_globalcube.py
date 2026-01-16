#!/usr/bin/env python3
"""
Vergleich YTD mit GlobalCube
============================
TAG 196: Prüft die aktuellen YTD-Werte gegen GlobalCube-Referenz
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

# YTD: Sep 2025 - Dez 2025
datum_von = '2025-09-01'
datum_bis = '2026-01-01'

# Gesamtsumme Filter (firma=0, standort=0)
firma_filter_einsatz = """AND (
    ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
    OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
    OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
)"""
guv_filter = "AND NOT ((nominal_account_number BETWEEN 890000 AND 899999 AND substr(CAST(nominal_account_number AS TEXT), 4, 1) = '9') OR (nominal_account_number BETWEEN 490000 AND 499999 AND substr(CAST(nominal_account_number AS TEXT), 4, 1) = '9'))"

print("="*80)
print("YTD VERGLEICH MIT GLOBALCUBE")
print("="*80)
print(f"Zeitraum: {datum_von} bis {datum_bis}")
print()

# GlobalCube Referenzwerte (aus vorherigen Analysen)
globalcube_referenz = {
    'einsatz': 9191864.00,
    'umsatz': 10618393.36,  # Aus API-Response
    'betriebsergebnis': -375905.00,  # Aus Screenshot
}

with db_session() as conn:
    cursor = conn.cursor()
    
    # Einsatz YTD (mit allen Ausschlüssen)
    query_einsatz = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND nominal_account_number NOT IN (743002, 717001, 727001, 727501)
          {firma_filter_einsatz}
          {guv_filter}
    """
    cursor.execute(convert_placeholders(query_einsatz), (datum_von, datum_bis))
    einsatz_ytd = float(row_to_dict(cursor.fetchone()).get('wert', 0) or 0)
    
    # Umsatz YTD
    firma_filter_umsatz = """AND (
        ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
        OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
        OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
    )"""
    
    ytd_umsatz_range_filter = "AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))"
    
    query_umsatz = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          {ytd_umsatz_range_filter}
          {firma_filter_umsatz}
          {guv_filter}
    """
    cursor.execute(convert_placeholders(query_umsatz), (datum_von, datum_bis))
    umsatz_ytd = float(row_to_dict(cursor.fetchone()).get('wert', 0) or 0)
    
    # DB1 YTD
    db1_ytd = umsatz_ytd - einsatz_ytd
    
    print("=== DRIVE WERTE ===")
    print(f"Einsatz YTD: {einsatz_ytd:,.2f} €")
    print(f"Umsatz YTD: {umsatz_ytd:,.2f} €")
    print(f"DB1 YTD: {db1_ytd:,.2f} €")
    print()
    
    print("=== GLOBALCUBE REFERENZ ===")
    print(f"Einsatz YTD: {globalcube_referenz['einsatz']:,.2f} €")
    print(f"Umsatz YTD: {globalcube_referenz['umsatz']:,.2f} €")
    print(f"Betriebsergebnis YTD: {globalcube_referenz['betriebsergebnis']:,.2f} €")
    print()
    
    print("=== DIFFERENZEN ===")
    diff_einsatz = einsatz_ytd - globalcube_referenz['einsatz']
    diff_umsatz = umsatz_ytd - globalcube_referenz['umsatz']
    diff_db1 = db1_ytd - (globalcube_referenz['umsatz'] - globalcube_referenz['einsatz'])
    
    print(f"Einsatz YTD: {diff_einsatz:+,.2f} € ({'DRIVE zu hoch' if diff_einsatz > 0 else 'DRIVE zu niedrig'})")
    print(f"Umsatz YTD: {diff_umsatz:+,.2f} € ({'DRIVE zu hoch' if diff_umsatz > 0 else 'DRIVE zu niedrig'})")
    print(f"DB1 YTD: {diff_db1:+,.2f} € ({'DRIVE zu hoch' if diff_db1 > 0 else 'DRIVE zu niedrig'})")
    print()
    
    # Prüfe ob zurückgestellte Konten möglicherweise doch enthalten sein sollten
    print("="*80)
    print("ANALYSE: SOLLTEN ZURÜCKGESTELLTE KONTEN DOCH ENTHALTEN SEIN?")
    print("="*80)
    
    # Prüfe verschiedene Kombinationen
    kombinationen = [
        ("Nur 743002 ausgeschlossen", [743002]),
        ("743002 + 727001 ausgeschlossen", [743002, 727001]),
        ("743002 + 717001 ausgeschlossen", [743002, 717001]),
        ("743002 + 727501 ausgeschlossen", [743002, 727501]),
        ("Alle zurückgestellten ausgeschlossen (aktuell)", [743002, 717001, 727001, 727501]),
    ]
    
    for beschreibung, ausgeschlossen in kombinationen:
        exclude_list = ', '.join(map(str, ausgeschlossen))
        query_test = f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 700000 AND 799999
              AND nominal_account_number NOT IN ({exclude_list})
              {firma_filter_einsatz}
              {guv_filter}
        """
        cursor.execute(convert_placeholders(query_test), (datum_von, datum_bis))
        wert = float(row_to_dict(cursor.fetchone()).get('wert', 0) or 0)
        diff = wert - globalcube_referenz['einsatz']
        print(f"{beschreibung}: {wert:,.2f} € (Differenz: {diff:+,.2f} €)")
