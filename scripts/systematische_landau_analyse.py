#!/usr/bin/env python3
"""
Systematische Landau BWA-Analyse
Vergleicht DRIVE vs. GlobalCube Position für Position

Erstellt: TAG 182
"""

import json
import os
import glob
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.db_connection import get_db
from datetime import datetime

# HAR-Datei finden
HAR_DIR = "/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/globalcube_analyse"
landau_har = None
if os.path.exists(HAR_DIR):
    landau_files = glob.glob(f"{HAR_DIR}/*landau*.har")
    if landau_files:
        landau_har = max(landau_files, key=os.path.getmtime)

print("=" * 80)
print("SYSTEMATISCHE LANDAU BWA-ANALYSE")
print("=" * 80)
print()

# SCHRITT 1: GlobalCube-Werte aus HAR extrahieren
print("SCHRITT 1: GlobalCube-Werte aus HAR extrahieren")
print("-" * 80)
if landau_har:
    print(f"✅ HAR-Datei gefunden: {landau_har}")
    # TODO: HAR-Datei analysieren und Werte extrahieren
    globalcube_werte = {
        'umsatz': None,
        'einsatz': None,
        'variable_kosten': None,
        'direkte_kosten': None,
        'indirekte_kosten': None,
        'betriebsergebnis': -82219.00,  # Aus vorheriger Analyse
        'neutrales_ergebnis': -127.00,  # Aus vorheriger Analyse
        'unternehmensergebnis': -82346.00  # Aus vorheriger Analyse
    }
    print("⚠️  HAR-Analyse muss noch implementiert werden")
    print("   Verwende bekannte Werte aus vorheriger Analyse")
else:
    print("❌ Keine Landau HAR-Datei gefunden")
    globalcube_werte = None

print()

# SCHRITT 2: DRIVE-Werte berechnen und Konten auflisten
print("SCHRITT 2: DRIVE-Werte berechnen und Konten auflisten")
print("-" * 80)

datum_von = "2025-09-01"
datum_bis = "2026-01-01"

conn = get_db()
cursor = conn.cursor()

# Landau Filter
firma = '1'
standort = '2'

# Umsatz
print("\n1. UMSATZ:")
cursor.execute("""
    SELECT 
        nominal_account_number,
        COUNT(*) as anzahl,
        SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as wert
    FROM loco_journal_accountings
    WHERE accounting_date >= %s AND accounting_date < %s
      AND nominal_account_number BETWEEN 800000 AND 899999
      AND NOT (nominal_account_number BETWEEN 893200 AND 893299)
      AND branch_number = 3
      AND subsidiary_to_company_ref = 1
      AND NOT (accounting_date >= '2025-12-01' AND accounting_date < '2026-01-01'
               AND nominal_account_number BETWEEN 890000 AND 899999)
    GROUP BY nominal_account_number
    ORDER BY nominal_account_number
""", (datum_von, datum_bis))
umsatz_konten = cursor.fetchall()
umsatz_summe = sum(row[2] for row in umsatz_konten)
print(f"   DRIVE: {umsatz_summe:,.2f} € ({len(umsatz_konten)} Konten)")

# Einsatz
print("\n2. EINSATZ:")
cursor.execute("""
    SELECT 
        nominal_account_number,
        COUNT(*) as anzahl,
        SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
    FROM loco_journal_accountings
    WHERE accounting_date >= %s AND accounting_date < %s
      AND nominal_account_number BETWEEN 700000 AND 799999
      AND branch_number = 3
      AND subsidiary_to_company_ref = 1
      AND NOT (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)
      AND NOT (accounting_date >= '2025-12-01' AND accounting_date < '2026-01-01'
               AND nominal_account_number BETWEEN 890000 AND 899999)
    GROUP BY nominal_account_number
    ORDER BY nominal_account_number
""", (datum_von, datum_bis))
einsatz_konten = cursor.fetchall()
einsatz_summe = sum(row[2] for row in einsatz_konten)
print(f"   DRIVE: {einsatz_summe:,.2f} € ({len(einsatz_konten)} Konten)")

# Variable Kosten
print("\n3. VARIABLE KOSTEN:")
cursor.execute("""
    SELECT 
        nominal_account_number,
        COUNT(*) as anzahl,
        SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
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
        OR nominal_account_number BETWEEN 891000 AND 891099
      )
      AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'
      AND subsidiary_to_company_ref = 1
      AND NOT (accounting_date >= '2025-12-01' AND accounting_date < '2026-01-01'
               AND nominal_account_number BETWEEN 890000 AND 899999)
    GROUP BY nominal_account_number
    ORDER BY nominal_account_number
""", (datum_von, datum_bis))
variable_konten = cursor.fetchall()
variable_summe = sum(row[2] for row in variable_konten)
print(f"   DRIVE: {variable_summe:,.2f} € ({len(variable_konten)} Konten)")

# Direkte Kosten
print("\n4. DIREKTE KOSTEN:")
cursor.execute("""
    SELECT 
        nominal_account_number,
        COUNT(*) as anzahl,
        SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
    FROM loco_journal_accountings
    WHERE accounting_date >= %s AND accounting_date < %s
      AND nominal_account_number BETWEEN 400000 AND 489999
      AND substr(CAST(nominal_account_number AS TEXT), 6, 1) BETWEEN '1' AND '7'
      AND NOT (
        nominal_account_number BETWEEN 415100 AND 415199
        OR nominal_account_number BETWEEN 424000 AND 424999
        OR nominal_account_number BETWEEN 435500 AND 435599
        OR nominal_account_number BETWEEN 438000 AND 438999
        OR nominal_account_number BETWEEN 455000 AND 456999
        OR nominal_account_number BETWEEN 487000 AND 487099
        OR (nominal_account_number BETWEEN 489000 AND 489999
            AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
        OR nominal_account_number BETWEEN 491000 AND 497999
      )
      AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'
      AND subsidiary_to_company_ref = 1
      AND NOT (accounting_date >= '2025-12-01' AND accounting_date < '2026-01-01'
               AND nominal_account_number BETWEEN 890000 AND 899999)
    GROUP BY nominal_account_number
    ORDER BY nominal_account_number
""", (datum_von, datum_bis))
direkte_konten = cursor.fetchall()
direkte_summe = sum(row[2] for row in direkte_konten)
print(f"   DRIVE: {direkte_summe:,.2f} € ({len(direkte_konten)} Konten)")

# Indirekte Kosten
print("\n5. INDIREKTE KOSTEN:")
cursor.execute("""
    SELECT 
        nominal_account_number,
        COUNT(*) as anzahl,
        SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
    FROM loco_journal_accountings
    WHERE accounting_date >= %s AND accounting_date < %s
      AND nominal_account_number BETWEEN 400000 AND 489999
      AND (
        substr(CAST(nominal_account_number AS TEXT), 6, 1) = '0'
        OR nominal_account_number = 410021
        OR nominal_account_number BETWEEN 411000 AND 411999
        OR (nominal_account_number BETWEEN 489000 AND 489999
            AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
      )
      AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'
      AND subsidiary_to_company_ref = 1
      AND NOT (accounting_date >= '2025-12-01' AND accounting_date < '2026-01-01'
               AND nominal_account_number BETWEEN 890000 AND 899999)
    GROUP BY nominal_account_number
    ORDER BY nominal_account_number
""", (datum_von, datum_bis))
indirekte_konten = cursor.fetchall()
indirekte_summe = sum(row[2] for row in indirekte_konten)
print(f"   DRIVE: {indirekte_summe:,.2f} € ({len(indirekte_konten)} Konten)")

# Neutrales Ergebnis
print("\n6. NEUTRALES ERGEBNIS:")
cursor.execute("""
    SELECT 
        nominal_account_number,
        COUNT(*) as anzahl,
        SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as wert
    FROM loco_journal_accountings
    WHERE accounting_date >= %s AND accounting_date < %s
      AND nominal_account_number BETWEEN 200000 AND 299999
      AND branch_number = 3
      AND subsidiary_to_company_ref = 1
      AND NOT (accounting_date >= '2025-12-01' AND accounting_date < '2026-01-01'
               AND nominal_account_number BETWEEN 890000 AND 899999)
    GROUP BY nominal_account_number
    ORDER BY nominal_account_number
""", (datum_von, datum_bis))
neutral_konten = cursor.fetchall()
neutral_summe = sum(row[2] for row in neutral_konten)
print(f"   DRIVE: {neutral_summe:,.2f} € ({len(neutral_konten)} Konten)")

conn.close()

# SCHRITT 3: Vergleich
print("\n" + "=" * 80)
print("SCHRITT 3: VERGLEICH DRIVE vs. GLOBALCUBE")
print("=" * 80)
print()

drive_werte = {
    'umsatz': float(umsatz_summe),
    'einsatz': float(einsatz_summe),
    'variable_kosten': float(variable_summe),
    'direkte_kosten': float(direkte_summe),
    'indirekte_kosten': float(indirekte_summe),
    'betriebsergebnis': float(umsatz_summe - einsatz_summe - variable_summe - direkte_summe - indirekte_summe),
    'neutrales_ergebnis': float(neutral_summe),
    'unternehmensergebnis': float((umsatz_summe - einsatz_summe - variable_summe - direkte_summe - indirekte_summe) + neutral_summe)
}

if globalcube_werte:
    print(f"{'Position':<25} {'DRIVE':>15} {'GlobalCube':>15} {'Differenz':>15}")
    print("-" * 70)
    for pos in ['umsatz', 'einsatz', 'variable_kosten', 'direkte_kosten', 'indirekte_kosten', 
                'betriebsergebnis', 'neutrales_ergebnis', 'unternehmensergebnis']:
        drive = drive_werte.get(pos, 0)
        gc = globalcube_werte.get(pos)
        if gc is not None:
            diff = drive - gc
            status = "✅" if abs(diff) < 1 else "❌"
            print(f"{status} {pos:<23} {drive:>15,.2f} {gc:>15,.2f} {diff:>15,.2f}")
        else:
            print(f"⚠️  {pos:<23} {drive:>15,.2f} {'N/A':>15} {'N/A':>15}")

# SCHRITT 4: Konten-Level-Analyse für Positionen mit Differenz
print("\n" + "=" * 80)
print("SCHRITT 4: KONTEN-LEVEL-ANALYSE")
print("=" * 80)
print()

if globalcube_werte:
    for pos_name, pos_key in [('Betriebsergebnis', 'betriebsergebnis'), 
                              ('Neutrales Ergebnis', 'neutrales_ergebnis')]:
        drive = drive_werte.get(pos_key, 0)
        gc = globalcube_werte.get(pos_key)
        if gc is not None and abs(drive - gc) > 1:
            print(f"\n{pos_name} - Differenz: {drive - gc:,.2f} €")
            print(f"  DRIVE: {drive:,.2f} €")
            print(f"  GlobalCube: {gc:,.2f} €")
            print(f"\n  → Konten-Level-Analyse erforderlich")
            print(f"  → Welche Konten fehlen in DRIVE?")
            print(f"  → Welche Konten sind in DRIVE, aber nicht in GlobalCube?")

print("\n" + "=" * 80)
print("NÄCHSTE SCHRITTE:")
print("=" * 80)
print("1. HAR-Datei vollständig analysieren - alle Konten aus GlobalCube extrahieren")
print("2. Konten-Level-Vergleich: DRIVE-Konten vs. GlobalCube-Konten")
print("3. Fehlende oder falsche Konten identifizieren")
print("4. Filter entsprechend korrigieren")
