#!/usr/bin/env python3
"""
Analyse aller 743xxx Konten
============================
TAG 196: Prüft ob weitere 743xxx Konten ausgeschlossen werden sollten
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
print("ANALYSE ALLER 743xxx KONTEN")
print("="*80)
print(f"Zeitraum: {datum_von} bis {datum_bis}")
print()

with db_session() as conn:
    cursor = conn.cursor()
    
    # Alle 743xxx Konten detailliert
    print("="*80)
    print("ALLE 743xxx KONTEN (YTD)")
    print("="*80)
    
    query = f"""
        SELECT 
            nominal_account_number as konto,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert,
            COUNT(*) as anzahl,
            branch_number,
            subsidiary_to_company_ref,
            MIN(accounting_date) as erste_buchung,
            MAX(accounting_date) as letzte_buchung
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 743000 AND 743999
          {firma_filter_einsatz}
          {guv_filter}
        GROUP BY nominal_account_number, branch_number, subsidiary_to_company_ref
        ORDER BY nominal_account_number, branch_number, subsidiary_to_company_ref
    """
    
    cursor.execute(convert_placeholders(query), (datum_von, datum_bis))
    rows = cursor.fetchall()
    
    total_743xxx = 0
    konten_liste = []
    
    for row in rows:
        r = row_to_dict(row)
        konto = r['konto']
        wert = float(r.get('wert', 0) or 0)
        anzahl = int(r.get('anzahl', 0) or 0)
        branch = r.get('branch_number', 'N/A')
        subsidiary = r.get('subsidiary_to_company_ref', 'N/A')
        erste = r.get('erste_buchung', 'N/A')
        letzte = r.get('letzte_buchung', 'N/A')
        
        total_743xxx += wert
        konten_liste.append({
            'konto': konto,
            'wert': wert,
            'anzahl': anzahl,
            'branch': branch,
            'subsidiary': subsidiary
        })
        
        print(f"  {konto}: {wert:,.2f} € ({anzahl} Buchungen, branch={branch}, subsidiary={subsidiary})")
        print(f"    Erste Buchung: {erste}, Letzte Buchung: {letzte}")
    
    print()
    print(f"Gesamt 743xxx: {total_743xxx:,.2f} €")
    print()
    
    # Prüfe ob 743002 korrekt ausgeschlossen wird
    print("="*80)
    print("PRÜFUNG: 743002 AUSSCHLUSS")
    print("="*80)
    
    query_743002 = f"""
        SELECT 
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert,
            COUNT(*) as anzahl
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number = 743002
          {firma_filter_einsatz}
          {guv_filter}
    """
    
    cursor.execute(convert_placeholders(query_743002), (datum_von, datum_bis))
    row = cursor.fetchone()
    if row:
        r = row_to_dict(row)
        wert_743002 = float(r.get('wert', 0) or 0)
        anzahl_743002 = int(r.get('anzahl', 0) or 0)
        print(f"743002 Wert (sollte ausgeschlossen werden): {wert_743002:,.2f} € ({anzahl_743002} Buchungen)")
        print(f"  → Dieser Wert sollte NICHT in Einsatz YTD enthalten sein!")
    
    # Prüfe ob andere 743xxx Konten ähnliche Eigenschaften haben
    print()
    print("="*80)
    print("VERGLEICH: 743001 vs 743002")
    print("="*80)
    
    wert_743001 = sum(k['wert'] for k in konten_liste if k['konto'] == 743001)
    wert_743002 = sum(k['wert'] for k in konten_liste if k['konto'] == 743002)
    
    print(f"743001: {wert_743001:,.2f} € (ist enthalten)")
    print(f"743002: {wert_743002:,.2f} € (sollte ausgeschlossen sein)")
    print()
    print("Frage: Sollten weitere 743xxx Konten ausgeschlossen werden?")
    print("  → 743001 ist 'EW Fremdleistungen' (allgemein)")
    print("  → 743002 ist 'EW Fremdleistungen für Kunden' (spezifisch)")
    print("  → Möglicherweise sollten ALLE 743xxx ausgeschlossen werden?")
    
    # Prüfe Gesamt-Einsatz mit und ohne 743xxx
    print()
    print("="*80)
    print("VERGLEICH: Einsatz YTD mit/ohne 743xxx")
    print("="*80)
    
    # Mit 743002 (aktuell)
    query_mit = f"""
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
    
    cursor.execute(convert_placeholders(query_mit), (datum_von, datum_bis))
    row = cursor.fetchone()
    wert_mit_743002_ausgeschlossen = float(row_to_dict(row).get('wert', 0) or 0)
    
    # Ohne alle 743xxx
    query_ohne_alle_743xxx = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND nominal_account_number NOT BETWEEN 743000 AND 743999
          {firma_filter_einsatz}
          {guv_filter}
    """
    
    cursor.execute(convert_placeholders(query_ohne_alle_743xxx), (datum_von, datum_bis))
    row = cursor.fetchone()
    wert_ohne_alle_743xxx = float(row_to_dict(row).get('wert', 0) or 0)
    
    print(f"Einsatz YTD mit 743002 ausgeschlossen: {wert_mit_743002_ausgeschlossen:,.2f} €")
    print(f"Einsatz YTD ohne alle 743xxx: {wert_ohne_alle_743xxx:,.2f} €")
    print(f"Differenz (743001 + 743003-743999): {wert_mit_743002_ausgeschlossen - wert_ohne_alle_743xxx:,.2f} €")
    print()
    print(f"GlobalCube Referenz: 9.191.864,00 €")
    print(f"DRIVE aktuell (743002 ausgeschlossen): 9.207.314,53 €")
    print(f"DRIVE ohne alle 743xxx: {wert_ohne_alle_743xxx:,.2f} €")
    print()
    print(f"Differenz zu GlobalCube:")
    print(f"  Mit 743002 ausgeschlossen: +15.450,53 €")
    print(f"  Ohne alle 743xxx: {wert_ohne_alle_743xxx - 9191864:,.2f} €")
    
    print()
    print("="*80)
    print("EMPFEHLUNG")
    print("="*80)
    print("Prüfe ob GlobalCube ALLE 743xxx Konten ausschließt (nicht nur 743002)")
    print("Wenn ja, dann sollte der Filter erweitert werden:")
    print("  AND nominal_account_number NOT BETWEEN 743000 AND 743999")
