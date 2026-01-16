#!/usr/bin/env python3
"""
Einsatz YTD Analyse
===================
TAG 196: Analysiert die +31.905,97 € Differenz im Einsatz YTD
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
print("EINSATZ YTD ANALYSE")
print("="*80)
print(f"Zeitraum: {datum_von} bis {datum_bis}")
print(f"GlobalCube Referenz: 9.191.864,00 €")
print(f"DRIVE aktuell: 9.223.769,97 €")
print(f"Differenz: +31.905,97 € (DRIVE zu hoch)")
print()

with db_session() as conn:
    cursor = conn.cursor()
    
    # Einsatz YTD gesamt
    query_gesamt = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND nominal_account_number != 743002
          {firma_filter_einsatz}
          {guv_filter}
    """
    cursor.execute(convert_placeholders(query_gesamt), (datum_von, datum_bis))
    einsatz_gesamt = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    print(f"Einsatz YTD gesamt: {einsatz_gesamt:,.2f} €")
    print()
    
    # Einsatz nach Standort aufschlüsseln
    print("="*80)
    print("EINSATZ YTD NACH STANDORT")
    print("="*80)
    
    # Deggendorf Opel (branch=1, subsidiary=1)
    filter_deg_opel = "AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)"
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND nominal_account_number != 743002
          {filter_deg_opel}
          {guv_filter}
    """), (datum_von, datum_bis))
    einsatz_deg_opel = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    print(f"Deggendorf Opel: {einsatz_deg_opel:,.2f} €")
    
    # Landau (branch=3, subsidiary=1)
    filter_landau = "AND branch_number = 3 AND subsidiary_to_company_ref = 1"
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND nominal_account_number != 743002
          {filter_landau}
          {guv_filter}
    """), (datum_von, datum_bis))
    einsatz_landau = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    print(f"Landau: {einsatz_landau:,.2f} €")
    
    # Hyundai (6. Ziffer='1', subsidiary=2)
    filter_hyundai = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2"
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND nominal_account_number != 743002
          {filter_hyundai}
          {guv_filter}
    """), (datum_von, datum_bis))
    einsatz_hyundai = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    print(f"Hyundai: {einsatz_hyundai:,.2f} €")
    
    summe_einzel = einsatz_deg_opel + einsatz_landau + einsatz_hyundai
    print(f"Summe Einzelstandorte: {summe_einzel:,.2f} €")
    print(f"Gesamt (Filter): {einsatz_gesamt:,.2f} €")
    print(f"Differenz: {summe_einzel - einsatz_gesamt:,.2f} €")
    print()
    
    # Einsatz nach Kontenbereichen
    print("="*80)
    print("EINSATZ YTD NACH KONTENBEREICHEN")
    print("="*80)
    
    konto_bereiche = [
        (700000, 709999, "71xxxx - Einsatz Neuwagen"),
        (710000, 719999, "71xxxx - Einsatz Neuwagen"),
        (720000, 729999, "72xxxx - Einsatz Gebrauchtwagen"),
        (730000, 739999, "73xxxx - Einsatz Teile"),
        (740000, 749999, "74xxxx - Einsatz Werkstatt"),
        (750000, 759999, "75xxxx - Einsatz Sonstige"),
        (760000, 769999, "76xxxx - Einsatz Sonstige"),
        (770000, 779999, "77xxxx - Einsatz Sonstige"),
        (780000, 789999, "78xxxx - Einsatz Sonstige"),
        (790000, 799999, "79xxxx - Einsatz Sonstige"),
    ]
    
    for von, bis, bezeichnung in konto_bereiche:
        cursor.execute(convert_placeholders(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN {von} AND {bis}
              AND nominal_account_number != 743002
              {firma_filter_einsatz}
              {guv_filter}
        """), (datum_von, datum_bis))
        wert = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        if abs(wert) > 100:
            print(f"{bezeichnung}: {wert:,.2f} €")
    
    # Prüfe 743002 (sollte ausgeschlossen sein)
    print()
    print("="*80)
    print("743002 PRÜFUNG (sollte ausgeschlossen sein)")
    print("="*80)
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number = 743002
          {firma_filter_einsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    wert_743002 = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    print(f"743002 YTD: {wert_743002:,.2f} €")
    if abs(wert_743002) > 0:
        print(f"⚠️ WARNUNG: 743002 sollte 0 sein (ausgeschlossen)!")
    
    print()
    print("="*80)
    print("ZUSAMMENFASSUNG")
    print("="*80)
    print(f"Einsatz YTD DRIVE: {einsatz_gesamt:,.2f} €")
    print(f"Einsatz YTD GlobalCube: 9.191.864,00 €")
    print(f"Differenz: {einsatz_gesamt - 9191864.00:,.2f} €")
    print()
    print("Mögliche Ursachen:")
    print("1. Doppelzählungen zwischen Standorten")
    print("2. Konten die GlobalCube ausschließt, DRIVE aber einschließt")
    print("3. Filter-Unterschiede")
    print("4. 743002 wird nicht korrekt ausgeschlossen")
