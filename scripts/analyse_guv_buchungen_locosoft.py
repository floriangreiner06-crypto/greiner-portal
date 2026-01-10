#!/usr/bin/env python3
"""
Analyse: G&V-Abschlussbuchungen und fehlende Buchungen
======================================================
Prüft:
1. Welche Buchungen werden durch GuV-Filter ausgeschlossen?
2. Gibt es Buchungen, die in Globalcube berücksichtigt werden, aber in Locosoft fehlen?
3. Werden alle relevanten Buchungen aus Locosoft importiert?
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

print("=" * 120)
print("ANALYSE: G&V-Abschlussbuchungen und fehlende Buchungen")
print("=" * 120)

jahr = 2025
datum_von = "2024-09-01"
datum_bis = "2025-09-01"

firma_filter_kosten = ''
guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"

print(f"\nZeitraum: {datum_von} - {datum_bis}")
print(f"DB3-Differenz: -100.381,57 €")
print(f"→ Prüfe, ob Buchungen fehlen oder falsch gefiltert werden")
print(f"\n{'='*120}")

with db_session() as conn:
    cursor = conn.cursor()
    
    # 1. G&V-Abschlussbuchungen analysieren
    print(f"\n1. G&V-ABSCHLUSSBUCHUNGEN (werden aktuell ausgeschlossen):")
    print(f"   {'Kontenbereich':<30} {'Anzahl':>10} {'Wert (SOLL)':>15} {'Wert (HABEN)':>15} {'Summe':>15}")
    
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
                WHEN nominal_account_number BETWEEN 700000 AND 799999 THEN '7000xx (Einsatz)'
                WHEN nominal_account_number BETWEEN 800000 AND 899999 THEN '8000xx (Umsatz)'
                ELSE 'Sonstige'
            END as kontenbereich,
            COUNT(*) as anzahl,
            COALESCE(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE 0 END)/100.0, 0) as wert_soll,
            COALESCE(SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE 0 END)/100.0, 0) as wert_haben,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as summe
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND posting_text LIKE '%%G&V-Abschluss%%'
          {firma_filter_kosten}
        GROUP BY kontenbereich
        ORDER BY kontenbereich
    """), (datum_von, datum_bis))
    
    guv_gesamt = 0
    for row in cursor.fetchall():
        r = row_to_dict(row)
        kontenbereich = r['kontenbereich']
        anzahl = r['anzahl']
        wert_soll = float(r['wert_soll'] or 0)
        wert_haben = float(r['wert_haben'] or 0)
        summe = float(r['summe'] or 0)
        guv_gesamt += abs(summe)
        
        if anzahl > 0:
            print(f"   {kontenbereich:<30} {anzahl:>10} {wert_soll:>15,.2f} € {wert_haben:>15,.2f} € {summe:>15,.2f} €")
    
    print(f"   {'GESAMT (absolut)':<30} {'':>10} {'':>15} {'':>15} {guv_gesamt:>15,.2f} €")
    
    # 2. Prüfe direkte Kosten MIT und OHNE GuV-Filter
    print(f"\n2. DIREKTE KOSTEN - VERGLEICH MIT/OHNE GuV-FILTER:")
    
    # Mit GuV-Filter (aktuell)
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
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
    """), (datum_von, datum_bis))
    direkte_mit_guv = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Ohne GuV-Filter
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
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
    """), (datum_von, datum_bis))
    direkte_ohne_guv = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    diff_guv = direkte_ohne_guv - direkte_mit_guv
    print(f"   Mit GuV-Filter (aktuell):    {direkte_mit_guv:>15,.2f} €")
    print(f"   Ohne GuV-Filter:             {direkte_ohne_guv:>15,.2f} €")
    print(f"   Differenz (GuV ausgeschlossen): {diff_guv:>15,.2f} €")
    
    # 3. Prüfe G&V-Abschlussbuchungen in direkten Kosten
    print(f"\n3. G&V-ABSCHLUSSBUCHUNGEN IN DIREKTEN KOSTEN (40xxxx-48xxxx KST 1-7):")
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
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
          AND posting_text LIKE '%%G&V-Abschluss%%'
          {firma_filter_kosten}
    """), (datum_von, datum_bis))
    guv_in_direkten = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    print(f"   G&V-Abschluss in direkten Kosten: {guv_in_direkten:>15,.2f} €")
    print(f"   → Wenn diese hinzugefügt werden: {direkte_mit_guv + guv_in_direkten:>15,.2f} €")
    print(f"   → DB3 würde um {guv_in_direkten:,.2f} € sinken")
    
    # 4. Prüfe indirekte Kosten MIT und OHNE GuV-Filter
    print(f"\n4. INDIREKTE KOSTEN - VERGLEICH MIT/OHNE GuV-FILTER:")
    
    # Mit GuV-Filter (aktuell)
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND (
            (nominal_account_number BETWEEN 400000 AND 499999
             AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
            OR (nominal_account_number BETWEEN 424000 AND 424999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR (nominal_account_number BETWEEN 438000 AND 438999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR nominal_account_number BETWEEN 498000 AND 499999
            OR (nominal_account_number BETWEEN 891000 AND 896999
                AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
          )
          {firma_filter_kosten}
          {guv_filter}
    """), (datum_von, datum_bis))
    indirekte_mit_guv = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Ohne GuV-Filter
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND (
            (nominal_account_number BETWEEN 400000 AND 499999
             AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
            OR (nominal_account_number BETWEEN 424000 AND 424999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR (nominal_account_number BETWEEN 438000 AND 438999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR nominal_account_number BETWEEN 498000 AND 499999
            OR (nominal_account_number BETWEEN 891000 AND 896999
                AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
          )
          {firma_filter_kosten}
    """), (datum_von, datum_bis))
    indirekte_ohne_guv = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    diff_guv_ind = indirekte_ohne_guv - indirekte_mit_guv
    print(f"   Mit GuV-Filter (aktuell):    {indirekte_mit_guv:>15,.2f} €")
    print(f"   Ohne GuV-Filter:             {indirekte_ohne_guv:>15,.2f} €")
    print(f"   Differenz (GuV ausgeschlossen): {diff_guv_ind:>15,.2f} €")
    
    # 5. Prüfe G&V-Abschlussbuchungen in indirekten Kosten
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND (
            (nominal_account_number BETWEEN 400000 AND 499999
             AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
            OR (nominal_account_number BETWEEN 424000 AND 424999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR (nominal_account_number BETWEEN 438000 AND 438999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR nominal_account_number BETWEEN 498000 AND 499999
            OR (nominal_account_number BETWEEN 891000 AND 896999
                AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
          )
          AND posting_text LIKE '%%G&V-Abschluss%%'
          {firma_filter_kosten}
    """), (datum_von, datum_bis))
    guv_in_indirekten = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    print(f"   G&V-Abschluss in indirekten Kosten: {guv_in_indirekten:>15,.2f} €")
    
    # 6. Zusammenfassung
    print(f"\n{'='*120}")
    print("ZUSAMMENFASSUNG:")
    print(f"{'='*120}")
    print(f"   DB3-Differenz: -100.381,57 €")
    print(f"   → DRIVE hat 100.381,57 € WENIGER direkte Kosten als Globalcube")
    print(f"\n   GuV-Abschlussbuchungen:")
    print(f"   - In direkten Kosten: {guv_in_direkten:>15,.2f} €")
    print(f"   - In indirekten Kosten: {guv_in_indirekten:>15,.2f} €")
    print(f"   - Gesamt ausgeschlossen: {diff_guv + diff_guv_ind:>15,.2f} €")
    print(f"\n   ⚠️  WICHTIG: Globalcube ist ein Reporting-System!")
    print(f"   → Globalcube könnte G&V-Abschlussbuchungen anders behandeln")
    print(f"   → Oder: Globalcube hat Zugriff auf andere/weitere Buchungen")
    print(f"\n   Nächste Schritte:")
    print(f"   1. Prüfe, ob Globalcube G&V-Abschlussbuchungen einbezieht")
    print(f"   2. Prüfe, ob es Buchungen gibt, die in Globalcube, aber nicht in Locosoft sind")
    print(f"   3. Prüfe, ob der Import aus Locosoft vollständig ist")

print(f"\n{'='*120}")
