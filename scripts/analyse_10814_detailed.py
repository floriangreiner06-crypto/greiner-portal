#!/usr/bin/env python3
"""
Detaillierte Analyse der fehlenden 10.814,14 €
==============================================
TAG 196: Findet welche Konten fehlen könnten
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
print("DETAILLIERTE ANALYSE: FEHLENDE 10.814,14 €")
print("="*80)
print(f"Zeitraum: {datum_von} bis {datum_bis}")
print(f"DRIVE Mechanik+CP: 75.604,86 €")
print(f"GlobalCube Mechanik+Karo: 86.419,00 €")
print(f"Fehlende Differenz: {target_differenz:,.2f} €")
print()

with db_session() as conn:
    cursor = conn.cursor()
    
    # Aktuelle Mechanik (ohne 8405xx, 8406xx, 847xxx)
    query_mech_erlos = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 840000 AND 849999
          AND nominal_account_number NOT BETWEEN 840500 AND 840599
          AND nominal_account_number NOT BETWEEN 840600 AND 840699
          AND nominal_account_number NOT BETWEEN 847000 AND 847999
          {firma_filter_umsatz}
          {guv_filter}
    """
    cursor.execute(convert_placeholders(query_mech_erlos), (datum_von, datum_bis))
    mech_erlos = float(row_to_dict(cursor.fetchone()).get('wert', 0) or 0)
    
    query_mech_einsatz = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 740000 AND 749999
          AND nominal_account_number != 743002
          AND nominal_account_number NOT BETWEEN 745000 AND 745999
          AND nominal_account_number NOT BETWEEN 746000 AND 746999
          AND nominal_account_number NOT BETWEEN 747000 AND 747999
          {firma_filter_einsatz}
          {guv_filter}
    """
    cursor.execute(convert_placeholders(query_mech_einsatz), (datum_von, datum_bis))
    mech_einsatz = float(row_to_dict(cursor.fetchone()).get('wert', 0) or 0)
    
    mech_be = mech_erlos - mech_einsatz
    
    # Clean Park
    query_cp_erlos = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 847000 AND 847999
          {firma_filter_umsatz}
          {guv_filter}
    """
    cursor.execute(convert_placeholders(query_cp_erlos), (datum_von, datum_bis))
    cp_erlos = float(row_to_dict(cursor.fetchone()).get('wert', 0) or 0)
    
    query_cp_einsatz = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 747000 AND 747999
          AND nominal_account_number != 743002
          {firma_filter_einsatz}
          {guv_filter}
    """
    cursor.execute(convert_placeholders(query_cp_einsatz), (datum_von, datum_bis))
    cp_einsatz = float(row_to_dict(cursor.fetchone()).get('wert', 0) or 0)
    
    cp_be = cp_erlos - cp_einsatz
    
    summe = mech_be + cp_be
    
    print("="*80)
    print("AKTUELLE WERTE")
    print("="*80)
    print(f"Mechanik (ohne CP): {mech_be:,.2f} €")
    print(f"Clean Park: {cp_be:,.2f} €")
    print(f"Summe: {summe:,.2f} €")
    print(f"GlobalCube: 86.419,00 €")
    print(f"Fehlende Differenz: {86419 - summe:,.2f} €")
    print()
    
    # Prüfe ob es andere 84xxxx Konten gibt, die möglicherweise zu Mechanik gehören sollten
    print("="*80)
    print("ALLE 84XXXX KONTEN (DETAILLIERT)")
    print("="*80)
    
    query_all_84 = f"""
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
        HAVING ABS(SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)) > 500
        ORDER BY ABS(SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)) DESC
    """
    cursor.execute(convert_placeholders(query_all_84), (datum_von, datum_bis))
    rows = cursor.fetchall()
    
    in_mech = 0
    ausgeschlossen = 0
    
    print("Konten in Mechanik (8400xx-8404xx, 8407xx-846xxx, 848xxx-849xxx):")
    for row in rows:
        r = row_to_dict(row)
        konto = r['konto']
        wert = float(r.get('wert', 0) or 0)
        anzahl = int(r.get('anzahl', 0) or 0)
        branch = r.get('branch_number', 'N/A')
        subsidiary = r.get('subsidiary_to_company_ref', 'N/A')
        
        # Prüfe ob Konto in Mechanik enthalten ist
        if (840000 <= konto < 840500) or (840700 <= konto < 847000) or (848000 <= konto <= 849999):
            in_mech += wert
            if abs(wert) > 1000:
                print(f"  {konto}: {wert:,.2f} € ({anzahl} Buchungen, branch={branch}, subsidiary={subsidiary})")
        else:
            ausgeschlossen += wert
            if abs(wert) > 1000:
                print(f"  {konto}: {wert:,.2f} € ({anzahl} Buchungen) ⚠️ AUSGESCHLOSSEN")
    
    print(f"\nGesamt in Mechanik: {in_mech:,.2f} €")
    print(f"Gesamt ausgeschlossen: {ausgeschlossen:,.2f} €")
    print()
    
    # Prüfe ob es 84xxxx Konten gibt, die möglicherweise zu Mechanik gehören sollten
    print("="*80)
    print("PRÜFUNG: SOLLTEN AUSGESCHLOSSENE KONTEN DOCH ENTHALTEN SEIN?")
    print("="*80)
    
    # Prüfe 84xxxx Konten die ausgeschlossen sind
    ausgeschlossen_bereiche = [
        ("8405xx (Karosserie)", 840500, 840599),
        ("8406xx (Lackierung)", 840600, 840699),
        ("847xxx (Clean Park)", 847000, 847999),
    ]
    
    for bezeichnung, von, bis in ausgeschlossen_bereiche:
        query = f"""
            SELECT 
                SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as erlos,
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
            erlos = float(r.get('erlos', 0) or 0)
            anzahl = int(r.get('anzahl', 0) or 0)
            if abs(erlos) > 0:
                print(f"{bezeichnung}: {erlos:,.2f} € ({anzahl} Buchungen)")
    
    # Prüfe ob es andere Bereiche gibt, die zu Mechanik gehören könnten
    print()
    print("="*80)
    print("PRÜFUNG: ANDERE BEREICHE")
    print("="*80)
    
    # Prüfe ob 85xxxx (Lack) zu Mechanik gehören könnte
    query_85 = f"""
        SELECT 
            SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as wert,
            COUNT(*) as anzahl
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 850000 AND 859999
          {firma_filter_umsatz}
          {guv_filter}
    """
    cursor.execute(convert_placeholders(query_85), (datum_von, datum_bis))
    row = cursor.fetchone()
    if row:
        r = row_to_dict(row)
        wert_85 = float(r.get('wert', 0) or 0)
        anzahl_85 = int(r.get('anzahl', 0) or 0)
        if abs(wert_85) > 0:
            print(f"85xxxx (Lack/Sonstige): {wert_85:,.2f} € ({anzahl_85} Buchungen)")
            if abs(wert_85) > 5000:
                print(f"  ⚠️ Großer Wert - könnte zu Mechanik gehören?")
