#!/usr/bin/env python3
"""
Analyse: Welche Konten fehlen in direkten Kosten?
==================================================
Vergleicht alle Konten 40xxxx-48xxxx mit KST 1-7 und identifiziert,
welche möglicherweise in Globalcube als direkte Kosten gezählt werden,
aber in DRIVE nicht.
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

print("=" * 120)
print("ANALYSE: Welche Konten fehlen in direkten Kosten?")
print("=" * 120)

jahr = 2025
datum_von = "2024-09-01"
datum_bis = "2025-09-01"

firma_filter_kosten = ''
guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"

# DB3-Differenz: -100.381,57 €
# Das bedeutet: DRIVE hat 100.381,57 € WENIGER direkte Kosten als Globalcube
# → DRIVE zählt bestimmte Konten NICHT als direkte Kosten, die Globalcube zählt

print(f"\nZeitraum: {datum_von} - {datum_bis}")
print(f"DB3-Differenz: -100.381,57 €")
print(f"→ DRIVE hat 100.381,57 € WENIGER direkte Kosten als Globalcube")
print(f"→ Suche nach Konten, die möglicherweise fehlen...")
print(f"\n{'='*120}")

with db_session() as conn:
    cursor = conn.cursor()
    
    # 1. Alle Konten 40xxxx-48xxxx mit KST 1-7, gruppiert nach Kontenbereich
    print(f"\n1. ALLE KONTEN 40xxxx-48xxxx MIT KST 1-7 (nach Kontenbereichen):")
    print(f"   {'Kontenbereich':<50} {'Wert':>15} {'In direkten Kosten?':>20}")
    
    cursor.execute(convert_placeholders(f"""
        SELECT 
            CASE 
                WHEN nominal_account_number BETWEEN 400000 AND 409999 THEN '4000xx'
                WHEN nominal_account_number BETWEEN 410000 AND 419999 THEN '4100xx'
                WHEN nominal_account_number BETWEEN 420000 AND 429999 THEN '4200xx'
                WHEN nominal_account_number BETWEEN 430000 AND 439999 THEN '4300xx'
                WHEN nominal_account_number BETWEEN 440000 AND 449999 THEN '4400xx'
                WHEN nominal_account_number BETWEEN 450000 AND 459999 THEN '4500xx'
                WHEN nominal_account_number BETWEEN 460000 AND 469999 THEN '4600xx'
                WHEN nominal_account_number BETWEEN 470000 AND 479999 THEN '4700xx'
                WHEN nominal_account_number BETWEEN 480000 AND 489999 THEN '4800xx'
                ELSE 'Sonstige'
            END as kontenbereich,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          {firma_filter_kosten}
          {guv_filter}
        GROUP BY kontenbereich
        ORDER BY kontenbereich
    """), (datum_von, datum_bis))
    
    alle_konten = {}
    for row in cursor.fetchall():
        r = row_to_dict(row)
        kontenbereich = r['kontenbereich']
        wert = float(r['wert'] or 0)
        alle_konten[kontenbereich] = wert
    
    # 2. Prüfe welche in direkten Kosten enthalten sind
    for kontenbereich, wert_gesamt in sorted(alle_konten.items()):
        if wert_gesamt == 0:
            continue
        
        # Bestimme Kontenbereich-Grenzen
        if kontenbereich == '4000xx':
            von, bis = 400000, 409999
        elif kontenbereich == '4100xx':
            von, bis = 410000, 419999
        elif kontenbereich == '4200xx':
            von, bis = 420000, 429999
        elif kontenbereich == '4300xx':
            von, bis = 430000, 439999
        elif kontenbereich == '4400xx':
            von, bis = 440000, 449999
        elif kontenbereich == '4500xx':
            von, bis = 450000, 459999
        elif kontenbereich == '4600xx':
            von, bis = 460000, 469999
        elif kontenbereich == '4700xx':
            von, bis = 470000, 479999
        elif kontenbereich == '4800xx':
            von, bis = 480000, 489999
        else:
            continue
        
        # Wert in direkten Kosten
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
        diff = wert_gesamt - wert_in_direkten
        
        status = "✅" if diff == 0 else "⚠️"
        in_direkten = "Ja" if wert_in_direkten > 0 else "Nein"
        
        print(f"   {kontenbereich:<50} {wert_gesamt:>15,.2f} € {in_direkten:>20}")
        if diff != 0:
            print(f"      → Differenz: {diff:>15,.2f} € (nicht in direkten Kosten)")
    
    # 3. Detaillierte Analyse: 4200xx (ohne 424xx)
    print(f"\n2. DETAILLIERTE ANALYSE: 4200xx (ohne 424xx):")
    cursor.execute(convert_placeholders(f"""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 1, 4) || 'xx' as konten_4stellig,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 420000 AND 429999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          AND NOT (nominal_account_number BETWEEN 424000 AND 424999)
          {firma_filter_kosten}
          {guv_filter}
        GROUP BY konten_4stellig
        ORDER BY konten_4stellig
    """), (datum_von, datum_bis))
    
    print(f"   {'Konten':<20} {'Wert':>15} {'In direkten Kosten?':>20}")
    for row in cursor.fetchall():
        r = row_to_dict(row)
        konten = r['konten_4stellig']
        wert = float(r['wert'] or 0)
        if wert != 0:
            print(f"   {konten:<20} {wert:>15,.2f} €")
    
    # 4. Detaillierte Analyse: 4400xx (ohne 4355xx, 438xx)
    print(f"\n3. DETAILLIERTE ANALYSE: 4400xx (ohne 4355xx, 438xx):")
    cursor.execute(convert_placeholders(f"""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 1, 4) || 'xx' as konten_4stellig,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 440000 AND 449999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          AND NOT (nominal_account_number BETWEEN 435500 AND 435599
                   OR nominal_account_number BETWEEN 438000 AND 438999)
          {firma_filter_kosten}
          {guv_filter}
        GROUP BY konten_4stellig
        ORDER BY konten_4stellig
    """), (datum_von, datum_bis))
    
    print(f"   {'Konten':<20} {'Wert':>15} {'In direkten Kosten?':>20}")
    for row in cursor.fetchall():
        r = row_to_dict(row)
        konten = r['konten_4stellig']
        wert = float(r['wert'] or 0)
        if wert != 0:
            print(f"   {konten:<20} {wert:>15,.2f} €")
    
    # 5. Prüfe spezielle Kontenbereiche, die möglicherweise fehlen
    print(f"\n4. PRÜFE SPEZIELLE KONTENBEREICHE:")
    
    # 498xx mit KST 1-7 (sollte eigentlich nicht existieren, da 498xx zu indirekten Kosten gehört)
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 498000 AND 499999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          {firma_filter_kosten}
          {guv_filter}
    """), (datum_von, datum_bis))
    wert_498xx_kst17 = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    if wert_498xx_kst17 != 0:
        print(f"   ⚠️  498xx mit KST 1-7: {wert_498xx_kst17:,.2f} €")
        print(f"      → Sollte in indirekten Kosten sein, nicht in direkten!")
    
    # 424xx/438xx mit KST 4/5 (aktuell in indirekten Kosten, aber vielleicht sollten sie in direkten sein?)
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND ((nominal_account_number BETWEEN 424000 AND 424999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('4','5'))
               OR (nominal_account_number BETWEEN 438000 AND 438999
                   AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('4','5')))
          {firma_filter_kosten}
          {guv_filter}
    """), (datum_von, datum_bis))
    wert_424438_kst45 = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    print(f"   424xx/438xx KST 4/5: {wert_424438_kst45:,.2f} €")
    print(f"      → Aktuell in indirekten Kosten (nur KST 1-3,6-7)")
    print(f"      → Wenn zu direkten Kosten: DB3 würde um {wert_424438_kst45:,.2f} € sinken")
    
    # 6. Zusammenfassung
    print(f"\n{'='*120}")
    print("ZUSAMMENFASSUNG:")
    print(f"{'='*120}")
    print(f"   DB3-Differenz: -100.381,57 €")
    print(f"   → DRIVE hat 100.381,57 € WENIGER direkte Kosten als Globalcube")
    print(f"\n   Mögliche Ursachen:")
    print(f"   1. Kontenbereiche fehlen in direkten Kosten")
    print(f"   2. 424xx/438xx KST 4/5 gehören zu direkten Kosten? ({wert_424438_kst45:,.2f} €)")
    print(f"   3. Andere Filter-Logik in Globalcube?")

print(f"\n{'='*120}")
