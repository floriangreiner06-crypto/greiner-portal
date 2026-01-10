#!/usr/bin/env python3
"""
Detaillierte Analyse: Direkte Kosten - Kontenbereiche
======================================================
Identifiziert welche Kontenbereiche in direkten Kosten enthalten sind
und vergleicht mit Globalcube.
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

print("=" * 120)
print("DETAILLIERTE ANALYSE: Direkte Kosten - Kontenbereiche")
print("=" * 120)

jahr = 2025
datum_von = "2024-09-01"  # WJ-Start
datum_bis = "2025-09-01"  # Bis Ende August

firma_filter_kosten = ''
guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"

# Globalcube DB3: 2.801.501,76 €
# DRIVE DB3: 2.701.120,19 €
# Differenz: -100.381,57 €

globalcube_db3 = 2801501.76
drive_db3_erwartet = 2701120.19
diff_db3 = -100381.57

print(f"\nZeitraum: {datum_von} - {datum_bis}")
print(f"Globalcube DB3: {globalcube_db3:,.2f} €")
print(f"DRIVE DB3 (erwartet): {drive_db3_erwartet:,.2f} €")
print(f"Differenz DB3: {diff_db3:,.2f} € ({diff_db3/globalcube_db3*100:+.2f}%)")
print(f"\n{'='*120}")

with db_session() as conn:
    cursor = conn.cursor()
    
    # 1. Gesamt direkte Kosten (aktuelle Logik)
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
    direkte_gesamt = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    print(f"\n1. GESAMT DIREKTE KOSTEN (aktuelle Logik):")
    print(f"   {direkte_gesamt:>15,.2f} €")
    
    # 2. Direkte Kosten nach Kontenbereichen (Hauptgruppen)
    print(f"\n2. DIREKTE KOSTEN NACH KONTENBEREICHEN:")
    print(f"   {'Kontenbereich':<40} {'Wert':>15} {'%':>8} {'KST':>10}")
    
    kontenbereiche = [
        # Personalkosten
        ('4100x-4110x (Lohn/Gehalt)', '410000', '411099', '1-7'),
        ('4150x (ohne 4151xx)', '415000', '415099', '1-7'),
        ('4300x-4320x (Lohn/Gehalt)', '430000', '432099', '1-7'),
        ('4360x (Lohn/Gehalt)', '436000', '436099', '1-7'),
        
        # Gemeinkosten
        ('4690x (Sonstige Kosten)', '469000', '469099', '1-7'),
        ('4890x (Sonstige Kosten)', '489000', '489099', '1-7'),
        
        # Weitere Bereiche
        ('4200x-4299x (ohne 424xx)', '420000', '423999', '1-7'),
        ('4200x-4299x (ohne 424xx)', '425000', '429999', '1-7'),
        ('4400x-4499x (ohne 4355xx, 438xx)', '440000', '435499', '1-7'),
        ('4400x-4499x (ohne 4355xx, 438xx)', '435600', '437999', '1-7'),
        ('4400x-4499x (ohne 4355xx, 438xx)', '439000', '449999', '1-7'),
        ('4500x-4549x', '450000', '454999', '1-7'),
        ('4570x-4599x', '457000', '459999', '1-7'),
        ('4600x-4689x', '460000', '468999', '1-7'),
        ('4700x-4869x (ohne 4870x)', '470000', '486999', '1-7'),
        ('4700x-4869x (ohne 4870x)', '487100', '488999', '1-7'),
        ('4900x (ohne 491xx-497xx)', '490000', '490999', '1-7'),
        ('4980x-4989x (ohne 498xx)', '498000', '497999', '1-7'),  # Sollte eigentlich leer sein
    ]
    
    summe_bereiche = 0
    for name, von_konto, bis_konto, kst in kontenbereiche:
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
        """), (datum_von, datum_bis, von_konto, bis_konto))
        
        wert = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        if wert != 0:
            prozent = (wert / direkte_gesamt) * 100 if direkte_gesamt > 0 else 0
            print(f"   {name:<40} {wert:>15,.2f} € {prozent:>7.2f}% {kst:>10}")
            summe_bereiche += wert
    
    print(f"   {'SUMME BEREICHE':<40} {summe_bereiche:>15,.2f} €")
    print(f"   {'DIFFERENZ':<40} {direkte_gesamt - summe_bereiche:>15,.2f} €")
    
    # 3. Prüfe ausgeschlossene Bereiche (sollten NICHT in direkten Kosten sein)
    print(f"\n3. AUSGESCHLOSSENE BEREICHE (sollten NICHT in direkten Kosten sein):")
    print(f"   {'Kontenbereich':<40} {'Wert':>15} {'Zuordnung':>20}")
    
    ausgeschlossene = [
        ('4151xx (Variable)', '415100', '415199', 'Variable'),
        ('424xx (Indirekte)', '424000', '424999', 'Indirekte'),
        ('4355xx (Variable)', '435500', '435599', 'Variable'),
        ('438xx (Indirekte)', '438000', '438999', 'Indirekte'),
        ('455xx-456xx KST 1-7 (Variable)', '455000', '456999', 'Variable'),
        ('4870x KST 1-7 (Variable)', '487000', '487099', 'Variable'),
        ('491xx-497xx (Variable)', '491000', '497999', 'Variable'),
    ]
    
    for name, von_konto, bis_konto, zuordnung in ausgeschlossene:
        cursor.execute(convert_placeholders(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN %s AND %s
              {firma_filter_kosten}
              {guv_filter}
        """), (datum_von, datum_bis, von_konto, bis_konto))
        
        wert = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        if wert != 0:
            print(f"   {name:<40} {wert:>15,.2f} € {zuordnung:>20}")
    
    # 4. Prüfe mögliche Fehlzuordnungen
    print(f"\n4. MÖGLICHE FEHLZUORDNUNGEN:")
    print(f"   Prüfe Konten, die möglicherweise fehlen oder falsch zugeordnet sind...")
    
    # Prüfe 498xx (sollte in indirekten Kosten sein, nicht in direkten)
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
        print(f"      → Sollte in indirekten Kosten sein (498xx gehört zu indirekten Kosten)!")
    
    # Prüfe 424xx/438xx mit KST 4 oder 5 (sollten in direkten Kosten sein?)
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
    
    if wert_424438_kst45 != 0:
        print(f"   ⚠️  424xx/438xx mit KST 4/5: {wert_424438_kst45:,.2f} €")
        print(f"      → Aktuell in indirekten Kosten (nur KST 1-3,6-7), aber KST 4/5 fehlt!")
    
    # 5. Vergleich: Was würde passieren, wenn wir 424xx/438xx KST 4/5 zu direkten Kosten hinzufügen?
    print(f"\n5. SIMULATION: Was wenn 424xx/438xx KST 4/5 zu direkten Kosten gehören?")
    direkte_mit_424438_kst45 = direkte_gesamt + wert_424438_kst45
    print(f"   Aktuelle direkte Kosten: {direkte_gesamt:,.2f} €")
    print(f"   + 424xx/438xx KST 4/5:   {wert_424438_kst45:,.2f} €")
    print(f"   = Neue direkte Kosten:   {direkte_mit_424438_kst45:,.2f} €")
    print(f"   → DB3 würde um {wert_424438_kst45:,.2f} € sinken")
    
    # 6. Prüfe alle Konten mit KST 1-7, die NICHT in direkten Kosten sind
    print(f"\n6. ALLE KONTEN 40xxxx-48xxxx MIT KST 1-7 (Gesamt):")
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          {firma_filter_kosten}
          {guv_filter}
    """), (datum_von, datum_bis))
    alle_kst17 = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    print(f"   Gesamt KST 1-7: {alle_kst17:,.2f} €")
    print(f"   Davon in direkten Kosten: {direkte_gesamt:,.2f} €")
    print(f"   Differenz (ausgeschlossen): {alle_kst17 - direkte_gesamt:,.2f} €")
    
    # 7. Zusammenfassung
    print(f"\n{'='*120}")
    print("ZUSAMMENFASSUNG:")
    print(f"{'='*120}")
    print(f"   Aktuelle direkte Kosten: {direkte_gesamt:,.2f} €")
    print(f"   Globalcube DB3-Differenz: {diff_db3:,.2f} €")
    print(f"   → Wenn direkte Kosten um {abs(diff_db3):,.2f} € höher wären, würde DB3-Differenz verschwinden")
    print(f"\n   Mögliche Ursachen:")
    print(f"   1. 424xx/438xx KST 4/5 fehlen in direkten Kosten? ({wert_424438_kst45:,.2f} €)")
    print(f"   2. Andere Kontenbereiche fehlen?")
    print(f"   3. Falsche Filter-Logik?")

print(f"\n{'='*120}")
