#!/usr/bin/env python3
"""
Identifiziert Kontenbereiche, die die 100k€ Differenz ausmachen
===============================================================
Testet verschiedene Kombinationen von Kontenbereichen, die ausgeschlossen werden könnten.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db_connection import get_db, convert_placeholders
from itertools import combinations

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

def analysiere_kontenbereiche(conn, datum_von: str, datum_bis: str):
    """Analysiert alle Kontenbereiche in direkten Kosten"""
    cursor = conn.cursor()
    
    print("=" * 100)
    print("ANALYSE: Kontenbereiche in direkten Kosten (detailliert)")
    print("=" * 100)
    print()
    
    # Gruppiere nach 3-stelligen Kontenbereichen
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
        ORDER BY wert DESC
    """), (datum_von, datum_bis))
    
    kontenbereiche = []
    rows = cursor.fetchall()
    print(f"{'Kontenbereich':<15} {'Anzahl':>12} {'Wert (€)':>20} {'% von Gesamt':>15}")
    print(f"{'-'*15} {'-'*12} {'-'*20} {'-'*15}")
    
    gesamt = 0
    for row in rows:
        d = row_to_dict(row)
        konten = d.get('konten_3stellig', '')
        anzahl = int(d.get('anzahl', 0))
        wert = float(d.get('wert', 0))
        kontenbereiche.append((konten, anzahl, wert))
        gesamt += wert
    
    for konten, anzahl, wert in kontenbereiche:
        prozent = (wert / gesamt * 100) if gesamt > 0 else 0
        print(f"{konten:<15} {anzahl:>12,} {wert:>20,.2f} {prozent:>14.2f}%")
    
    print(f"{'-'*15} {'-'*12} {'-'*20} {'-'*15}")
    print(f"{'GESAMT':<15} {'':>12} {gesamt:>20,.2f} 100.00%")
    print()
    
    return kontenbereiche, gesamt

def teste_ausschluss_kombinationen(conn, datum_von: str, datum_bis: str, kontenbereiche: list, target_diff: float):
    """Testet verschiedene Kombinationen von Kontenbereichen, die ausgeschlossen werden könnten"""
    
    print("=" * 100)
    print("TEST: Verschiedene Ausschluss-Kombinationen")
    print("=" * 100)
    print()
    
    # Globalcube Ziel (DRIVE - 100k€)
    drive_wert = berechne_direkte_kosten(conn, datum_von, datum_bis)
    globalcube_ziel = drive_wert - target_diff
    
    print(f"DRIVE direkte Kosten:     {drive_wert:>20,.2f} €")
    print(f"Globalcube Ziel:          {globalcube_ziel:>20,.2f} €")
    print(f"Ziel-Differenz:           {target_diff:>20,.2f} €")
    print()
    
    # Teste einzelne Kontenbereiche
    print("1. EINZELNE KONTENBEREICHE (nahe 100k€):")
    print(f"{'Kontenbereich':<15} {'Wert (€)':>20} {'Nach Ausschluss':>20} {'Diff zu Ziel':>20}")
    print(f"{'-'*15} {'-'*20} {'-'*20} {'-'*20}")
    
    for konten, anzahl, wert in kontenbereiche:
        if wert > 50000:  # Nur größere Bereiche testen
            von = int(konten.replace('xxx', '000'))
            bis = int(konten.replace('xxx', '999'))
            nach_ausschluss = berechne_direkte_kosten(conn, datum_von, datum_bis, [(von, bis)])
            diff = abs(nach_ausschluss - globalcube_ziel)
            status = "✅" if diff < 1000 else "❌"
            print(f"{status} {konten:<13} {wert:>20,.2f} {nach_ausschluss:>20,.2f} {diff:>20,.2f}")
    
    print()
    
    # Teste Kombinationen von 2-3 Kontenbereichen
    print("2. KOMBINATIONEN (2-3 Kontenbereiche, nahe 100k€):")
    print(f"{'Kontenbereiche':<40} {'Summe (€)':>20} {'Nach Ausschluss':>20} {'Diff zu Ziel':>20}")
    print(f"{'-'*40} {'-'*20} {'-'*20} {'-'*20}")
    
    # Filtere Kontenbereiche > 20k€
    relevante = [(k, a, w) for k, a, w in kontenbereiche if w > 20000]
    
    # Teste alle Kombinationen von 2-3 Kontenbereichen
    tested = set()
    for r in range(2, min(4, len(relevante) + 1)):
        for combo in combinations(relevante, r):
            konten_list = [k for k, a, w in combo]
            summe = sum(w for k, a, w in combo)
            
            # Nur testen, wenn Summe nahe 100k€ (±20k€)
            if 80000 <= summe <= 120000:
                ranges = []
                for konten, _, _ in combo:
                    von = int(konten.replace('xxx', '000'))
                    bis = int(konten.replace('xxx', '999'))
                    ranges.append((von, bis))
                
                # Prüfe, ob wir diese Kombination schon getestet haben
                combo_key = tuple(sorted(konten_list))
                if combo_key in tested:
                    continue
                tested.add(combo_key)
                
                nach_ausschluss = berechne_direkte_kosten(conn, datum_von, datum_bis, ranges)
                diff = abs(nach_ausschluss - globalcube_ziel)
                status = "✅" if diff < 1000 else "❌"
                konten_str = ", ".join(konten_list)
                if len(konten_str) > 37:
                    konten_str = konten_str[:34] + "..."
                print(f"{status} {konten_str:<38} {summe:>20,.2f} {nach_ausschluss:>20,.2f} {diff:>20,.2f}")
    
    print()
    
    # 3. Detaillierte Analyse: 4-stellige Kontenbereiche in 411xxx
    print("3. DETAILLIERTE ANALYSE: 4-stellige Kontenbereiche in 411xxx:")
    cursor = conn.cursor()
    cursor.execute(convert_placeholders("""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 1, 4) || 'xx' as konten_4stellig,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 411000 AND 411999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
        GROUP BY konten_4stellig
        ORDER BY wert DESC
    """), (datum_von, datum_bis))
    
    print(f"{'Konten (4stellig)':<20} {'Anzahl':>12} {'Wert (€)':>20} {'Nach Ausschluss':>20} {'Diff zu Ziel':>20}")
    print(f"{'-'*20} {'-'*12} {'-'*20} {'-'*20} {'-'*20}")
    
    rows = cursor.fetchall()
    for row in rows:
        d = row_to_dict(row)
        konten = d.get('konten_4stellig', '')
        anzahl = int(d.get('anzahl', 0))
        wert = float(d.get('wert', 0))
        
        if wert > 10000:  # Nur größere Bereiche testen
            von = int(konten.replace('xx', '00'))
            bis = int(konten.replace('xx', '99'))
            nach_ausschluss = berechne_direkte_kosten(conn, datum_von, datum_bis, [(von, bis)])
            diff = abs(nach_ausschluss - globalcube_ziel)
            status = "✅" if diff < 1000 else "❌"
            print(f"{status} {konten:<18} {anzahl:>12,} {wert:>20,.2f} {nach_ausschluss:>20,.2f} {diff:>20,.2f}")
    
    print()
    
    # 4. Teste: 411xxx + kleine Ergänzungen
    print("4. TEST: 411xxx + kleine Ergänzungen (nahe 100k€):")
    print(f"{'Kontenbereiche':<40} {'Summe (€)':>20} {'Nach Ausschluss':>20} {'Diff zu Ziel':>20}")
    print(f"{'-'*40} {'-'*20} {'-'*20} {'-'*20}")
    
    # 411xxx allein
    nach_411 = berechne_direkte_kosten(conn, datum_von, datum_bis, [(411000, 411999)])
    diff_411 = abs(nach_411 - globalcube_ziel)
    status_411 = "✅" if diff_411 < 1000 else "❌"
    wert_411 = 95789.70  # Bekannter Wert aus vorheriger Analyse
    print(f"{status_411} 411xxx allein{'':<30} {wert_411:>20,.2f} {nach_411:>20,.2f} {diff_411:>20,.2f}")
    
    # 411xxx + kleine Ergänzungen
    kleine_ergaenzungen = [(k, a, w) for k, a, w in kontenbereiche if 2000 <= w <= 10000]
    for konten, anzahl, wert in kleine_ergaenzungen[:5]:  # Top 5
        von = int(konten.replace('xxx', '000'))
        bis = int(konten.replace('xxx', '999'))
        summe = 95789.70 + wert
        nach_ausschluss = berechne_direkte_kosten(conn, datum_von, datum_bis, [(411000, 411999), (von, bis)])
        diff = abs(nach_ausschluss - globalcube_ziel)
        status = "✅" if diff < 1000 else "❌"
        konten_str = f"411xxx + {konten}"
        print(f"{status} {konten_str:<38} {summe:>20,.2f} {nach_ausschluss:>20,.2f} {diff:>20,.2f}")
    
    print()

if __name__ == '__main__':
    datum_von = '2024-09-01'
    datum_bis = '2025-09-01'
    target_diff = 100381.57  # Bekannte Differenz
    
    conn = get_db()
    try:
        # 1. Analysiere alle Kontenbereiche
        kontenbereiche, gesamt = analysiere_kontenbereiche(conn, datum_von, datum_bis)
        
        # 2. Teste Ausschluss-Kombinationen
        teste_ausschluss_kombinationen(conn, datum_von, datum_bis, kontenbereiche, target_diff)
        
        # Zusammenfassung
        print("=" * 100)
        print("ZUSAMMENFASSUNG:")
        print("=" * 100)
        print(f"Gesamt direkte Kosten (DRIVE): {gesamt:>20,.2f} €")
        print(f"Ziel-Differenz:                {target_diff:>20,.2f} €")
        print(f"Globalcube Ziel:               {gesamt - target_diff:>20,.2f} €")
        print()
        print("✅ = Diff < 1.000 € (sehr nah am Ziel)")
        print("❌ = Diff >= 1.000 €")
        print()
        
    finally:
        conn.close()
