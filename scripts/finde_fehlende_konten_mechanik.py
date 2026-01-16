#!/usr/bin/env python3
"""
Finde fehlende Konten für Mechanik+Karo
========================================
TAG 196: Analysiert welche Konten zu "Mechanik+Karo" gehören sollten
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

# Dezember 2025
datum_von = '2025-12-01'
datum_bis = '2026-01-01'

# Gesamtsumme Filter (firma=0, standort=0)
firma_filter_umsatz = """AND (
    ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
    OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
    OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
)"""
firma_filter_einsatz = """AND (
    ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
    OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
    OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
)"""
guv_filter = "AND NOT ((nominal_account_number BETWEEN 890000 AND 899999 AND substr(CAST(nominal_account_number AS TEXT), 4, 1) = '9') OR (nominal_account_number BETWEEN 490000 AND 499999 AND substr(CAST(nominal_account_number AS TEXT), 4, 1) = '9'))"

target_differenz = 10814.14

print("="*80)
print("FINDE FEHLENDE KONTEN FÜR MECHANIK+KARO")
print("="*80)
print(f"Zeitraum: {datum_von} bis {datum_bis}")
print(f"Fehlende Differenz: {target_differenz:,.2f} €")
print()

with db_session() as conn:
    cursor = conn.cursor()
    
    # Prüfe alle 84xxxx Konten die NICHT in Mechanik enthalten sind
    print("="*80)
    print("84XXXX KONTEN - AUSGESCHLOSSENE BEREICHE")
    print("="*80)
    
    ausgeschlossen_bereiche = [
        ("8405xx (Karosserie)", 840500, 840599),
        ("8406xx (Lackierung)", 840600, 840699),
        ("847xxx (Clean Park)", 847000, 847999),
    ]
    
    for bezeichnung, von, bis in ausgeschlossen_bereiche:
        query_erlos = f"""
            SELECT 
                SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as erlos,
                COUNT(*) as anzahl
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN {von} AND {bis}
              {firma_filter_umsatz}
              {guv_filter}
        """
        cursor.execute(convert_placeholders(query_erlos), (datum_von, datum_bis))
        row = cursor.fetchone()
        if row:
            r = row_to_dict(row)
            erlos = float(r.get('erlos', 0) or 0)
            anzahl = int(r.get('anzahl', 0) or 0)
            if abs(erlos) > 0:
                print(f"{bezeichnung}: {erlos:,.2f} € ({anzahl} Buchungen)")
    
    # Prüfe ob es andere 8xxxxx Konten gibt, die zu Mechanik gehören könnten
    print()
    print("="*80)
    print("ANDERE 8XXXXX KONTEN (außer 84xxxx)")
    print("="*80)
    
    andere_bereiche = [
        ("85xxxx (Lack/Sonstige)", 850000, 859999),
        ("86xxxx (Mietwagen)", 860000, 869999),
        ("88xxxx (falls existiert)", 880000, 889999),
    ]
    
    for bezeichnung, von, bis in andere_bereiche:
        query = f"""
            SELECT 
                SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as wert,
                COUNT(*) as anzahl
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN {von} AND {bis}
              {firma_filter_umsatz}
              {guv_filter}
        """
        cursor.execute(convert_placeholders(query), (datum_von, datum_bis))
        row = cursor.fetchone()
        if row:
            r = row_to_dict(row)
            wert = float(r.get('wert', 0) or 0)
            anzahl = int(r.get('anzahl', 0) or 0)
            if abs(wert) > 1000:
                print(f"{bezeichnung}: {wert:,.2f} € ({anzahl} Buchungen)")
                if abs(wert - target_differenz) < target_differenz * 0.2:
                    print(f"  ⚠️ NAHE DIFFERENZ!")
    
    # Prüfe ob es 74xxxx Konten gibt, die ausgeschlossen werden sollten (negative Differenz)
    print()
    print("="*80)
    print("74XXXX KONTEN - PRÜFUNG OB AUSGESCHLOSSENE ZU HOCH SIND")
    print("="*80)
    
    ausgeschlossen_einsatz = [
        ("745xxx (Karosserie)", 745000, 745999),
        ("746xxx (Lackierung)", 746000, 746999),
        ("747xxx (Clean Park)", 747000, 747999),
    ]
    
    for bezeichnung, von, bis in ausgeschlossen_einsatz:
        query = f"""
            SELECT 
                SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert,
                COUNT(*) as anzahl
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN {von} AND {bis}
              AND nominal_account_number != 743002
              {firma_filter_einsatz}
              {guv_filter}
        """
        cursor.execute(convert_placeholders(query), (datum_von, datum_bis))
        row = cursor.fetchone()
        if row:
            r = row_to_dict(row)
            wert = float(r.get('wert', 0) or 0)
            anzahl = int(r.get('anzahl', 0) or 0)
            if abs(wert) > 0:
                print(f"{bezeichnung}: {wert:,.2f} € ({anzahl} Buchungen)")
    
    # Prüfe ob es Standort-Unterschiede gibt
    print()
    print("="*80)
    print("STANDORT-ANALYSE")
    print("="*80)
    
    query_standorte = f"""
        SELECT 
            branch_number,
            subsidiary_to_company_ref,
            SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as erlos_84,
            SUM(CASE WHEN nominal_account_number BETWEEN 840000 AND 849999 AND debit_or_credit='H' THEN posted_value ELSE CASE WHEN nominal_account_number BETWEEN 840000 AND 849999 THEN -posted_value ELSE 0 END END)/100.0 as erlos_84_only
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 840000 AND 849999
          AND nominal_account_number NOT BETWEEN 840500 AND 840599
          AND nominal_account_number NOT BETWEEN 840600 AND 840699
          AND nominal_account_number NOT BETWEEN 847000 AND 847999
          {firma_filter_umsatz}
          {guv_filter}
        GROUP BY branch_number, subsidiary_to_company_ref
        ORDER BY branch_number, subsidiary_to_company_ref
    """
    cursor.execute(convert_placeholders(query_standorte), (datum_von, datum_bis))
    rows = cursor.fetchall()
    
    for row in rows:
        r = row_to_dict(row)
        branch = r.get('branch_number', 'N/A')
        subsidiary = r.get('subsidiary_to_company_ref', 'N/A')
        erlos = float(r.get('erlos_84_only', 0) or 0)
        if abs(erlos) > 1000:
            print(f"Branch {branch}, Subsidiary {subsidiary}: {erlos:,.2f} €")
