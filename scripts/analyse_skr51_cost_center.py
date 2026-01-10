#!/usr/bin/env python3
"""
Analyse der skr51_cost_center Verteilung vs. 5. Stelle des Kontos
Identifiziert die Differenz zwischen DRIVE und Globalcube Filter-Logik
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db_connection import get_db, convert_placeholders

def row_to_dict(row):
    """Konvertiert eine Datenbank-Zeile in ein Dictionary"""
    if row is None:
        return {}
    if hasattr(row, '_asdict'):
        return row._asdict()
    if isinstance(row, dict):
        return row
    # HybridRow: Unterstützt sowohl Index- als auch Spaltennamen-Zugriff
    return {key: row[key] if hasattr(row, '__getitem__') else getattr(row, key, None) 
            for key in row.keys() if hasattr(row, 'keys')}

def analysiere_cost_center_verteilung(conn, datum_von: str, datum_bis: str):
    """Analysiert die Verteilung von skr51_cost_center vs. 5. Stelle des Kontos"""
    
    cursor = conn.cursor()
    
    print("=" * 80)
    print("ANALYSE: skr51_cost_center vs. 5. Stelle des Kontos")
    print("=" * 80)
    print(f"Zeitraum: {datum_von} bis {datum_bis}")
    print()
    
    # 1. Direkte Kosten nach 5. Stelle (DRIVE aktuell)
    print("1. DIREKTE KOSTEN nach 5. Stelle des Kontos (DRIVE aktuell):")
    cursor.execute(convert_placeholders("""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 5, 1) as kst_stelle,
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
        GROUP BY kst_stelle
        ORDER BY kst_stelle
    """), (datum_von, datum_bis))
    
    rows = cursor.fetchall()
    summe_drive = 0
    for row in rows:
        d = row_to_dict(row)
        print(f"  KST {d['kst_stelle']}: {d['anzahl']:>8} Buchungen, {d['summe']:>15,.2f} €")
        summe_drive += float(d['summe'] or 0)
    print(f"  GESAMT: {summe_drive:>15,.2f} €")
    print()
    
    # 2. Direkte Kosten nach skr51_cost_center (Globalcube)
    print("2. DIREKTE KOSTEN nach skr51_cost_center (Globalcube):")
    cursor.execute(convert_placeholders("""
        SELECT 
            skr51_cost_center,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as summe
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
        GROUP BY skr51_cost_center
        ORDER BY skr51_cost_center
    """), (datum_von, datum_bis))
    
    rows = cursor.fetchall()
    summe_globalcube = 0
    for row in rows:
        d = row_to_dict(row)
        print(f"  KST {d['skr51_cost_center']}: {d['anzahl']:>8} Buchungen, {d['summe']:>15,.2f} €")
        summe_globalcube += float(d['summe'] or 0)
    print(f"  GESAMT: {summe_globalcube:>15,.2f} €")
    print()
    
    # 3. Differenz-Analyse
    print("3. DIFFERENZ-ANALYSE:")
    differenz = summe_drive - summe_globalcube
    print(f"  DRIVE (5. Stelle):     {summe_drive:>15,.2f} €")
    print(f"  Globalcube (skr51_cc): {summe_globalcube:>15,.2f} €")
    print(f"  DIFFERENZ:              {differenz:>15,.2f} €")
    print()
    
    # 4. Konten mit KST 1-7 in 5. Stelle, aber skr51_cost_center != 1-7
    print("4. KONTEN mit KST 1-7 in 5. Stelle, aber skr51_cost_center != 1-7:")
    cursor.execute(convert_placeholders("""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 5, 1) as kst_stelle,
            skr51_cost_center,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as summe
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          AND (skr51_cost_center NOT BETWEEN 1 AND 7 OR skr51_cost_center IS NULL)
          AND NOT (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 455000 AND 456999
            OR nominal_account_number BETWEEN 487000 AND 487099
            OR nominal_account_number BETWEEN 491000 AND 497999
          )
        GROUP BY kst_stelle, skr51_cost_center
        ORDER BY summe DESC
        LIMIT 20
    """), (datum_von, datum_bis))
    
    rows = cursor.fetchall()
    summe_problem = 0
    for row in rows:
        d = row_to_dict(row)
        print(f"  KST-Stelle {d['kst_stelle']}, skr51_cc={d['skr51_cost_center']}: {d['anzahl']:>6} Buchungen, {d['summe']:>15,.2f} €")
        summe_problem += float(d['summe'] or 0)
    print(f"  GESAMT (Problem-Konten): {summe_problem:>15,.2f} €")
    print()
    
    # 5. Konten mit skr51_cost_center 1-7, aber KST != 1-7 in 5. Stelle
    print("5. KONTEN mit skr51_cost_center 1-7, aber KST != 1-7 in 5. Stelle:")
    cursor.execute(convert_placeholders("""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 5, 1) as kst_stelle,
            skr51_cost_center,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as summe
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
          AND skr51_cost_center BETWEEN 1 AND 7
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) NOT IN ('1','2','3','4','5','6','7')
          AND NOT (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 455000 AND 456999
            OR nominal_account_number BETWEEN 487000 AND 487099
            OR nominal_account_number BETWEEN 491000 AND 497999
          )
        GROUP BY kst_stelle, skr51_cost_center
        ORDER BY summe DESC
        LIMIT 20
    """), (datum_von, datum_bis))
    
    rows = cursor.fetchall()
    summe_globalcube_only = 0
    for row in rows:
        d = row_to_dict(row)
        print(f"  KST-Stelle {d['kst_stelle']}, skr51_cc={d['skr51_cost_center']}: {d['anzahl']:>6} Buchungen, {d['summe']:>15,.2f} €")
        summe_globalcube_only += float(d['summe'] or 0)
    print(f"  GESAMT (nur Globalcube): {summe_globalcube_only:>15,.2f} €")
    print()
    
    return {
        'drive': summe_drive,
        'globalcube': summe_globalcube,
        'differenz': differenz,
        'problem_konten': summe_problem,
        'globalcube_only': summe_globalcube_only
    }

if __name__ == '__main__':
    # Zeitraum: Sep 2024 - Aug 2025 (Jahr)
    datum_von = '2024-09-01'
    datum_bis = '2025-09-01'
    
    conn = get_db()
    try:
        result = analysiere_cost_center_verteilung(conn, datum_von, datum_bis)
        
        print("=" * 80)
        print("ZUSAMMENFASSUNG:")
        print("=" * 80)
        print(f"DRIVE Filter (5. Stelle):     {result['drive']:>15,.2f} €")
        print(f"Globalcube Filter (skr51_cc): {result['globalcube']:>15,.2f} €")
        print(f"DIFFERENZ:                    {result['differenz']:>15,.2f} €")
        print()
        print(f"Problem-Konten (DRIVE zählt, Globalcube nicht): {result['problem_konten']:>15,.2f} €")
        print(f"Globalcube-only (Globalcube zählt, DRIVE nicht): {result['globalcube_only']:>15,.2f} €")
        
    finally:
        conn.close()
