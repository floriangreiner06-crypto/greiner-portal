#!/usr/bin/env python3
"""
Analyse: Globalcube Filter-Varianten
=====================================
Testet verschiedene Filter-Kombinationen für direkte Kosten,
um die Globalcube-Logik zu identifizieren.
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

print("=" * 120)
print("ANALYSE: Globalcube Filter-Varianten für direkte Kosten")
print("=" * 120)

jahr = 2025
datum_von = "2024-09-01"
datum_bis = "2025-09-01"

firma_filter_kosten = ''
guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"

# Globalcube DB3: 2.801.501,76 €
# DRIVE DB3: 2.701.120,19 €
# Differenz: -100.381,57 €
# → DRIVE hat 100.381,57 € WENIGER direkte Kosten

globalcube_db3 = 2801501.76
drive_db3 = 2701120.19
diff_db3 = -100381.57

# Berechne DB2 (ist gleich in beiden Systemen)
# DB3 = DB2 - direkte Kosten
# → direkte_kosten = DB2 - DB3
# → Globalcube direkte Kosten = DB2 - 2.801.501,76
# → DRIVE direkte Kosten = DB2 - 2.701.120,19
# → Differenz direkte Kosten = (DB2 - 2.801.501,76) - (DB2 - 2.701.120,19) = -100.381,57

print(f"\nZeitraum: {datum_von} - {datum_bis}")
print(f"Globalcube DB3: {globalcube_db3:,.2f} €")
print(f"DRIVE DB3: {drive_db3:,.2f} €")
print(f"Differenz DB3: {diff_db3:,.2f} €")
print(f"→ Globalcube hat {abs(diff_db3):,.2f} € MEHR direkte Kosten als DRIVE")
print(f"\n{'='*120}")

with db_session() as conn:
    cursor = conn.cursor()
    
    # Berechne DB2 (für Vergleich)
    # Umsatz
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
    
    # Einsatz
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
    
    # Variable Kosten
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
    
    print(f"\nBasis-Werte:")
    print(f"  Umsatz: {umsatz:>15,.2f} €")
    print(f"  Einsatz: {einsatz:>15,.2f} €")
    print(f"  DB1: {db1:>15,.2f} €")
    print(f"  Variable Kosten: {variable:>15,.2f} €")
    print(f"  DB2: {db2:>15,.2f} €")
    
    # Berechne direkte Kosten aus DB3
    direkte_drive = db2 - drive_db3
    direkte_globalcube = db2 - globalcube_db3
    
    print(f"\nDirekte Kosten (berechnet aus DB3):")
    print(f"  DRIVE: {direkte_drive:>15,.2f} €")
    print(f"  Globalcube: {direkte_globalcube:>15,.2f} €")
    print(f"  Differenz: {direkte_globalcube - direkte_drive:>15,.2f} €")
    
    # Teste verschiedene Filter-Varianten
    print(f"\n{'='*120}")
    print("TESTE FILTER-VARIANTEN:")
    print(f"{'='*120}")
    
    varianten = [
        {
            'name': 'Aktuell (DRIVE)',
            'kst_filter': "IN ('1','2','3','4','5','6','7')",
            'exclude': [
                (415100, 415199),  # Variable
                (424000, 424999),  # Indirekte
                (435500, 435599),  # Variable
                (438000, 438999),  # Indirekte
                (455000, 456999),  # Variable
                (487000, 487099),  # Variable
                (491000, 497999),  # Variable
            ]
        },
        {
            'name': 'Ohne 424xx/438xx Ausschluss',
            'kst_filter': "IN ('1','2','3','4','5','6','7')",
            'exclude': [
                (415100, 415199),  # Variable
                (435500, 435599),  # Variable
                (455000, 456999),  # Variable
                (487000, 487099),  # Variable
                (491000, 497999),  # Variable
            ]
        },
        {
            'name': 'Nur KST 1-3,6-7 (ohne 4,5)',
            'kst_filter': "IN ('1','2','3','6','7')",
            'exclude': [
                (415100, 415199),
                (424000, 424999),
                (435500, 435599),
                (438000, 438999),
                (455000, 456999),
                (487000, 487099),
                (491000, 497999),
            ]
        },
        {
            'name': 'Alle KST 1-7 (keine Ausschlüsse)',
            'kst_filter': "IN ('1','2','3','4','5','6','7')",
            'exclude': []
        },
    ]
    
    for variant in varianten:
        exclude_conditions = []
        for von, bis in variant['exclude']:
            exclude_conditions.append(f"nominal_account_number BETWEEN {von} AND {bis}")
        
        exclude_sql = ""
        if exclude_conditions:
            exclude_sql = "AND NOT (" + " OR ".join(exclude_conditions) + ")"
        
        cursor.execute(convert_placeholders(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 400000 AND 489999
              AND substr(CAST(nominal_account_number AS TEXT), 5, 1) {variant['kst_filter']}
              {exclude_sql}
              {firma_filter_kosten}
              {guv_filter}
        """), (datum_von, datum_bis))
        
        wert = float((cursor.fetchone() or [0])[0] or 0)
        db3_test = db2 - wert
        diff = abs(db3_test - globalcube_db3)
        
        status = "✅" if diff < 1.0 else "❌"
        print(f"{status} {variant['name']:<40} Direkte: {wert:>15,.2f} €, DB3: {db3_test:>15,.2f} €, Diff: {diff:>10,.2f} €")
    
    # Teste spezielle Kontenbereiche
    print(f"\n{'='*120}")
    print("TESTE SPEZIELLE KONTENBEREICHE:")
    print(f"{'='*120}")
    
    # Prüfe 424xx/438xx mit KST 4/5
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
    wert_424438_kst45 = float((cursor.fetchone() or [0])[0] or 0)
    
    if wert_424438_kst45 > 0:
        print(f"  424xx/438xx KST 4/5: {wert_424438_kst45:,.2f} €")
        print(f"  → Wenn zu direkten Kosten: {direkte_drive + wert_424438_kst45:,.2f} €")
        print(f"  → DB3 würde: {db2 - (direkte_drive + wert_424438_kst45):,.2f} €")
        print(f"  → Diff zu Globalcube: {abs((db2 - (direkte_drive + wert_424438_kst45)) - globalcube_db3):,.2f} €")
    
    # Zusammenfassung
    print(f"\n{'='*120}")
    print("ZUSAMMENFASSUNG:")
    print(f"{'='*120}")
    print(f"   Globalcube DB3: {globalcube_db3:,.2f} €")
    print(f"   DRIVE DB3: {drive_db3:,.2f} €")
    print(f"   Differenz: {diff_db3:,.2f} €")
    print(f"\n   → Globalcube hat {abs(diff_db3):,.2f} € MEHR direkte Kosten")
    print(f"   → Möglicherweise zählt Globalcube bestimmte Konten als direkte Kosten,")
    print(f"     die in DRIVE als Variable oder Indirekte Kosten gezählt werden")

print(f"\n{'='*120}")
