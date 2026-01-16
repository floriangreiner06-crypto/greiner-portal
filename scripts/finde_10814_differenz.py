#!/usr/bin/env python3
"""
Finde fehlende 10.814,14 € für Mechanik+Karo
============================================
TAG 196: Analysiert welche Konten fehlen könnten
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

target_differenz = 10814.14  # Fehlende 10.814,14 €

print("="*80)
print("FINDE FEHLENDE 10.814,14 € FÜR MECHANIK+KARO")
print("="*80)
print(f"Zeitraum: {datum_von} bis {datum_bis}")
print(f"DRIVE Mechanik (inkl. CP): 75.604,86 €")
print(f"GlobalCube Mechanik+Karo: 86.419,00 €")
print(f"Fehlende Differenz: {target_differenz:,.2f} €")
print()

with db_session() as conn:
    cursor = conn.cursor()
    
    # Aktuelle Mechanik-Berechnung (ohne 8405xx, ohne 8406xx, MIT 847xxx)
    query_mech_erlos = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 840000 AND 849999
          AND nominal_account_number NOT BETWEEN 840500 AND 840599
          AND nominal_account_number NOT BETWEEN 840600 AND 840699
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
          {firma_filter_einsatz}
          {guv_filter}
    """
    cursor.execute(convert_placeholders(query_mech_einsatz), (datum_von, datum_bis))
    mech_einsatz = float(row_to_dict(cursor.fetchone()).get('wert', 0) or 0)
    
    mech_be = mech_erlos - mech_einsatz
    
    print("="*80)
    print("AKTUELLE MECHANIK-BERECHNUNG")
    print("="*80)
    print(f"Erlös: {mech_erlos:,.2f} €")
    print(f"Einsatz: {mech_einsatz:,.2f} €")
    print(f"Bruttoertrag: {mech_be:,.2f} €")
    print()
    
    # Prüfe ob 8406xx (Lackierung) doch enthalten sein sollte
    query_8406 = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 840600 AND 840699
          {firma_filter_umsatz}
          {guv_filter}
    """
    cursor.execute(convert_placeholders(query_8406), (datum_von, datum_bis))
    wert_8406 = float(row_to_dict(cursor.fetchone()).get('wert', 0) or 0)
    
    query_746 = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 746000 AND 746999
          AND nominal_account_number != 743002
          {firma_filter_einsatz}
          {guv_filter}
    """
    cursor.execute(convert_placeholders(query_746), (datum_von, datum_bis))
    wert_746 = float(row_to_dict(cursor.fetchone()).get('wert', 0) or 0)
    
    lack_be = wert_8406 - wert_746
    
    print("="*80)
    print("PRÜFUNG: LACKIERUNG (8406xx/746xxx)")
    print("="*80)
    print(f"8406xx Erlös: {wert_8406:,.2f} €")
    print(f"746xxx Einsatz: {wert_746:,.2f} €")
    print(f"Lackierung BE: {lack_be:,.2f} €")
    print()
    print(f"Mechanik + Lackierung: {mech_be + lack_be:,.2f} €")
    print(f"GlobalCube: {86419:,.2f} €")
    print(f"Differenz: {mech_be + lack_be - 86419:+,.2f} €")
    print()
    
    # Prüfe alle 84xxxx Konten die ausgeschlossen sind
    print("="*80)
    print("AUSGESCHLOSSENE 84XXXX KONTEN")
    print("="*80)
    
    ausgeschlossen_bereiche = [
        ("8405xx (Karosserie)", 840500, 840599),
        ("8406xx (Lackierung)", 840600, 840699),
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
    
    # Prüfe ob es andere 84xxxx Konten gibt, die nahe der Differenz sind
    print()
    print("="*80)
    print("SUCHE NACH KONTEN MIT WERTEN NAHE DER DIFFERENZ")
    print("="*80)
    
    # Alle 84xxxx Konten (außer ausgeschlossene)
    query_all_84 = f"""
        SELECT 
            nominal_account_number as konto,
            SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as wert,
            COUNT(*) as anzahl
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 840000 AND 849999
          AND nominal_account_number NOT BETWEEN 840500 AND 840599
          AND nominal_account_number NOT BETWEEN 840600 AND 840699
          {firma_filter_umsatz}
          {guv_filter}
        GROUP BY nominal_account_number
        HAVING ABS(SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)) > 5000
        ORDER BY ABS(SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)) DESC
        LIMIT 30
    """
    cursor.execute(convert_placeholders(query_all_84), (datum_von, datum_bis))
    rows = cursor.fetchall()
    
    print("Top 84xxxx Konten (außer Karosserie/Lack):")
    for row in rows:
        r = row_to_dict(row)
        konto = r['konto']
        wert = float(r.get('wert', 0) or 0)
        anzahl = int(r.get('anzahl', 0) or 0)
        diff = abs(abs(wert) - target_differenz)
        if diff < target_differenz * 0.2:  # ±20%
            print(f"  {konto}: {wert:,.2f} € ({anzahl} Buchungen) ⚠️ NAHE DIFFERENZ (Abweichung: {diff:,.2f} €)")
        else:
            print(f"  {konto}: {wert:,.2f} € ({anzahl} Buchungen)")
    
    # Prüfe ob es 84xxxx Konten gibt, die möglicherweise ausgeschlossen werden sollten
    print()
    print("="*80)
    print("PRÜFUNG: SOLLTEN WEITERE KONTEN AUSGESCHLOSSEN WERDEN?")
    print("="*80)
    
    # Prüfe 84xxxx Konten die möglicherweise nicht zu Mechanik gehören
    moegliche_ausschlüsse = [
        ("847xxx (Clean Park - bereits in Mechanik)", 847000, 847999),
        ("848xxx (falls existiert)", 848000, 848999),
        ("849xxx (falls existiert)", 849000, 849999),
    ]
    
    for bezeichnung, von, bis in moegliche_ausschlüsse:
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
            if abs(wert) > 0:
                print(f"{bezeichnung}: {wert:,.2f} € ({anzahl} Buchungen)")
                if abs(wert) > 1000:
                    print(f"  ⚠️ Großer Wert - könnte ausgeschlossen werden sollten!")
