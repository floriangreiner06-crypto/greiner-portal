#!/usr/bin/env python3
"""
Analyse: Vollständigkeit des Imports aus Locosoft
==================================================
Prüft:
1. Werden alle Buchungen aus Locosoft importiert?
2. Gibt es Filter beim Import, die Buchungen ausschließen?
3. Vergleich: Anzahl Buchungen in Locosoft vs. DRIVE Portal
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import db_session, locosoft_session, row_to_dict
from api.db_connection import convert_placeholders

print("=" * 120)
print("ANALYSE: Vollständigkeit des Imports aus Locosoft")
print("=" * 120)

jahr = 2025
datum_von = "2024-09-01"
datum_bis = "2025-09-01"

print(f"\nZeitraum: {datum_von} - {datum_bis}")
print(f"DB3-Differenz: -100.381,57 €")
print(f"→ Prüfe, ob alle Buchungen aus Locosoft importiert werden")
print(f"\n{'='*120}")

# 1. Anzahl Buchungen in Locosoft (QUELLE)
print(f"\n1. ANZAHL BUCHUNGEN IN LOCOSOFT (QUELLE):")
with locosoft_session() as conn_loco:
    cursor_loco = conn_loco.cursor()
    
    # Gesamt
    cursor_loco.execute("""
        SELECT COUNT(*) as anzahl
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
    """, (datum_von, datum_bis))
    row = cursor_loco.fetchone()
    anzahl_loco_gesamt = row[0] if row else 0
    
    # Mit GuV-Filter
    cursor_loco.execute("""
        SELECT COUNT(*) as anzahl
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
    """, (datum_von, datum_bis))
    row = cursor_loco.fetchone()
    anzahl_loco_ohne_guv = row[0] if row else 0
    
    # In direkten Kosten (40xxxx-48xxxx KST 1-7)
    cursor_loco.execute("""
        SELECT COUNT(*) as anzahl
        FROM journal_accountings
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
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
    """, (datum_von, datum_bis))
    row = cursor_loco.fetchone()
    anzahl_loco_direkte = row[0] if row else 0
    
    print(f"   Gesamt: {anzahl_loco_gesamt:,} Buchungen")
    print(f"   Ohne GuV-Filter: {anzahl_loco_ohne_guv:,} Buchungen")
    print(f"   GuV-Abschluss: {anzahl_loco_gesamt - anzahl_loco_ohne_guv:,} Buchungen")
    print(f"   In direkten Kosten: {anzahl_loco_direkte:,} Buchungen")

# 2. Anzahl Buchungen in DRIVE Portal (ZIEL)
print(f"\n2. ANZAHL BUCHUNGEN IN DRIVE PORTAL (ZIEL):")
with db_session() as conn_drive:
    cursor_drive = conn_drive.cursor()
    
    # Gesamt
    cursor_drive.execute("""
        SELECT COUNT(*) as anzahl
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
    """, (datum_von, datum_bis))
    row = cursor_drive.fetchone()
    anzahl_drive_gesamt = row[0] if row else 0
    
    # Mit GuV-Filter
    cursor_drive.execute("""
        SELECT COUNT(*) as anzahl
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
    """, (datum_von, datum_bis))
    row = cursor_drive.fetchone()
    anzahl_drive_ohne_guv = row[0] if row else 0
    
    # In direkten Kosten
    cursor_drive.execute("""
        SELECT COUNT(*) as anzahl
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
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
    """, (datum_von, datum_bis))
    row = cursor_drive.fetchone()
    anzahl_drive_direkte = row[0] if row else 0
    
    print(f"   Gesamt: {anzahl_drive_gesamt:,} Buchungen")
    print(f"   Ohne GuV-Filter: {anzahl_drive_ohne_guv:,} Buchungen")
    print(f"   GuV-Abschluss: {anzahl_drive_gesamt - anzahl_drive_ohne_guv:,} Buchungen")
    print(f"   In direkten Kosten: {anzahl_drive_direkte:,} Buchungen")

# 3. Vergleich
print(f"\n3. VERGLEICH:")
diff_gesamt = anzahl_drive_gesamt - anzahl_loco_gesamt
diff_ohne_guv = anzahl_drive_ohne_guv - anzahl_loco_ohne_guv
diff_direkte = anzahl_drive_direkte - anzahl_loco_direkte

print(f"   Gesamt: {diff_gesamt:+,} Buchungen ({diff_gesamt/anzahl_loco_gesamt*100:+.2f}%)")
print(f"   Ohne GuV: {diff_ohne_guv:+,} Buchungen ({diff_ohne_guv/anzahl_loco_ohne_guv*100:+.2f}%)")
print(f"   Direkte Kosten: {diff_direkte:+,} Buchungen ({diff_direkte/anzahl_loco_direkte*100:+.2f}%)")

if diff_gesamt != 0 or diff_ohne_guv != 0 or diff_direkte != 0:
    print(f"\n   ⚠️  WARNUNG: Unterschiedliche Anzahl Buchungen!")
    print(f"   → Möglicherweise fehlen Buchungen im Import")
else:
    print(f"\n   ✅ Anzahl Buchungen stimmt überein")

# 4. Prüfe Werte (direkte Kosten)
print(f"\n4. WERTE-VERGLEICH (DIREKTE KOSTEN):")
with locosoft_session() as conn_loco:
    cursor_loco = conn_loco.cursor()
    cursor_loco.execute("""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM journal_accountings
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
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
    """, (datum_von, datum_bis))
    row = cursor_loco.fetchone()
    wert_loco = float(row[0] if row and row[0] is not None else 0)

with db_session() as conn_drive:
    cursor_drive = conn_drive.cursor()
    cursor_drive.execute("""
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
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
    """, (datum_von, datum_bis))
    row = cursor_drive.fetchone()
    wert_drive = float(row[0] if row and row[0] is not None else 0)

diff_wert = wert_drive - wert_loco
print(f"   Locosoft (QUELLE): {wert_loco:>15,.2f} €")
print(f"   DRIVE Portal (ZIEL): {wert_drive:>15,.2f} €")
print(f"   Differenz: {diff_wert:>15,.2f} € ({diff_wert/wert_loco*100:+.2f}%)")

if abs(diff_wert) > 0.01:
    print(f"\n   ⚠️  WARNUNG: Unterschiedliche Werte!")
    print(f"   → Möglicherweise fehlen Buchungen oder es gibt Rundungsdifferenzen")
else:
    print(f"\n   ✅ Werte stimmen überein")

# 5. Zusammenfassung
print(f"\n{'='*120}")
print("ZUSAMMENFASSUNG:")
print(f"{'='*120}")
print(f"   ⚠️  WICHTIG: Globalcube ist ein Reporting-System!")
print(f"   → Globalcube bezieht seine Daten aus Locosoft (oder einer anderen Quelle)")
print(f"   → Wenn es Abweichungen gibt, könnte Globalcube:")
print(f"      1. Andere Filter verwenden")
print(f"      2. Andere Zeitpunkte verwenden (Buchungsdatum vs. Wertstellungsdatum)")
print(f"      3. Manuelle Anpassungen haben")
print(f"      4. Oder: Wir haben nicht alle Buchungen aus Locosoft")

print(f"\n{'='*120}")
