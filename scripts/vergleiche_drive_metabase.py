#!/usr/bin/env python3
"""
Vergleicht Werte zwischen DRIVE und Metabase (fact_bwa)
"""

import psycopg2
from datetime import date

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='drive_portal',
    user='drive_user',
    password='DrivePortal2024'
)
cursor = conn.cursor()

heute = date.today()
monat = heute.month
jahr = heute.year
datum_von = f"{jahr}-{monat:02d}-01"
datum_bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"

print("="*80)
print("VERGLEICH: DRIVE vs. Metabase (nach Korrektur)")
print("="*80)
print(f"\nZeitraum: {datum_von} bis {datum_bis}\n")

# TEK Gesamt - Vergleich
print("TEK Gesamt - Monat kumuliert:")
print("-" * 80)
print(f"{'Bereich':<20} {'DRIVE (€)':>15} {'Metabase (€)':>15} {'Differenz (€)':>15} {'Status':>10}")
print("-" * 80)

# Neuwagen
cursor.execute("""
    SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0)
    FROM loco_journal_accountings
    WHERE accounting_date >= %s AND accounting_date < %s
      AND nominal_account_number BETWEEN 810000 AND 819999
      AND NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')
""", (datum_von, datum_bis))
result = cursor.fetchone()
drive_nw = float(result[0]) if result and len(result) > 0 and result[0] is not None else 0.0

cursor.execute("""
    SELECT COALESCE(SUM(-betrag), 0)
    FROM fact_bwa
    WHERE zeit_id >= %s AND zeit_id < %s
      AND konto_id BETWEEN 810000 AND 819999
      AND debit_or_credit = 'H'
""", (datum_von, datum_bis))
result = cursor.fetchone()
metabase_nw = float(result[0]) if result and len(result) > 0 and result[0] is not None else 0.0
diff_nw = abs(drive_nw - metabase_nw)
status_nw = "✅ OK" if diff_nw < 0.01 else "❌ FEHLER"
print(f"{'Neuwagen':<20} {drive_nw:>15,.2f} {metabase_nw:>15,.2f} {diff_nw:>15,.2f} {status_nw:>10}")

# Gebrauchtwagen
cursor.execute("""
    SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0)
    FROM loco_journal_accountings
    WHERE accounting_date >= %s AND accounting_date < %s
      AND nominal_account_number BETWEEN 820000 AND 829999
      AND NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')
""", (datum_von, datum_bis))
result = cursor.fetchone()
drive_gw = float(result[0]) if result and result[0] else 0.0

cursor.execute("""
    SELECT SUM(-betrag)
    FROM fact_bwa
    WHERE zeit_id >= %s AND zeit_id < %s
      AND konto_id BETWEEN 820000 AND 829999
      AND debit_or_credit = 'H'
""", (datum_von, datum_bis))
result = cursor.fetchone()
metabase_gw = float(result[0]) if result and result[0] else 0.0
diff_gw = abs(drive_gw - metabase_gw)
status_gw = "✅ OK" if diff_gw < 0.01 else "❌ FEHLER"
print(f"{'Gebrauchtwagen':<20} {drive_gw:>15,.2f} {metabase_gw:>15,.2f} {diff_gw:>15,.2f} {status_gw:>10}")

# Teile
cursor.execute("""
    SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0)
    FROM loco_journal_accountings
    WHERE accounting_date >= %s AND accounting_date < %s
      AND nominal_account_number BETWEEN 830000 AND 839999
      AND NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')
""", (datum_von, datum_bis))
result = cursor.fetchone()
drive_teile = float(result[0]) if result and result[0] else 0.0

cursor.execute("""
    SELECT SUM(-betrag)
    FROM fact_bwa
    WHERE zeit_id >= %s AND zeit_id < %s
      AND konto_id BETWEEN 830000 AND 839999
      AND debit_or_credit = 'H'
""", (datum_von, datum_bis))
result = cursor.fetchone()
metabase_teile = float(result[0]) if result and result[0] else 0.0
diff_teile = abs(drive_teile - metabase_teile)
status_teile = "✅ OK" if diff_teile < 0.01 else "❌ FEHLER"
print(f"{'Teile':<20} {drive_teile:>15,.2f} {metabase_teile:>15,.2f} {diff_teile:>15,.2f} {status_teile:>10}")

# Werkstatt
cursor.execute("""
    SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0)
    FROM loco_journal_accountings
    WHERE accounting_date >= %s AND accounting_date < %s
      AND nominal_account_number BETWEEN 840000 AND 849999
      AND NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')
""", (datum_von, datum_bis))
result = cursor.fetchone()
drive_werkstatt = float(result[0]) if result and result[0] else 0.0

cursor.execute("""
    SELECT SUM(-betrag)
    FROM fact_bwa
    WHERE zeit_id >= %s AND zeit_id < %s
      AND konto_id BETWEEN 840000 AND 849999
      AND debit_or_credit = 'H'
""", (datum_von, datum_bis))
result = cursor.fetchone()
metabase_werkstatt = float(result[0]) if result and result[0] else 0.0
diff_werkstatt = abs(drive_werkstatt - metabase_werkstatt)
status_werkstatt = "✅ OK" if diff_werkstatt < 0.01 else "❌ FEHLER"
print(f"{'Werkstatt':<20} {drive_werkstatt:>15,.2f} {metabase_werkstatt:>15,.2f} {diff_werkstatt:>15,.2f} {status_werkstatt:>10}")

# Sonstige
cursor.execute("""
    SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0)
    FROM loco_journal_accountings
    WHERE accounting_date >= %s AND accounting_date < %s
      AND nominal_account_number BETWEEN 860000 AND 869999
      AND NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')
""", (datum_von, datum_bis))
result = cursor.fetchone()
drive_sonst = float(result[0]) if result and result[0] else 0.0

cursor.execute("""
    SELECT SUM(-betrag)
    FROM fact_bwa
    WHERE zeit_id >= %s AND zeit_id < %s
      AND konto_id BETWEEN 860000 AND 869999
      AND debit_or_credit = 'H'
""", (datum_von, datum_bis))
result = cursor.fetchone()
metabase_sonst = float(result[0]) if result and result[0] else 0.0
diff_sonst = abs(drive_sonst - metabase_sonst)
status_sonst = "✅ OK" if diff_sonst < 0.01 else "❌ FEHLER"
print(f"{'Sonstige':<20} {drive_sonst:>15,.2f} {metabase_sonst:>15,.2f} {diff_sonst:>15,.2f} {status_sonst:>10}")

# Gesamt
drive_gesamt = drive_nw + drive_gw + drive_teile + drive_werkstatt + drive_sonst
metabase_gesamt = metabase_nw + metabase_gw + metabase_teile + metabase_werkstatt + metabase_sonst
diff_gesamt = abs(drive_gesamt - metabase_gesamt)
status_gesamt = "✅ OK" if diff_gesamt < 0.01 else "❌ FEHLER"

print("-" * 80)
print(f"{'GESAMT':<20} {drive_gesamt:>15,.2f} {metabase_gesamt:>15,.2f} {diff_gesamt:>15,.2f} {status_gesamt:>10}")

cursor.close()
conn.close()

print("\n" + "="*80)
print("✅ Vergleich abgeschlossen!")
print("="*80)
