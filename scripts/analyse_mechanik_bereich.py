#!/usr/bin/env python3
"""
Analyse Mechanik-Bereich
========================
TAG 196: Analysiert Mechanik-Bereichsberechnung für Dezember 2025
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

print("="*80)
print("ANALYSE MECHANIK-BEREICH DEZEMBER 2025")
print("="*80)
print(f"Zeitraum: {datum_von} bis {datum_bis}")
print()
print("DRIVE Mechanik Dezember: 93.862,80 €")
print("GlobalCube Mechanik+Karo: 86.419,00 €")
print("Differenz: +7.443,80 € (DRIVE zu hoch)")
print()

with db_session() as conn:
    cursor = conn.cursor()
    
    # Mechanik Erlöse (84xxxx)
    print("="*80)
    print("MECHANIK ERLÖSE (84xxxx)")
    print("="*80)
    
    query_erlos = f"""
        SELECT 
            nominal_account_number as konto,
            SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as wert,
            COUNT(*) as anzahl,
            branch_number,
            subsidiary_to_company_ref
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 840000 AND 849999
          {firma_filter_umsatz}
          {guv_filter}
        GROUP BY nominal_account_number, branch_number, subsidiary_to_company_ref
        ORDER BY ABS(SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)) DESC
    """
    
    cursor.execute(convert_placeholders(query_erlos), (datum_von, datum_bis))
    rows = cursor.fetchall()
    
    total_erlos = 0
    for row in rows:
        r = row_to_dict(row)
        konto = r['konto']
        wert = float(r.get('wert', 0) or 0)
        anzahl = int(r.get('anzahl', 0) or 0)
        branch = r.get('branch_number', 'N/A')
        subsidiary = r.get('subsidiary_to_company_ref', 'N/A')
        total_erlos += wert
        
        if abs(wert) > 100:
            print(f"  {konto}: {wert:,.2f} € ({anzahl} Buchungen, branch={branch}, subsidiary={subsidiary})")
    
    print(f"\nGesamt Erlös 84xxxx: {total_erlos:,.2f} €")
    print()
    
    # Mechanik Einsatz (74xxxx)
    print("="*80)
    print("MECHANIK EINSATZ (74xxxx)")
    print("="*80)
    
    query_einsatz = f"""
        SELECT 
            nominal_account_number as konto,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert,
            COUNT(*) as anzahl,
            branch_number,
            subsidiary_to_company_ref
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 740000 AND 749999
          AND nominal_account_number != 743002
          {firma_filter_einsatz}
          {guv_filter}
        GROUP BY nominal_account_number, branch_number, subsidiary_to_company_ref
        ORDER BY ABS(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)) DESC
    """
    
    cursor.execute(convert_placeholders(query_einsatz), (datum_von, datum_bis))
    rows = cursor.fetchall()
    
    total_einsatz = 0
    for row in rows:
        r = row_to_dict(row)
        konto = r['konto']
        wert = float(r.get('wert', 0) or 0)
        anzahl = int(r.get('anzahl', 0) or 0)
        branch = r.get('branch_number', 'N/A')
        subsidiary = r.get('subsidiary_to_company_ref', 'N/A')
        total_einsatz += wert
        
        if abs(wert) > 100:
            print(f"  {konto}: {wert:,.2f} € ({anzahl} Buchungen, branch={branch}, subsidiary={subsidiary})")
    
    print(f"\nGesamt Einsatz 74xxxx: {total_einsatz:,.2f} €")
    print()
    
    # Bruttoertrag
    bruttoertrag = total_erlos - total_einsatz
    print("="*80)
    print("ZUSAMMENFASSUNG")
    print("="*80)
    print(f"Erlös 84xxxx: {total_erlos:,.2f} €")
    print(f"Einsatz 74xxxx: {total_einsatz:,.2f} €")
    print(f"Bruttoertrag: {bruttoertrag:,.2f} €")
    print()
    print(f"DRIVE API: 93.862,80 €")
    print(f"GlobalCube: 86.419,00 €")
    print(f"Differenz: {bruttoertrag - 86419:+,.2f} €")
    print()
    
    # Prüfe ob Karosserie-Konten ausgeschlossen werden sollten
    print("="*80)
    print("KAROSSERIE-KONTEN PRÜFUNG")
    print("="*80)
    print("GlobalCube zeigt 'Mechanik+Karo', DRIVE zeigt nur 'Mechanik'")
    print("Prüfe ob 84xxxx Karosserie-Konten ausgeschlossen werden sollten:")
    print()
    
    # Prüfe spezifische Karosserie-Konten (8405xx = Karosserie, 8406xx = Lackierung)
    karosserie_konten = [
        (840500, 840599, "8405xx - Karosserie"),
        (840600, 840699, "8406xx - Lackierung"),
    ]
    
    for von, bis, bezeichnung in karosserie_konten:
        query_karo = f"""
            SELECT 
                SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as wert,
                COUNT(*) as anzahl
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN {von} AND {bis}
              {firma_filter_umsatz}
              {guv_filter}
        """
        cursor.execute(convert_placeholders(query_karo), (datum_von, datum_bis))
        row = cursor.fetchone()
        if row:
            r = row_to_dict(row)
            wert = float(r.get('wert', 0) or 0)
            anzahl = int(r.get('anzahl', 0) or 0)
            if abs(wert) > 0:
                print(f"{bezeichnung}: {wert:,.2f} € ({anzahl} Buchungen)")
                if abs(wert) > 1000:
                    print(f"  ⚠️ Großer Wert - könnte ausgeschlossen werden sollten!")
