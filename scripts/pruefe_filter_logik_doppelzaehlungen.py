#!/usr/bin/env python3
"""
Prüft die Filter-Logik auf Doppelzählungen und Logikfehler
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_connection import get_db
from decimal import Decimal

def main():
    conn = get_db()
    cursor = conn.cursor()
    
    print("="*100)
    print("PRÜFUNG: FILTER-LOGIK AUF DOPPELZÄHLUNGEN")
    print("="*100)
    
    datum_von_ytd = '2025-09-01'
    datum_bis = '2026-01-01'
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    
    # Aktueller Einsatz-Filter für Gesamtbetrieb
    firma_filter_einsatz = """AND (
            ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
            OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
            OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
        )"""
    
    # Prüfe: Gibt es Buchungen, die durch MEHRERE Filter-Teile erfasst werden?
    print("\n1. PRÜFUNG: DOPPELZÄHLUNGEN IM EINSATZ-FILTER")
    print("-"*100)
    
    # Teil 1: Deggendorf Stellantis
    query_teil1 = f"""
        SELECT COUNT(*) as anzahl, 
               SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) / 100.0 as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
          {guv_filter}
    """
    cursor.execute(query_teil1, (datum_von_ytd, datum_bis))
    teil1 = cursor.fetchone()
    teil1_anzahl = teil1[0]
    teil1_wert = Decimal(str(teil1[1] or 0))
    
    # Teil 2: Landau
    query_teil2 = f"""
        SELECT COUNT(*) as anzahl, 
               SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) / 100.0 as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND (branch_number = 3 AND subsidiary_to_company_ref = 1)
          {guv_filter}
    """
    cursor.execute(query_teil2, (datum_von_ytd, datum_bis))
    teil2 = cursor.fetchone()
    teil2_anzahl = teil2[0]
    teil2_wert = Decimal(str(teil2[1] or 0))
    
    # Teil 3: Hyundai
    query_teil3 = f"""
        SELECT COUNT(*) as anzahl, 
               SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) / 100.0 as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
          {guv_filter}
    """
    cursor.execute(query_teil3, (datum_von_ytd, datum_bis))
    teil3 = cursor.fetchone()
    teil3_anzahl = teil3[0]
    teil3_wert = Decimal(str(teil3[1] or 0))
    
    # Gesamt mit Filter
    query_gesamt = f"""
        SELECT COUNT(*) as anzahl, 
               SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) / 100.0 as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          {firma_filter_einsatz}
          {guv_filter}
    """
    cursor.execute(query_gesamt, (datum_von_ytd, datum_bis))
    gesamt = cursor.fetchone()
    gesamt_anzahl = gesamt[0]
    gesamt_wert = Decimal(str(gesamt[1] or 0))
    
    summe_teile_anzahl = teil1_anzahl + teil2_anzahl + teil3_anzahl
    summe_teile_wert = teil1_wert + teil2_wert + teil3_wert
    
    print(f"\nTeil 1 (Deggendorf Stellantis): {teil1_anzahl:>8} Buchungen, {teil1_wert:>15,.2f} €")
    print(f"Teil 2 (Landau):                  {teil2_anzahl:>8} Buchungen, {teil2_wert:>15,.2f} €")
    print(f"Teil 3 (Hyundai):                 {teil3_anzahl:>8} Buchungen, {teil3_wert:>15,.2f} €")
    print(f"{'='*60}")
    print(f"Summe der Teile:                 {summe_teile_anzahl:>8} Buchungen, {summe_teile_wert:>15,.2f} €")
    print(f"Gesamt mit Filter:                {gesamt_anzahl:>8} Buchungen, {gesamt_wert:>15,.2f} €")
    
    if summe_teile_anzahl != gesamt_anzahl or summe_teile_wert != gesamt_wert:
        print(f"\n⚠️ WARNUNG: Unterschied zwischen Summe der Teile und Gesamt!")
        print(f"   Differenz Buchungen: {abs(summe_teile_anzahl - gesamt_anzahl)}")
        print(f"   Differenz Wert:      {abs(summe_teile_wert - gesamt_wert):,.2f} €")
        print(f"\n   → Mögliche Doppelzählungen oder Logikfehler!")
    else:
        print(f"\n✅ Keine Doppelzählungen erkannt")
    
    # Prüfe: Gibt es Buchungen, die durch Teil 1 UND Teil 2 erfasst werden?
    print("\n2. PRÜFUNG: ÜBERSCHNEIDUNGEN ZWISCHEN TEIL 1 UND TEIL 2")
    print("-"*100)
    
    query_ueberschneidung_12 = f"""
        SELECT COUNT(*) as anzahl, 
               SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) / 100.0 as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
          AND (branch_number = 3 AND subsidiary_to_company_ref = 1)
          {guv_filter}
    """
    cursor.execute(query_ueberschneidung_12, (datum_von_ytd, datum_bis))
    ueberschneidung_12 = cursor.fetchone()
    ueberschneidung_12_anzahl = ueberschneidung_12[0]
    ueberschneidung_12_wert = Decimal(str(ueberschneidung_12[1] or 0))
    
    if ueberschneidung_12_anzahl > 0:
        print(f"\n⚠️ WARNUNG: {ueberschneidung_12_anzahl} Buchungen werden durch Teil 1 UND Teil 2 erfasst!")
        print(f"   Wert: {ueberschneidung_12_wert:,.2f} €")
    else:
        print(f"\n✅ Keine Überschneidung zwischen Teil 1 und Teil 2")
    
    # Prüfe: Gibt es Buchungen, die durch Teil 1 UND Teil 3 erfasst werden?
    print("\n3. PRÜFUNG: ÜBERSCHNEIDUNGEN ZWISCHEN TEIL 1 UND TEIL 3")
    print("-"*100)
    
    query_ueberschneidung_13 = f"""
        SELECT COUNT(*) as anzahl, 
               SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) / 100.0 as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
          AND (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
          {guv_filter}
    """
    cursor.execute(query_ueberschneidung_13, (datum_von_ytd, datum_bis))
    ueberschneidung_13 = cursor.fetchone()
    ueberschneidung_13_anzahl = ueberschneidung_13[0]
    ueberschneidung_13_wert = Decimal(str(ueberschneidung_13[1] or 0))
    
    if ueberschneidung_13_anzahl > 0:
        print(f"\n⚠️ WARNUNG: {ueberschneidung_13_anzahl} Buchungen werden durch Teil 1 UND Teil 3 erfasst!")
        print(f"   Wert: {ueberschneidung_13_wert:,.2f} €")
    else:
        print(f"\n✅ Keine Überschneidung zwischen Teil 1 und Teil 3")
    
    # Prüfe: 74xxxx Konten mit branch=1 - werden sie korrekt erfasst?
    print("\n4. PRÜFUNG: 74XXXX KONTEN MIT BRANCH=1")
    print("-"*100)
    
    query_74xxxx_branch1 = f"""
        SELECT COUNT(*) as anzahl, 
               SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) / 100.0 as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 740000 AND 749999
          AND branch_number = 1
          AND subsidiary_to_company_ref = 1
          {guv_filter}
    """
    cursor.execute(query_74xxxx_branch1, (datum_von_ytd, datum_bis))
    konten_74xxxx_branch1 = cursor.fetchone()
    konten_74xxxx_branch1_anzahl = konten_74xxxx_branch1[0]
    konten_74xxxx_branch1_wert = Decimal(str(konten_74xxxx_branch1[1] or 0))
    
    print(f"\n74xxxx Konten mit branch=1, subsidiary=1:")
    print(f"  Anzahl: {konten_74xxxx_branch1_anzahl}")
    print(f"  Wert:   {konten_74xxxx_branch1_wert:,.2f} €")
    print(f"\n  → Diese sollten durch Teil 1 erfasst werden (74xxxx AND branch=1)")
    
    # Prüfe: Werden diese durch den Gesamt-Filter erfasst?
    query_74xxxx_gesamt = f"""
        SELECT COUNT(*) as anzahl, 
               SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) / 100.0 as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 740000 AND 749999
          AND branch_number = 1
          AND subsidiary_to_company_ref = 1
          {firma_filter_einsatz}
          {guv_filter}
    """
    cursor.execute(query_74xxxx_gesamt, (datum_von_ytd, datum_bis))
    konten_74xxxx_gesamt = cursor.fetchone()
    konten_74xxxx_gesamt_anzahl = konten_74xxxx_gesamt[0]
    konten_74xxxx_gesamt_wert = Decimal(str(konten_74xxxx_gesamt[1] or 0))
    
    print(f"\n74xxxx Konten mit branch=1, durch Gesamt-Filter erfasst:")
    print(f"  Anzahl: {konten_74xxxx_gesamt_anzahl}")
    print(f"  Wert:   {konten_74xxxx_gesamt_wert:,.2f} €")
    
    if konten_74xxxx_branch1_anzahl != konten_74xxxx_gesamt_anzahl:
        print(f"\n⚠️ WARNUNG: Nicht alle 74xxxx Konten werden durch den Gesamt-Filter erfasst!")
        print(f"   Differenz: {abs(konten_74xxxx_branch1_anzahl - konten_74xxxx_gesamt_anzahl)} Buchungen")
        print(f"   Wert-Differenz: {abs(konten_74xxxx_branch1_wert - konten_74xxxx_gesamt_wert):,.2f} €")
    
    conn.close()

if __name__ == '__main__':
    main()
