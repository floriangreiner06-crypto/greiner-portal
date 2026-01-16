#!/usr/bin/env python3
"""
Detaillierte Einsatz YTD Analyse
=================================
TAG 196: Analysiert die +15.450,53 € Differenz im Einsatz YTD
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
print("DETAILLIERTE EINSATZ YTD ANALYSE")
print("="*80)
print(f"Zeitraum: {datum_von} bis {datum_bis}")
print(f"GlobalCube Referenz: 9.191.864,00 €")
print(f"DRIVE aktuell: 9.207.314,53 €")
print(f"Differenz: +15.450,53 € (DRIVE zu hoch)")
print()

with db_session() as conn:
    cursor = conn.cursor()
    
    # Top 50 Konten nach Betrag (um große Abweichungen zu finden)
    print("="*80)
    print("TOP 50 EINSATZ-KONTEN YTD (nach Betrag)")
    print("="*80)
    
    query_top = f"""
        SELECT 
            nominal_account_number as konto,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert,
            COUNT(*) as anzahl_buchungen,
            branch_number,
            subsidiary_to_company_ref
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND nominal_account_number != 743002
          {firma_filter_einsatz}
          {guv_filter}
        GROUP BY nominal_account_number, branch_number, subsidiary_to_company_ref
        ORDER BY ABS(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)) DESC
        LIMIT 50
    """
    
    cursor.execute(convert_placeholders(query_top), (datum_von, datum_bis))
    rows = cursor.fetchall()
    
    total_top = 0
    for row in rows:
        r = row_to_dict(row)
        konto = r['konto']
        wert = float(r['wert'] or 0)
        anzahl = int(r.get('anzahl_buchungen', 0) or 0)
        branch = r.get('branch_number', 'N/A')
        subsidiary = r.get('subsidiary_to_company_ref', 'N/A')
        total_top += wert
        
        if abs(wert) > 1000:
            print(f"  {konto}: {wert:,.2f} € ({anzahl} Buchungen, branch={branch}, subsidiary={subsidiary})")
    
    print(f"\nSumme Top 50: {total_top:,.2f} €")
    print()
    
    # Prüfe spezielle Konten die möglicherweise ausgeschlossen werden sollten
    print("="*80)
    print("SPEZIELLE KONTEN PRÜFUNG")
    print("="*80)
    
    spezielle_konten = [
        (743000, 743099, "743xxx - EW Fremdleistungen Bereich"),
        (743001, 743001, "743001 - Spezifisches Konto"),
        (743002, 743002, "743002 - EW Fremdleistungen für Kunden (sollte ausgeschlossen sein)"),
        (743003, 743999, "743003-743999 - Weitere EW Konten"),
    ]
    
    for von, bis, bezeichnung in spezielle_konten:
        cursor.execute(convert_placeholders(f"""
            SELECT 
                SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert,
                COUNT(*) as anzahl
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN {von} AND {bis}
              {firma_filter_einsatz}
              {guv_filter}
        """), (datum_von, datum_bis))
        row = cursor.fetchone()
        if row:
            r = row_to_dict(row)
            wert = float(r.get('wert', 0) or 0)
            anzahl = int(r.get('anzahl', 0) or 0)
            if abs(wert) > 0:
                print(f"{bezeichnung}: {wert:,.2f} € ({anzahl} Buchungen)")
    
    # Prüfe Doppelzählungen zwischen Standorten
    print()
    print("="*80)
    print("DOPPELZÄHLUNGS-PRÜFUNG")
    print("="*80)
    
    # Prüfe ob Konten mit branch=1 UND branch=3 existieren (Landau/Deggendorf Überschneidung)
    query_doppel = f"""
        SELECT 
            nominal_account_number as konto,
            branch_number,
            subsidiary_to_company_ref,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND nominal_account_number != 743002
          AND (branch_number = 1 OR branch_number = 3)
          AND subsidiary_to_company_ref = 1
          {guv_filter}
        GROUP BY nominal_account_number, branch_number, subsidiary_to_company_ref
        HAVING ABS(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)) > 10000
        ORDER BY ABS(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)) DESC
        LIMIT 20
    """
    
    cursor.execute(convert_placeholders(query_doppel), (datum_von, datum_bis))
    rows_doppel = cursor.fetchall()
    
    konten_mit_branch = {}
    for row in rows_doppel:
        r = row_to_dict(row)
        konto = r['konto']
        branch = r['branch_number']
        wert = float(r['wert'] or 0)
        
        if konto not in konten_mit_branch:
            konten_mit_branch[konto] = {}
        konten_mit_branch[konto][branch] = wert
    
    doppel_gefunden = False
    for konto, branches in konten_mit_branch.items():
        if len(branches) > 1:
            # Konto existiert mit mehreren branch-Werten
            total = sum(branches.values())
            if abs(total) > 1000:
                print(f"Konto {konto}:")
                for branch, wert in branches.items():
                    print(f"  branch={branch}: {wert:,.2f} €")
                print(f"  Gesamt: {total:,.2f} €")
                doppel_gefunden = True
    
    if not doppel_gefunden:
        print("Keine offensichtlichen Doppelzählungen gefunden.")
    
    print()
    print("="*80)
    print("ZUSAMMENFASSUNG")
    print("="*80)
    print(f"Einsatz YTD DRIVE: 9.207.314,53 €")
    print(f"Einsatz YTD GlobalCube: 9.191.864,00 €")
    print(f"Differenz: +15.450,53 €")
    print()
    print("Nächste Schritte:")
    print("1. Prüfe ob weitere 743xxx Konten ausgeschlossen werden sollten")
    print("2. Prüfe ob Filter-Unterschiede zwischen DRIVE und GlobalCube existieren")
    print("3. Prüfe ob es Konten gibt, die GlobalCube anders behandelt")
