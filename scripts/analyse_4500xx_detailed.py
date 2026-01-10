#!/usr/bin/env python3
"""
Detaillierte Analyse: 4500xx-Konten
====================================
Prüft welche 45xxxx-Konten mit KST 1-7 existieren und ob sie korrekt zugeordnet sind.
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

print("=" * 120)
print("DETAILLIERTE ANALYSE: 4500xx-Konten")
print("=" * 120)

jahr = 2025
datum_von = "2024-09-01"
datum_bis = "2025-09-01"

firma_filter_kosten = ''
guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"

with db_session() as conn:
    cursor = conn.cursor()
    
    # Alle 45xxxx-Konten mit KST 1-7
    print(f"\n1. ALLE 45xxxx-KONTEN MIT KST 1-7:")
    print(f"   {'Kontenbereich':<30} {'Wert':>15} {'Zuordnung':>30}")
    
    cursor.execute(convert_placeholders(f"""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 1, 4) || 'xx' as konten_4stellig,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 450000 AND 459999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          {firma_filter_kosten}
          {guv_filter}
        GROUP BY konten_4stellig
        ORDER BY konten_4stellig
    """), (datum_von, datum_bis))
    
    gesamt_4500xx = 0
    for row in cursor.fetchall():
        r = row_to_dict(row)
        konten = r['konten_4stellig']
        wert = float(r['wert'] or 0)
        gesamt_4500xx += wert
        
        # Bestimme Zuordnung
        if konten == '4550xx' or konten == '4560xx':
            zuordnung = "Variable (455xx-456xx)"
        else:
            zuordnung = "❓ Unbekannt"
        
        if wert != 0:
            print(f"   {konten:<30} {wert:>15,.2f} € {zuordnung:>30}")
    
    print(f"   {'SUMME 4500xx':<30} {gesamt_4500xx:>15,.2f} €")
    
    # Prüfe welche in direkten Kosten sind
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 450000 AND 459999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          AND NOT (
            nominal_account_number BETWEEN 455000 AND 456999
          )
          {firma_filter_kosten}
          {guv_filter}
    """), (datum_von, datum_bis))
    
    wert_ohne_455456 = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    print(f"\n2. 45xxxx OHNE 455xx-456xx (sollten in direkten Kosten sein?):")
    print(f"   Wert: {wert_ohne_455456:,.2f} €")
    
    # Detailliert: Alle 45xxxx-Konten einzeln
    print(f"\n3. DETAILLIERT: Alle 45xxxx-Konten (erste 3 Ziffern):")
    cursor.execute(convert_placeholders(f"""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 1, 3) || 'xxx' as konten_3stellig,
            COUNT(DISTINCT nominal_account_number) as anzahl_konten,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 450000 AND 459999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          {firma_filter_kosten}
          {guv_filter}
        GROUP BY konten_3stellig
        ORDER BY konten_3stellig
    """), (datum_von, datum_bis))
    
    print(f"   {'Konten (3stellig)':<20} {'Anzahl':>10} {'Wert':>15} {'Zuordnung':>30}")
    for row in cursor.fetchall():
        r = row_to_dict(row)
        konten = r['konten_3stellig']
        anzahl = r['anzahl_konten']
        wert = float(r['wert'] or 0)
        
        if konten.startswith('455') or konten.startswith('456'):
            zuordnung = "Variable (455xx-456xx)"
        else:
            zuordnung = "❓ Sollte in direkten Kosten sein?"
        
        if wert != 0:
            print(f"   {konten:<20} {anzahl:>10} {wert:>15,.2f} € {zuordnung:>30}")
    
    # Prüfe ob 4500xx-4549xx oder 4570xx-4599xx in direkten Kosten fehlen
    print(f"\n4. PRÜFE: 4500xx-4549xx und 4570xx-4599xx (ohne 455xx-456xx):")
    
    for bereich_name, von, bis in [
        ('4500xx-4549xx', 450000, 454999),
        ('4570xx-4599xx', 457000, 459999)
    ]:
        cursor.execute(convert_placeholders(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN %s AND %s
              AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
              {firma_filter_kosten}
              {guv_filter}
        """), (datum_von, datum_bis, von, bis))
        
        wert = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        
        # Prüfe ob in direkten Kosten
        cursor.execute(convert_placeholders(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN %s AND %s
              AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
              AND NOT (
                nominal_account_number BETWEEN 415100 AND 415199
                OR nominal_account_number BETWEEN 424000 AND 424999
                OR nominal_account_number BETWEEN 435500 AND 435599
                OR nominal_account_number BETWEEN 438000 AND 438999
                OR nominal_account_number BETWEEN 455000 AND 456999
                OR nominal_account_number BETWEEN 487000 AND 487099
                OR nominal_account_number BETWEEN 491000 AND 497999
              )
              {firma_filter_kosten}
              {guv_filter}
        """), (datum_von, datum_bis, von, bis))
        
        wert_in_direkten = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        
        print(f"   {bereich_name:<20} Gesamt: {wert:>15,.2f} €, In direkten: {wert_in_direkten:>15,.2f} €")
        if wert != wert_in_direkten:
            print(f"      ⚠️  Differenz: {wert - wert_in_direkten:,.2f} € fehlt in direkten Kosten!")

print(f"\n{'='*120}")
