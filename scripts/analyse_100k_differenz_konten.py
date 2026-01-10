#!/usr/bin/env python3
"""
Analyse: Welche Konten machen die 100.381,57 € Differenz aus?
=============================================================
Suche nach Kontenbereichen, die genau diese Differenz ergeben.
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

print("=" * 120)
print("ANALYSE: Welche Konten machen die 100.381,57 € Differenz aus?")
print("=" * 120)

jahr = 2025
datum_von = "2024-09-01"
datum_bis = "2025-09-01"

firma_filter_kosten = ''
guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"

target_diff = 100381.57

print(f"\nZeitraum: {datum_von} - {datum_bis}")
print(f"Ziel-Differenz: {target_diff:,.2f} €")
print(f"→ Suche Kontenbereiche, die diese Differenz ergeben")
print(f"\n{'='*120}")

with db_session() as conn:
    cursor = conn.cursor()
    
    # Prüfe: Gibt es Kontenbereiche, die in DRIVE direkten Kosten sind,
    # aber möglicherweise in Globalcube als Variable Kosten gezählt werden?
    
    # Teste: Was wenn bestimmte Kontenbereiche in Globalcube als Variable Kosten gezählt werden?
    print(f"\n1. PRÜFE: Kontenbereiche, die möglicherweise in Globalcube als Variable Kosten gezählt werden:")
    
    # Prüfe 4150x genauer (ohne 4151xx)
    # 4151xx ist Variable, aber was ist mit 4150x-4150x (ohne 4151xx)?
    cursor.execute(convert_placeholders(f"""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 1, 4) || 'xx' as konten_4stellig,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 415000 AND 415099
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          {firma_filter_kosten}
          {guv_filter}
        GROUP BY konten_4stellig
        ORDER BY konten_4stellig
    """), (datum_von, datum_bis))
    
    print(f"   {'Konten (4stellig)':<20} {'Wert':>15}")
    summe_4150x = 0
    for row in cursor.fetchall():
        r = row_to_dict(row)
        konten = r['konten_4stellig']
        wert = float(r['wert'] or 0)
        if wert != 0:
            print(f"   {konten:<20} {wert:>15,.2f} €")
            summe_4150x += wert
    
    # Prüfe alle Kontenbereiche, die in direkten Kosten sind, aber möglicherweise falsch zugeordnet sind
    print(f"\n2. PRÜFE: Alle Kontenbereiche in direkten Kosten (detailliert):")
    
    # Gruppiere nach ersten 3 Ziffern für detaillierte Analyse
    cursor.execute(convert_placeholders(f"""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 1, 3) || 'xxx' as konten_3stellig,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
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
        GROUP BY konten_3stellig
        ORDER BY wert DESC
    """), (datum_von, datum_bis))
    
    print(f"   {'Konten (3stellig)':<20} {'Anzahl':>10} {'Wert':>15} {'% von Diff':>12}")
    gesamt = 0
    for row in cursor.fetchall():
        r = row_to_dict(row)
        konten = r['konten_3stellig']
        anzahl = r['anzahl']
        wert = float(r['wert'] or 0)
        if wert != 0:
            prozent_von_diff = (wert / target_diff) * 100 if target_diff > 0 else 0
            print(f"   {konten:<20} {anzahl:>10} {wert:>15,.2f} € {prozent_von_diff:>11.1f}%")
            gesamt += wert
    
    print(f"   {'SUMME':<20} {'':>10} {gesamt:>15,.2f} €")
    
    # Prüfe: Gibt es Konten, die nahe an der Differenz sind?
    print(f"\n3. PRÜFE: Kontenbereiche, die nahe an der Differenz sind (±10%):")
    cursor.execute(convert_placeholders(f"""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 1, 3) || 'xxx' as konten_3stellig,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
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
        GROUP BY konten_3stellig
        HAVING ABS(COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) - %s) <= %s * 0.1
        ORDER BY ABS(COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) - %s)
    """), (datum_von, datum_bis, target_diff, target_diff, target_diff))
    
    gefunden = False
    for row in cursor.fetchall():
        r = row_to_dict(row)
        konten = r['konten_3stellig']
        wert = float(r['wert'] or 0)
        diff = abs(wert - target_diff)
        print(f"   {konten:<20} {wert:>15,.2f} € (Diff: {diff:,.2f} €)")
        gefunden = True
    
    if not gefunden:
        print(f"   Keine einzelnen Kontenbereiche gefunden, die genau die Differenz ergeben")
        print(f"   → Die Differenz kommt wahrscheinlich aus einer Kombination mehrerer Bereiche")

print(f"\n{'='*120}")
