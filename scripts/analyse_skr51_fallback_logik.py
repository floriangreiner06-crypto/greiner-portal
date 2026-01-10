#!/usr/bin/env python3
"""
Umfassende Analyse: skr51_cost_center Fallback-Logik
====================================================
Analysiert:
1. Warum sind alle direkten Kosten skr51_cost_center = 0?
2. Wie filtert Globalcube bei skr51_cost_center = 0? (Fallback-Logik)
3. 411xxx Kontenbereich detailliert (100k€ Differenz-Kandidat)
4. Monat-für-Monat-Vergleich (wann entsteht die Differenz?)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db_connection import get_db, convert_placeholders
from datetime import datetime, timedelta
import calendar

def row_to_dict(row):
    """Konvertiert eine Datenbank-Zeile in ein Dictionary"""
    if row is None:
        return {}
    if hasattr(row, '_asdict'):
        return row._asdict()
    if isinstance(row, dict):
        return row
    # HybridRow: Unterstützt sowohl Index- als auch Spaltennamen-Zugriff
    try:
        if hasattr(row, 'keys'):
            return {key: row[key] for key in row.keys()}
    except:
        pass
    return dict(row) if hasattr(row, '__iter__') else {}

def analysiere_skr51_verteilung(conn, datum_von: str, datum_bis: str):
    """Analysiert die Verteilung von skr51_cost_center in direkten Kosten"""
    
    cursor = conn.cursor()
    
    print("=" * 100)
    print("ANALYSE 1: skr51_cost_center Verteilung in direkten Kosten")
    print("=" * 100)
    print(f"Zeitraum: {datum_von} bis {datum_bis}")
    print()
    
    # 1. Gesamt-Verteilung skr51_cost_center
    print("1. GESAMT-VERTEILUNG skr51_cost_center (alle direkten Kosten):")
    cursor.execute(convert_placeholders("""
        SELECT 
            COALESCE(skr51_cost_center, -1) as skr51_cc,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as summe
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
        GROUP BY skr51_cc
        ORDER BY skr51_cc
    """), (datum_von, datum_bis))
    
    rows = cursor.fetchall()
    total_anzahl = 0
    total_summe = 0
    print(f"   {'skr51_cc':<12} {'Anzahl':>12} {'Summe (€)':>20} {'%':>8}")
    print(f"   {'-'*12} {'-'*12} {'-'*20} {'-'*8}")
    for row in rows:
        d = row_to_dict(row)
        skr51_cc = d.get('skr51_cc', -1)
        anzahl = int(d.get('anzahl', 0))
        summe = float(d.get('summe', 0))
        total_anzahl += anzahl
        total_summe += summe
        prozent = (summe / total_summe * 100) if total_summe > 0 else 0
        print(f"   {skr51_cc:<12} {anzahl:>12,} {summe:>20,.2f} {prozent:>7.2f}%")
    
    print(f"   {'-'*12} {'-'*12} {'-'*20} {'-'*8}")
    print(f"   {'GESAMT':<12} {total_anzahl:>12,} {total_summe:>20,.2f} 100.00%")
    print()
    
    # 2. Konten mit skr51_cost_center = 0 (Problem-Konten)
    print("2. KONTEN mit skr51_cost_center = 0 (Problem-Konten für Globalcube):")
    cursor.execute(convert_placeholders("""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 1, 3) || 'xxx' as konten_3stellig,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as summe
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          AND (skr51_cost_center = 0 OR skr51_cost_center IS NULL)
          AND NOT (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 455000 AND 456999
            OR nominal_account_number BETWEEN 487000 AND 487099
            OR nominal_account_number BETWEEN 491000 AND 497999
          )
        GROUP BY konten_3stellig
        ORDER BY summe DESC
        LIMIT 20
    """), (datum_von, datum_bis))
    
    rows = cursor.fetchall()
    problem_summe = 0
    print(f"   {'Konten (3stellig)':<20} {'Anzahl':>12} {'Summe (€)':>20}")
    print(f"   {'-'*20} {'-'*12} {'-'*20}")
    for row in rows:
        d = row_to_dict(row)
        konten = d.get('konten_3stellig', '')
        anzahl = int(d.get('anzahl', 0))
        summe = float(d.get('summe', 0))
        problem_summe += summe
        print(f"   {konten:<20} {anzahl:>12,} {summe:>20,.2f}")
    print(f"   {'-'*20} {'-'*12} {'-'*20}")
    print(f"   {'GESAMT (skr51_cc=0)':<20} {'':>12} {problem_summe:>20,.2f}")
    print()
    
    return {
        'total_anzahl': total_anzahl,
        'total_summe': total_summe,
        'problem_summe': problem_summe
    }

def analysiere_411xxx_detailed(conn, datum_von: str, datum_bis: str):
    """Detaillierte Analyse des 411xxx Kontenbereichs (100k€ Differenz-Kandidat)"""
    
    cursor = conn.cursor()
    
    print("=" * 100)
    print("ANALYSE 2: 411xxx Kontenbereich detailliert (100k€ Differenz-Kandidat)")
    print("=" * 100)
    print()
    
    # 1. 411xxx Gesamt
    print("1. 411xxx GESAMT (alle KST):")
    cursor.execute(convert_placeholders("""
        SELECT 
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as summe
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 411000 AND 411999
    """), (datum_von, datum_bis))
    
    row = cursor.fetchone()
    d = row_to_dict(row)
    gesamt_411 = float(d.get('summe', 0))
    print(f"   Gesamt 411xxx: {gesamt_411:>20,.2f} €")
    print()
    
    # 2. 411xxx nach KST (5. Stelle)
    print("2. 411xxx nach KST (5. Stelle):")
    cursor.execute(convert_placeholders("""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 5, 1) as kst_stelle,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as summe
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 411000 AND 411999
        GROUP BY kst_stelle
        ORDER BY kst_stelle
    """), (datum_von, datum_bis))
    
    rows = cursor.fetchall()
    print(f"   {'KST':<6} {'Anzahl':>12} {'Summe (€)':>20} {'% von Gesamt':>15}")
    print(f"   {'-'*6} {'-'*12} {'-'*20} {'-'*15}")
    for row in rows:
        d = row_to_dict(row)
        kst = d.get('kst_stelle', '')
        anzahl = int(d.get('anzahl', 0))
        summe = float(d.get('summe', 0))
        prozent = (summe / gesamt_411 * 100) if gesamt_411 > 0 else 0
        print(f"   {kst:<6} {anzahl:>12,} {summe:>20,.2f} {prozent:>14.2f}%")
    print()
    
    # 3. 411xxx nach skr51_cost_center
    print("3. 411xxx nach skr51_cost_center:")
    cursor.execute(convert_placeholders("""
        SELECT 
            COALESCE(skr51_cost_center, -1) as skr51_cc,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as summe
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 411000 AND 411999
        GROUP BY skr51_cc
        ORDER BY skr51_cc
    """), (datum_von, datum_bis))
    
    rows = cursor.fetchall()
    print(f"   {'skr51_cc':<12} {'Anzahl':>12} {'Summe (€)':>20} {'% von Gesamt':>15}")
    print(f"   {'-'*12} {'-'*12} {'-'*20} {'-'*15}")
    for row in rows:
        d = row_to_dict(row)
        skr51_cc = d.get('skr51_cc', -1)
        anzahl = int(d.get('anzahl', 0))
        summe = float(d.get('summe', 0))
        prozent = (summe / gesamt_411 * 100) if gesamt_411 > 0 else 0
        print(f"   {skr51_cc:<12} {anzahl:>12,} {summe:>20,.2f} {prozent:>14.2f}%")
    print()
    
    # 4. 411xxx mit KST 1-7 in 5. Stelle, aber skr51_cost_center != 1-7
    print("4. 411xxx mit KST 1-7 in 5. Stelle, aber skr51_cost_center != 1-7:")
    cursor.execute(convert_placeholders("""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 5, 1) as kst_stelle,
            COALESCE(skr51_cost_center, -1) as skr51_cc,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as summe
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 411000 AND 411999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          AND (skr51_cost_center NOT BETWEEN 1 AND 7 OR skr51_cost_center IS NULL)
        GROUP BY kst_stelle, skr51_cc
        ORDER BY summe DESC
        LIMIT 20
    """), (datum_von, datum_bis))
    
    rows = cursor.fetchall()
    problem_411 = 0
    print(f"   {'KST':<6} {'skr51_cc':<12} {'Anzahl':>12} {'Summe (€)':>20}")
    print(f"   {'-'*6} {'-'*12} {'-'*12} {'-'*20}")
    for row in rows:
        d = row_to_dict(row)
        kst = d.get('kst_stelle', '')
        skr51_cc = d.get('skr51_cc', -1)
        anzahl = int(d.get('anzahl', 0))
        summe = float(d.get('summe', 0))
        problem_411 += summe
        print(f"   {kst:<6} {skr51_cc:<12} {anzahl:>12,} {summe:>20,.2f}")
    print(f"   {'-'*6} {'-'*12} {'-'*12} {'-'*20}")
    print(f"   {'GESAMT (Problem)':<20} {'':>12} {problem_411:>20,.2f}")
    print()
    
    # 5. 411xxx detailliert nach Konten (4stellig)
    print("5. 411xxx detailliert nach Konten (4stellig):")
    cursor.execute(convert_placeholders("""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 1, 4) || 'xx' as konten_4stellig,
            substr(CAST(nominal_account_number AS TEXT), 5, 1) as kst_stelle,
            COALESCE(skr51_cost_center, -1) as skr51_cc,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as summe
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 411000 AND 411999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
        GROUP BY konten_4stellig, kst_stelle, skr51_cc
        ORDER BY summe DESC
        LIMIT 30
    """), (datum_von, datum_bis))
    
    rows = cursor.fetchall()
    print(f"   {'Konten':<10} {'KST':<6} {'skr51_cc':<12} {'Anzahl':>12} {'Summe (€)':>20}")
    print(f"   {'-'*10} {'-'*6} {'-'*12} {'-'*12} {'-'*20}")
    for row in rows:
        d = row_to_dict(row)
        konten = d.get('konten_4stellig', '')
        kst = d.get('kst_stelle', '')
        skr51_cc = d.get('skr51_cc', -1)
        anzahl = int(d.get('anzahl', 0))
        summe = float(d.get('summe', 0))
        print(f"   {konten:<10} {kst:<6} {skr51_cc:<12} {anzahl:>12,} {summe:>20,.2f}")
    print()
    
    return {
        'gesamt_411': gesamt_411,
        'problem_411': problem_411
    }

def analysiere_monatlich(conn, jahr_start: int, monat_start: int, jahr_end: int, monat_end: int):
    """Monat-für-Monat-Analyse der direkten Kosten"""
    
    cursor = conn.cursor()
    
    print("=" * 100)
    print("ANALYSE 3: Monat-für-Monat-Vergleich direkte Kosten")
    print("=" * 100)
    print()
    
    # Berechne für jeden Monat
    monate = []
    current_date = datetime(jahr_start, monat_start, 1)
    end_date = datetime(jahr_end, monat_end, 1)
    
    while current_date <= end_date:
        monate.append((current_date.year, current_date.month))
        if current_date.month == 12:
            current_date = datetime(current_date.year + 1, 1, 1)
        else:
            current_date = datetime(current_date.year, current_date.month + 1, 1)
    
    print(f"{'Monat':<12} {'DRIVE (5.Stelle)':>20} {'Globalcube (skr51)':>20} {'Differenz':>20} {'% Diff':>10}")
    print(f"{'-'*12} {'-'*20} {'-'*20} {'-'*20} {'-'*10}")
    
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    
    for jahr, monat in monate:
        datum_von = f"{jahr}-{monat:02d}-01"
        if monat == 12:
            datum_bis = f"{jahr+1}-01-01"
        else:
            datum_bis = f"{jahr}-{monat+1:02d}-01"
        
        # DRIVE: 5. Stelle
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
              {guv_filter}
        """), (datum_von, datum_bis))
        
        row = cursor.fetchone()
        drive_wert = float((row[0] if row else 0) or 0)
        
        # Globalcube: skr51_cost_center
        cursor.execute(convert_placeholders(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 400000 AND 489999
              AND skr51_cost_center BETWEEN 1 AND 7
              AND NOT (
                nominal_account_number BETWEEN 415100 AND 415199
                OR nominal_account_number BETWEEN 424000 AND 424999
                OR nominal_account_number BETWEEN 435500 AND 435599
                OR nominal_account_number BETWEEN 438000 AND 438999
                OR nominal_account_number BETWEEN 455000 AND 456999
                OR nominal_account_number BETWEEN 487000 AND 487099
                OR nominal_account_number BETWEEN 491000 AND 497999
              )
              {guv_filter}
        """), (datum_von, datum_bis))
        
        row = cursor.fetchone()
        globalcube_wert = float((row[0] if row else 0) or 0)
        
        differenz = drive_wert - globalcube_wert
        prozent_diff = (differenz / globalcube_wert * 100) if globalcube_wert != 0 else 0
        
        monat_name = f"{jahr}-{monat:02d}"
        print(f"{monat_name:<12} {drive_wert:>20,.2f} {globalcube_wert:>20,.2f} {differenz:>20,.2f} {prozent_diff:>9.2f}%")
    
    print()

def test_fallback_logik(conn, datum_von: str, datum_bis: str):
    """Testet verschiedene Fallback-Logik-Varianten"""
    
    cursor = conn.cursor()
    
    print("=" * 100)
    print("ANALYSE 4: Fallback-Logik-Varianten (wie filtert Globalcube?)")
    print("=" * 100)
    print()
    
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    
    # Variante 1: Nur skr51_cost_center 1-7
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
          AND skr51_cost_center BETWEEN 1 AND 7
          AND NOT (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 455000 AND 456999
            OR nominal_account_number BETWEEN 487000 AND 487099
            OR nominal_account_number BETWEEN 491000 AND 497999
          )
          {guv_filter}
    """), (datum_von, datum_bis))
    
    row = cursor.fetchone()
    variant1 = float((row[0] if row else 0) or 0)
    
    # Variante 2: skr51_cost_center 1-7 ODER (skr51_cost_center = 0 UND 5. Stelle 1-7)
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
          AND (
            skr51_cost_center BETWEEN 1 AND 7
            OR (skr51_cost_center = 0 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7'))
          )
          AND NOT (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 455000 AND 456999
            OR nominal_account_number BETWEEN 487000 AND 487099
            OR nominal_account_number BETWEEN 491000 AND 497999
          )
          {guv_filter}
    """), (datum_von, datum_bis))
    
    row = cursor.fetchone()
    variant2 = float((row[0] if row else 0) or 0)
    
    # Variante 3: Nur 5. Stelle (DRIVE aktuell)
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
          {guv_filter}
    """), (datum_von, datum_bis))
    
    row = cursor.fetchone()
    variant3 = float((row[0] if row else 0) or 0)
    
    # Globalcube Ziel (aus vorheriger Analyse)
    globalcube_ziel = 2801501.76 - (2801501.76 - 2701120.19)  # DB3 Globalcube - Differenz
    # Oder: Globalcube direkte Kosten = DB3 Globalcube - DB2
    # Wir wissen: DB3 DRIVE = 2.701.120,19 €, DB3 Globalcube = 2.801.501,76 €
    # Differenz = 100.381,57 €
    # Also: Globalcube direkte Kosten = DRIVE direkte Kosten - 100.381,57 €
    globalcube_ziel = variant3 - 100381.57
    
    print(f"{'Variante':<50} {'Wert (€)':>20} {'Diff zu Ziel':>20}")
    print(f"{'-'*50} {'-'*20} {'-'*20}")
    print(f"{'1. Nur skr51_cost_center 1-7':<50} {variant1:>20,.2f} {abs(variant1 - globalcube_ziel):>20,.2f}")
    print(f"{'2. skr51_cc 1-7 ODER (skr51_cc=0 UND 5.Stelle 1-7)':<50} {variant2:>20,.2f} {abs(variant2 - globalcube_ziel):>20,.2f}")
    print(f"{'3. Nur 5. Stelle (DRIVE aktuell)':<50} {variant3:>20,.2f} {abs(variant3 - globalcube_ziel):>20,.2f}")
    print(f"{'Ziel (Globalcube, geschätzt)':<50} {globalcube_ziel:>20,.2f} {'0.00':>20}")
    print()

if __name__ == '__main__':
    # Zeitraum: Sep 2024 - Aug 2025 (Jahr)
    datum_von = '2024-09-01'
    datum_bis = '2025-09-01'
    
    conn = get_db()
    try:
        # Analyse 1: skr51_cost_center Verteilung
        result1 = analysiere_skr51_verteilung(conn, datum_von, datum_bis)
        
        # Analyse 2: 411xxx detailliert
        result2 = analysiere_411xxx_detailed(conn, datum_von, datum_bis)
        
        # Analyse 3: Monat-für-Monat
        analysiere_monatlich(conn, 2024, 9, 2025, 8)
        
        # Analyse 4: Fallback-Logik-Varianten
        test_fallback_logik(conn, datum_von, datum_bis)
        
        # Zusammenfassung
        print("=" * 100)
        print("ZUSAMMENFASSUNG:")
        print("=" * 100)
        print(f"Gesamt direkte Kosten (DRIVE): {result1['total_summe']:>20,.2f} €")
        print(f"Problem-Konten (skr51_cc=0):   {result1['problem_summe']:>20,.2f} € ({result1['problem_summe']/result1['total_summe']*100:.2f}%)")
        print(f"411xxx Gesamt:                 {result2['gesamt_411']:>20,.2f} €")
        print(f"411xxx Problem (skr51_cc!=1-7): {result2['problem_411']:>20,.2f} €")
        print()
        
    finally:
        conn.close()
