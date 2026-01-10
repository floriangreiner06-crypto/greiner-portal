#!/usr/bin/env python3
"""
Detaillierte Analyse: Die verbleibenden 4.591,87 € Differenz
=============================================================
Findet genau, welche Konten die verbleibende Differenz ausmachen.
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
    try:
        if hasattr(row, 'keys'):
            return {key: row[key] for key in row.keys()}
    except:
        pass
    return dict(row) if hasattr(row, '__iter__') else {}

def berechne_direkte_kosten(conn, datum_von: str, datum_bis: str, exclude_ranges: list = None):
    """Berechnet direkte Kosten mit optionalen Ausschlüssen"""
    cursor = conn.cursor()
    
    exclude_sql = ""
    if exclude_ranges:
        exclude_conditions = []
        for von, bis in exclude_ranges:
            exclude_conditions.append(f"nominal_account_number BETWEEN {von} AND {bis}")
        if exclude_conditions:
            exclude_sql = "AND NOT (" + " OR ".join(exclude_conditions) + ")"
    
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    
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
          {exclude_sql}
          {guv_filter}
    """), (datum_von, datum_bis))
    
    row = cursor.fetchone()
    return float((row[0] if row else 0) or 0)

def analysiere_411xxx_detailed(conn, datum_von: str, datum_bis: str):
    """Detaillierte Analyse aller 411xxx-Konten (5-stellig und 6-stellig)"""
    cursor = conn.cursor()
    
    print("=" * 100)
    print("ANALYSE 1: 411xxx Konten detailliert (5-stellig)")
    print("=" * 100)
    print()
    
    # 5-stellige Konten
    cursor.execute(convert_placeholders("""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 1, 5) || 'x' as konten_5stellig,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 411000 AND 411999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
        GROUP BY konten_5stellig
        ORDER BY wert DESC
    """), (datum_von, datum_bis))
    
    print(f"{'Konten (5stellig)':<20} {'Anzahl':>12} {'Wert (€)':>20}")
    print(f"{'-'*20} {'-'*12} {'-'*20}")
    
    rows = cursor.fetchall()
    gesamt_411 = 0
    for row in rows:
        d = row_to_dict(row)
        konten = d.get('konten_5stellig', '')
        anzahl = int(d.get('anzahl', 0))
        wert = float(d.get('wert', 0))
        gesamt_411 += wert
        print(f"{konten:<20} {anzahl:>12,} {wert:>20,.2f}")
    
    print(f"{'-'*20} {'-'*12} {'-'*20}")
    print(f"{'GESAMT 411xxx':<20} {'':>12} {gesamt_411:>20,.2f}")
    print()
    
    # 6-stellige Konten (alle einzelnen Konten)
    print("=" * 100)
    print("ANALYSE 2: 411xxx Konten detailliert (6-stellig - alle einzelnen Konten)")
    print("=" * 100)
    print()
    
    cursor.execute(convert_placeholders("""
        SELECT 
            nominal_account_number,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert,
            substr(CAST(nominal_account_number AS TEXT), 5, 1) as kst_stelle,
            COALESCE(skr51_cost_center, -1) as skr51_cc
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 411000 AND 411999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
        GROUP BY nominal_account_number, kst_stelle, skr51_cc
        ORDER BY wert DESC
    """), (datum_von, datum_bis))
    
    print(f"{'Konto':<10} {'KST':<6} {'skr51_cc':<12} {'Anzahl':>12} {'Wert (€)':>20}")
    print(f"{'-'*10} {'-'*6} {'-'*12} {'-'*12} {'-'*20}")
    
    rows = cursor.fetchall()
    gesamt_411_detailed = 0
    for row in rows:
        d = row_to_dict(row)
        konto = int(d.get('nominal_account_number', 0))
        kst = d.get('kst_stelle', '')
        skr51_cc = d.get('skr51_cc', -1)
        anzahl = int(d.get('anzahl', 0))
        wert = float(d.get('wert', 0))
        gesamt_411_detailed += wert
        print(f"{konto:<10} {kst:<6} {skr51_cc:<12} {anzahl:>12,} {wert:>20,.2f}")
    
    print(f"{'-'*10} {'-'*6} {'-'*12} {'-'*12} {'-'*20}")
    print(f"{'GESAMT':<10} {'':<6} {'':<12} {'':>12} {gesamt_411_detailed:>20,.2f}")
    print()
    
    return gesamt_411, rows

def finde_4600_euro(conn, datum_von: str, datum_bis: str, target_diff: float):
    """Findet genau die Konten, die die 4.591,87 € Differenz ausmachen"""
    cursor = conn.cursor()
    
    print("=" * 100)
    print("ANALYSE 3: Finde genau die 4.591,87 € Differenz")
    print("=" * 100)
    print()
    
    globalcube_ziel = 1736691.52
    drive_ohne_411 = berechne_direkte_kosten(conn, datum_von, datum_bis, [(411000, 411999)])
    aktueller_diff = drive_ohne_411 - globalcube_ziel
    
    print(f"DRIVE ohne 411xxx:         {drive_ohne_411:>20,.2f} €")
    print(f"Globalcube Ziel:           {globalcube_ziel:>20,.2f} €")
    print(f"Aktuelle Differenz:        {aktueller_diff:>20,.2f} €")
    print(f"Ziel: Differenz = 0,00 €")
    print()
    
    # Suche nach Kontenbereichen, die genau diese Differenz ergeben
    print("1. PRÜFE: Alle Kontenbereiche (außer 411xxx), die nahe der Differenz sind:")
    cursor.execute(convert_placeholders("""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 1, 3) || 'xxx' as konten_3stellig,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
          AND NOT (nominal_account_number BETWEEN 411000 AND 411999)
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
        GROUP BY konten_3stellig
        HAVING ABS(COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) - %s) <= %s * 0.5
        ORDER BY ABS(COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) - %s)
    """), (datum_von, datum_bis, aktueller_diff, aktueller_diff, aktueller_diff))
    
    print(f"{'Kontenbereich':<20} {'Wert (€)':>20} {'Diff zu Ziel':>20}")
    print(f"{'-'*20} {'-'*20} {'-'*20}")
    
    rows = cursor.fetchall()
    for row in rows:
        d = row_to_dict(row)
        konten = d.get('konten_3stellig', '')
        wert = float(d.get('wert', 0))
        diff = abs(wert - aktueller_diff)
        print(f"{konten:<20} {wert:>20,.2f} {diff:>20,.2f}")
    
    print()
    
    # Prüfe: Gibt es spezifische Konten innerhalb 411xxx, die ausgeschlossen werden?
    print("2. PRÜFE: Spezifische Konten innerhalb 411xxx, die ausgeschlossen werden könnten:")
    cursor.execute(convert_placeholders("""
        SELECT 
            nominal_account_number,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 411000 AND 411999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
        GROUP BY nominal_account_number
        HAVING ABS(COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) - %s) <= %s * 0.5
        ORDER BY ABS(COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) - %s)
    """), (datum_von, datum_bis, aktueller_diff, aktueller_diff, aktueller_diff))
    
    print(f"{'Konto':<10} {'Anzahl':>12} {'Wert (€)':>20} {'Diff zu Ziel':>20}")
    print(f"{'-'*10} {'-'*12} {'-'*20} {'-'*20}")
    
    rows = cursor.fetchall()
    for row in rows:
        d = row_to_dict(row)
        konto = int(d.get('nominal_account_number', 0))
        anzahl = int(d.get('anzahl', 0))
        wert = float(d.get('wert', 0))
        diff = abs(wert - aktueller_diff)
        print(f"{konto:<10} {anzahl:>12,} {wert:>20,.2f} {diff:>20,.2f}")
    
    print()
    
    # Teste: Was wenn wir bestimmte Konten innerhalb 411xxx ausschließen?
    print("3. TEST: Verschiedene Ausschlüsse innerhalb 411xxx:")
    print(f"{'Ausschluss':<40} {'Nach Ausschluss':>20} {'Diff zu Ziel':>20}")
    print(f"{'-'*40} {'-'*20} {'-'*20}")
    
    # Teste: Nur bestimmte KST innerhalb 411xxx
    for kst in ['1', '2', '3', '6', '7']:
        cursor.execute(convert_placeholders("""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 411000 AND 411999
              AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = %s
              AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
        """), (datum_von, datum_bis, kst))
        
        wert_kst = float(cursor.fetchone()[0] or 0)
        
        # Teste Ausschluss dieser KST
        exclude_ranges = [(411000, 411999)]
        # Aber wir müssen die anderen KST behalten - das ist komplizierter
        # Stattdessen: Teste Ausschluss der gesamten 411xxx und dann Addition dieser KST
        nach_ausschluss = berechne_direkte_kosten(conn, datum_von, datum_bis, exclude_ranges) + wert_kst
        diff = abs(nach_ausschluss - globalcube_ziel)
        status = "✅" if diff < 100 else "❌"
        print(f"{status} 411xxx OHNE KST {kst} (nur KST {kst} behalten) {'':<20} {nach_ausschluss:>20,.2f} {diff:>20,.2f}")
    
    print()
    
    # Teste: Kombinationen von kleinen Kontenbereichen
    print("4. TEST: Kombinationen kleiner Kontenbereiche (außer 411xxx):")
    print(f"{'Kombination':<40} {'Summe (€)':>20} {'Nach Ausschluss':>20} {'Diff zu Ziel':>20}")
    print(f"{'-'*40} {'-'*20} {'-'*20} {'-'*20}")
    
    # Kleine Kontenbereiche
    kleine_bereiche = [
        ('410xxx', 410000, 410999, 31484.22),
        ('432xxx', 432000, 432999, 33499.49),
        ('469xxx', 469000, 469999, 23351.35),
        ('436xxx', 436000, 436999, 10472.67),
    ]
    
    # Teste einzelne kleine Bereiche zusätzlich zu 411xxx
    for name, von, bis, wert in kleine_bereiche:
        exclude_ranges = [(411000, 411999), (von, bis)]
        nach_ausschluss = berechne_direkte_kosten(conn, datum_von, datum_bis, exclude_ranges)
        diff = abs(nach_ausschluss - globalcube_ziel)
        status = "✅" if diff < 100 else "❌"
        summe = 95789.70 + wert
        print(f"{status} 411xxx + {name:<30} {summe:>20,.2f} {nach_ausschluss:>20,.2f} {diff:>20,.2f}")
    
    # Teste Kombinationen von 2 kleinen Bereichen
    from itertools import combinations
    for combo in combinations(kleine_bereiche, 2):
        names = [name for name, _, _, _ in combo]
        ranges = [(411000, 411999)] + [(von, bis) for _, von, bis, _ in combo]
        summe = 95789.70 + sum(wert for _, _, _, wert in combo)
        nach_ausschluss = berechne_direkte_kosten(conn, datum_von, datum_bis, ranges)
        diff = abs(nach_ausschluss - globalcube_ziel)
        status = "✅" if diff < 100 else "❌"
        combo_str = "411xxx + " + " + ".join(names)
        if len(combo_str) > 37:
            combo_str = combo_str[:34] + "..."
        print(f"{status} {combo_str:<38} {summe:>20,.2f} {nach_ausschluss:>20,.2f} {diff:>20,.2f}")
    
    print()

if __name__ == '__main__':
    datum_von = '2024-09-01'
    datum_bis = '2025-09-01'
    target_diff = 4591.87  # Verbleibende Differenz nach Ausschluss von 411xxx
    
    conn = get_db()
    try:
        # 1. Detaillierte Analyse 411xxx
        gesamt_411, rows_411 = analysiere_411xxx_detailed(conn, datum_von, datum_bis)
        
        # 2. Finde genau die 4.591,87 €
        finde_4600_euro(conn, datum_von, datum_bis, target_diff)
        
        # Zusammenfassung
        print("=" * 100)
        print("ZUSAMMENFASSUNG:")
        print("=" * 100)
        drive_gesamt = berechne_direkte_kosten(conn, datum_von, datum_bis)
        drive_ohne_411 = berechne_direkte_kosten(conn, datum_von, datum_bis, [(411000, 411999)])
        globalcube_ziel = 1736691.52
        
        print(f"DRIVE gesamt:              {drive_gesamt:>20,.2f} €")
        print(f"DRIVE ohne 411xxx:         {drive_ohne_411:>20,.2f} €")
        print(f"Globalcube Ziel:           {globalcube_ziel:>20,.2f} €")
        print(f"Verbleibende Differenz:    {abs(drive_ohne_411 - globalcube_ziel):>20,.2f} €")
        print()
        print("✅ = Diff < 100 € (sehr genau)")
        print("❌ = Diff >= 100 €")
        print()
        
    finally:
        conn.close()
