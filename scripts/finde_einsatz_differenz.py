#!/usr/bin/env python3
"""
Finde die Ursache der Einsatz YTD Differenz
===========================================
TAG 196: Findet Konten, die möglicherweise ausgeschlossen werden sollten
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

target_differenz = 15450.53  # +15.450,53 €

print("="*80)
print("FINDE EINSATZ YTD DIFFERENZ URSACHE")
print("="*80)
print(f"Zeitraum: {datum_von} bis {datum_bis}")
print(f"Ziel-Differenz: +{target_differenz:,.2f} € (DRIVE zu hoch)")
print(f"GlobalCube Referenz: 9.191.864,00 €")
print(f"DRIVE aktuell: 9.207.314,53 €")
print()

with db_session() as conn:
    cursor = conn.cursor()
    
    # Suche nach Konten, die genau oder nahe der Differenz entsprechen
    print("="*80)
    print("KONTEN MIT WERTEN NAHE DER DIFFERENZ (±5%)")
    print("="*80)
    
    query = f"""
        SELECT 
            nominal_account_number as konto,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert,
            COUNT(*) as anzahl,
            branch_number,
            subsidiary_to_company_ref
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND nominal_account_number != 743002
          {firma_filter_einsatz}
          {guv_filter}
        GROUP BY nominal_account_number, branch_number, subsidiary_to_company_ref
        ORDER BY ABS(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END))
        DESC
        LIMIT 100
    """
    
    cursor.execute(convert_placeholders(query), (datum_von, datum_bis))
    rows = cursor.fetchall()
    
    nahe_konten = []
    for row in rows:
        r = row_to_dict(row)
        konto = r['konto']
        wert = float(r.get('wert', 0) or 0)
        anzahl = int(r.get('anzahl', 0) or 0)
        branch = r.get('branch_number', 'N/A')
        subsidiary = r.get('subsidiary_to_company_ref', 'N/A')
        abs_wert = abs(wert)
        diff = abs(abs_wert - target_differenz)
        rel_diff = diff / target_differenz if target_differenz > 0 else 1
        
        if rel_diff < 0.05:  # ±5%
            nahe_konten.append({
                'konto': konto,
                'wert': wert,
                'anzahl': anzahl,
                'branch': branch,
                'subsidiary': subsidiary,
                'diff': diff
            })
    
    if nahe_konten:
        for k in sorted(nahe_konten, key=lambda x: x['diff']):
            print(f"  {k['konto']} (branch={k['branch']}, subsidiary={k['subsidiary']}): {k['wert']:,.2f} € ({k['anzahl']} Buchungen, Abweichung: {k['diff']:,.2f} €)")
    else:
        print("  Keine Konten gefunden, die genau der Differenz entsprechen.")
    
    print()
    
    # Prüfe ob es Konten gibt, die möglicherweise doppelt gezählt werden
    print("="*80)
    print("MÖGLICHE DOPPELZÄHLUNGEN (gleiches Konto, verschiedene branch/subsidiary)")
    print("="*80)
    
    query_doppel = f"""
        SELECT 
            nominal_account_number as konto,
            COUNT(DISTINCT branch_number) as branch_count,
            COUNT(DISTINCT subsidiary_to_company_ref) as subsidiary_count,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as gesamt_wert,
            COUNT(*) as anzahl
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND nominal_account_number != 743002
          {firma_filter_einsatz}
          {guv_filter}
        GROUP BY nominal_account_number
        HAVING COUNT(DISTINCT branch_number) > 1 OR COUNT(DISTINCT subsidiary_to_company_ref) > 1
        ORDER BY ABS(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)) DESC
        LIMIT 20
    """
    
    cursor.execute(convert_placeholders(query_doppel), (datum_von, datum_bis))
    rows_doppel = cursor.fetchall()
    
    if rows_doppel:
        for row in rows_doppel:
            r = row_to_dict(row)
            konto = r['konto']
            branch_count = int(r.get('branch_count', 0) or 0)
            subsidiary_count = int(r.get('subsidiary_count', 0) or 0)
            gesamt = float(r.get('gesamt_wert', 0) or 0)
            anzahl = int(r.get('anzahl', 0) or 0)
            
            if abs(gesamt) > 1000:
                print(f"  {konto}: {gesamt:,.2f} € ({anzahl} Buchungen, {branch_count} branches, {subsidiary_count} subsidiaries)")
                
                # Detaillierte Aufschlüsselung
                query_detail = f"""
                    SELECT 
                        branch_number,
                        subsidiary_to_company_ref,
                        SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
                    FROM loco_journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND nominal_account_number = {konto}
                      AND nominal_account_number != 743002
                      {firma_filter_einsatz}
                      {guv_filter}
                    GROUP BY branch_number, subsidiary_to_company_ref
                    ORDER BY branch_number, subsidiary_to_company_ref
                """
                cursor.execute(convert_placeholders(query_detail), (datum_von, datum_bis))
                detail_rows = cursor.fetchall()
                for detail_row in detail_rows:
                    dr = row_to_dict(detail_row)
                    print(f"    branch={dr.get('branch_number', 'N/A')}, subsidiary={dr.get('subsidiary_to_company_ref', 'N/A')}: {float(dr.get('wert', 0) or 0):,.2f} €")
    else:
        print("  Keine offensichtlichen Doppelzählungen gefunden.")
    
    print()
    
    # Prüfe ob es Konten gibt, die möglicherweise negative Werte haben (HABEN-Buchungen)
    print("="*80)
    print("KONTEN MIT GROSSEN HABEN-BUCHUNGEN (negative Werte)")
    print("="*80)
    
    query_haben = f"""
        SELECT 
            nominal_account_number as konto,
            SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE 0 END)/100.0 as haben_wert,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE 0 END)/100.0 as soll_wert,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as netto_wert,
            COUNT(*) as anzahl
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND nominal_account_number != 743002
          {firma_filter_einsatz}
          {guv_filter}
        GROUP BY nominal_account_number
        HAVING ABS(SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE 0 END)) > 10000
        ORDER BY ABS(SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE 0 END)) DESC
        LIMIT 20
    """
    
    cursor.execute(convert_placeholders(query_haben), (datum_von, datum_bis))
    rows_haben = cursor.fetchall()
    
    if rows_haben:
        for row in rows_haben:
            r = row_to_dict(row)
            konto = r['konto']
            haben = float(r.get('haben_wert', 0) or 0)
            soll = float(r.get('soll_wert', 0) or 0)
            netto = float(r.get('netto_wert', 0) or 0)
            anzahl = int(r.get('anzahl', 0) or 0)
            
            if abs(haben) > 1000:
                print(f"  {konto}: Netto={netto:,.2f} € (SOLL={soll:,.2f} €, HABEN={haben:,.2f} €, {anzahl} Buchungen)")
                if abs(haben) > abs(soll) * 0.5:  # HABEN ist signifikant
                    print(f"    ⚠️ Große HABEN-Buchung - möglicherweise Korrekturbuchung oder Rückstellung")
    else:
        print("  Keine großen HABEN-Buchungen gefunden.")
    
    print()
    print("="*80)
    print("ZUSAMMENFASSUNG")
    print("="*80)
    print(f"Ziel: Finde Konten, die +{target_differenz:,.2f} € zur Differenz beitragen")
    print(f"Wenn ein Konto ausgeschlossen werden sollte, sollte sein Wert nahe {target_differenz:,.2f} € sein")
