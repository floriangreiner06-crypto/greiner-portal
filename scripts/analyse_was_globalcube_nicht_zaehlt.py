#!/usr/bin/env python3
"""
Analyse: Was zählt Globalcube NICHT als direkte Kosten?
========================================================
Da Globalcube DB3 HÖHER ist, hat es WENIGER direkte Kosten.
→ Welche Konten zählt DRIVE als direkte Kosten, die Globalcube NICHT zählt?
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

print("=" * 120)
print("ANALYSE: Was zählt Globalcube NICHT als direkte Kosten?")
print("=" * 120)

jahr = 2025
datum_von = "2024-09-01"
datum_bis = "2025-09-01"

firma_filter_kosten = ''
guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"

globalcube_db3 = 2801501.76
drive_db3 = 2701120.19
diff_db3 = 100381.57  # Globalcube hat MEHR DB3 = WENIGER direkte Kosten

print(f"\nZeitraum: {datum_von} - {datum_bis}")
print(f"Globalcube DB3: {globalcube_db3:,.2f} € (HÖHER)")
print(f"DRIVE DB3: {drive_db3:,.2f} €")
print(f"Differenz: +{diff_db3:,.2f} €")
print(f"→ Globalcube hat {diff_db3:,.2f} € WENIGER direkte Kosten als DRIVE")
print(f"→ Globalcube zählt bestimmte Konten NICHT als direkte Kosten")
print(f"\n{'='*120}")

with db_session() as conn:
    cursor = conn.cursor()
    
    # Aktuelle direkte Kosten (DRIVE)
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
    direkte_drive = float((cursor.fetchone() or [0])[0] or 0)
    
    # Globalcube direkte Kosten (berechnet)
    # DB2 berechnen
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND ((nominal_account_number BETWEEN 800000 AND 889999)
               OR (nominal_account_number BETWEEN 893200 AND 893299))
          {guv_filter}
    """), (datum_von, datum_bis))
    umsatz = float((cursor.fetchone() or [0])[0] or 0)
    
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          {guv_filter}
    """), (datum_von, datum_bis))
    einsatz = float((cursor.fetchone() or [0])[0] or 0)
    
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR (nominal_account_number BETWEEN 455000 AND 456999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            OR (nominal_account_number BETWEEN 487000 AND 487099
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            OR nominal_account_number BETWEEN 491000 AND 497899
          )
          {firma_filter_kosten}
          {guv_filter}
    """), (datum_von, datum_bis))
    variable = float((cursor.fetchone() or [0])[0] or 0)
    
    db1 = umsatz - einsatz
    db2 = db1 - variable
    direkte_globalcube = db2 - globalcube_db3
    
    print(f"\nDirekte Kosten:")
    print(f"  DRIVE: {direkte_drive:,.2f} €")
    print(f"  Globalcube (berechnet): {direkte_globalcube:,.2f} €")
    print(f"  Differenz: {direkte_drive - direkte_globalcube:,.2f} €")
    
    # Analysiere: Welche Kontenbereiche könnten in DRIVE, aber nicht in Globalcube sein?
    print(f"\n{'='*120}")
    print("ANALYSE: Kontenbereiche in DRIVE direkten Kosten:")
    print(f"{'='*120}")
    
    # Detailliert nach Kontenbereichen
    kontenbereiche = [
        ('4100x-4110x', 410000, 411099),
        ('4150x (ohne 4151xx)', 415000, 415099),
        ('4200x-4239x (ohne 424xx)', 420000, 423999),
        ('4250x-4299x', 425000, 429999),
        ('4300x-4320x', 430000, 432099),
        ('4330x-4354x (ohne 4355xx)', 433000, 435499),
        ('4356x-4379x (ohne 438xx)', 435600, 437999),
        ('4390x-4499x', 439000, 449999),
        ('4500x-4549x', 450000, 454999),
        ('4570x-4599x', 457000, 459999),
        ('4600x-4689x', 460000, 468999),
        ('4690x', 469000, 469999),
        ('4700x-4869x (ohne 4870x)', 470000, 486999),
        ('4871x-4889x', 487100, 488999),
        ('4890x', 489000, 489999),
    ]
    
    print(f"\n{'Kontenbereich':<40} {'Wert':>15} {'%':>8}")
    summe = 0
    for name, von, bis in kontenbereiche:
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
        
        wert = float((cursor.fetchone() or [0])[0] or 0)
        if wert != 0:
            prozent = (wert / direkte_drive) * 100 if direkte_drive > 0 else 0
            print(f"  {name:<40} {wert:>15,.2f} € {prozent:>7.2f}%")
            summe += wert
    
    print(f"  {'SUMME':<40} {summe:>15,.2f} €")
    
    # Prüfe, ob bestimmte Kontenbereiche möglicherweise in Globalcube NICHT als direkte Kosten gezählt werden
    print(f"\n{'='*120}")
    print("HYPOTHESE: Welche Kontenbereiche zählt Globalcube NICHT als direkte Kosten?")
    print(f"{'='*120}")
    print(f"   Differenz: {diff_db3:,.2f} €")
    print(f"   → Globalcube zählt {diff_db3:,.2f} € NICHT als direkte Kosten")
    print(f"   → Möglicherweise zählt Globalcube diese als Variable oder Indirekte Kosten")

print(f"\n{'='*120}")
