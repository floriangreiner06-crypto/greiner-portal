#!/usr/bin/env python3
"""
Detaillierte Analyse: Indirekte Kosten -21.840,34 € Differenz
==============================================================
Findet genau, welche Konten die Differenz ausmachen.
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

def berechne_indirekte_kosten(conn, datum_von: str, datum_bis: str, exclude_ranges: list = None):
    """Berechnet indirekte Kosten mit optionalen Ausschlüssen"""
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
          AND (
            (nominal_account_number BETWEEN 400000 AND 499999
             AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
            OR (nominal_account_number BETWEEN 424000 AND 424999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR (nominal_account_number BETWEEN 438000 AND 438999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR nominal_account_number BETWEEN 498000 AND 499999
            OR (nominal_account_number BETWEEN 891000 AND 896999
                AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
          )
          {exclude_sql}
          {guv_filter}
    """), (datum_von, datum_bis))
    
    row = cursor.fetchone()
    return float((row[0] if row else 0) or 0)

def analysiere_indirekte_kosten_komponenten(conn, datum_von: str, datum_bis: str):
    """Analysiert die Komponenten der indirekten Kosten"""
    cursor = conn.cursor()
    
    print("=" * 100)
    print("ANALYSE: Indirekte Kosten - Komponenten")
    print("=" * 100)
    print()
    
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    
    # 1. KST 0 (4xxxx0)
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0'
          {guv_filter}
    """), (datum_von, datum_bis))
    kst0 = float(cursor.fetchone()[0] or 0)
    
    # 2. 424xx KST 1-7
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 424000 AND 424999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7')
          {guv_filter}
    """), (datum_von, datum_bis))
    kst424 = float(cursor.fetchone()[0] or 0)
    
    # 3. 438xx KST 1-7
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 438000 AND 438999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7')
          {guv_filter}
    """), (datum_von, datum_bis))
    kst438 = float(cursor.fetchone()[0] or 0)
    
    # 4. 498xx
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 498000 AND 499999
          {guv_filter}
    """), (datum_von, datum_bis))
    kst498 = float(cursor.fetchone()[0] or 0)
    
    # 5. 89xxxx (ohne 8932xx)
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 891000 AND 896999
          AND NOT (nominal_account_number BETWEEN 893200 AND 893299)
          {guv_filter}
    """), (datum_von, datum_bis))
    kst89 = float(cursor.fetchone()[0] or 0)
    
    gesamt = kst0 + kst424 + kst438 + kst498 + kst89
    
    print(f"{'Komponente':<30} {'Wert (€)':>20} {'% von Gesamt':>15}")
    print(f"{'-'*30} {'-'*20} {'-'*15}")
    print(f"{'KST 0 (4xxxx0)':<30} {kst0:>20,.2f} {kst0/gesamt*100:>14.2f}%")
    print(f"{'424xx KST 1-7':<30} {kst424:>20,.2f} {kst424/gesamt*100:>14.2f}%")
    print(f"{'438xx KST 1-7':<30} {kst438:>20,.2f} {kst438/gesamt*100:>14.2f}%")
    print(f"{'498xx':<30} {kst498:>20,.2f} {kst498/gesamt*100:>14.2f}%")
    print(f"{'89xxxx (ohne 8932xx)':<30} {kst89:>20,.2f} {kst89/gesamt*100:>14.2f}%")
    print(f"{'-'*30} {'-'*20} {'-'*15}")
    print(f"{'GESAMT':<30} {gesamt:>20,.2f} 100.00%")
    print()
    
    return {
        'kst0': kst0,
        'kst424': kst424,
        'kst438': kst438,
        'kst498': kst498,
        'kst89': kst89,
        'gesamt': gesamt
    }

def analysiere_kontenbereiche(conn, datum_von: str, datum_bis: str):
    """Analysiert Kontenbereiche in indirekten Kosten"""
    cursor = conn.cursor()
    
    print("=" * 100)
    print("ANALYSE: Kontenbereiche in indirekten Kosten")
    print("=" * 100)
    print()
    
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    
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
          AND (
            (nominal_account_number BETWEEN 400000 AND 499999
             AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
            OR (nominal_account_number BETWEEN 424000 AND 424999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR (nominal_account_number BETWEEN 438000 AND 438999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR nominal_account_number BETWEEN 498000 AND 499999
            OR (nominal_account_number BETWEEN 891000 AND 896999
                AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
          )
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
        GROUP BY konten_3stellig
        ORDER BY wert DESC
    """), (datum_von, datum_bis))
    
    print(f"{'Kontenbereich':<15} {'Anzahl':>12} {'Wert (€)':>20} {'% von Gesamt':>15}")
    print(f"{'-'*15} {'-'*12} {'-'*20} {'-'*15}")
    
    rows = cursor.fetchall()
    gesamt = 0
    for row in rows:
        konten = row[0]
        anzahl = int(row[1])
        wert = float(row[2] or 0)
        gesamt += wert
    
    for row in rows:
        konten = row[0]
        anzahl = int(row[1])
        wert = float(row[2] or 0)
        prozent = (wert / gesamt * 100) if gesamt > 0 else 0
        print(f"{konten:<15} {anzahl:>12,} {wert:>20,.2f} {prozent:>14.2f}%")
    
    print(f"{'-'*15} {'-'*12} {'-'*20} {'-'*15}")
    print(f"{'GESAMT':<15} {'':>12} {gesamt:>20,.2f} 100.00%")
    print()
    
    return gesamt

def finde_21840_euro(conn, datum_von: str, datum_bis: str, target_diff: float):
    """Findet genau die Konten, die die 21.840,34 € Differenz ausmachen"""
    cursor = conn.cursor()
    
    print("=" * 100)
    print("ANALYSE: Finde genau die 21.840,34 € Differenz")
    print("=" * 100)
    print()
    
    globalcube_ziel = 2479617.08
    drive_aktuell = berechne_indirekte_kosten(conn, datum_von, datum_bis)
    aktueller_diff = drive_aktuell - globalcube_ziel
    
    print(f"DRIVE aktuell:         {drive_aktuell:>20,.2f} €")
    print(f"Globalcube Ziel:       {globalcube_ziel:>20,.2f} €")
    print(f"Aktuelle Differenz:    {aktueller_diff:>20,.2f} €")
    print(f"Ziel: Differenz = 0,00 €")
    print()
    
    # Prüfe: Gibt es Kontenbereiche, die nahe der Differenz sind?
    print("1. PRÜFE: Kontenbereiche, die nahe 21.840,34 € sind:")
    cursor.execute(convert_placeholders("""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 1, 3) || 'xxx' as konten_3stellig,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND (
            (nominal_account_number BETWEEN 400000 AND 499999
             AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
            OR (nominal_account_number BETWEEN 424000 AND 424999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR (nominal_account_number BETWEEN 438000 AND 438999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR nominal_account_number BETWEEN 498000 AND 499999
            OR (nominal_account_number BETWEEN 891000 AND 896999
                AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
          )
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
        GROUP BY konten_3stellig
        HAVING ABS(COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) - %s) <= %s * 0.5
        ORDER BY ABS(COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) - %s)
    """), (datum_von, datum_bis, abs(aktueller_diff), abs(aktueller_diff), abs(aktueller_diff)))
    
    print(f"{'Kontenbereich':<20} {'Wert (€)':>20} {'Diff zu Ziel':>20}")
    print(f"{'-'*20} {'-'*20} {'-'*20}")
    
    rows = cursor.fetchall()
    for row in rows:
        konten = row[0]
        wert = float(row[2] or 0)
        diff = abs(wert - abs(aktueller_diff))
        print(f"{konten:<20} {wert:>20,.2f} {diff:>20,.2f}")
    
    print()
    
    # Prüfe: Gibt es Konten, die Globalcube zählt, aber DRIVE nicht?
    print("2. PRÜFE: Könnte Globalcube zusätzliche Konten zählen?")
    print("   (z.B. andere Filter-Logik für KST)")
    
    # Teste: Was wenn Globalcube auch andere KST zählt?
    # Aktuell: DRIVE zählt KST 0, aber vielleicht zählt Globalcube auch andere?
    
    # Teste: Was wenn Globalcube skr51_cost_center verwendet statt 5. Stelle?
    cursor.execute(convert_placeholders("""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND (
            (nominal_account_number BETWEEN 400000 AND 499999
             AND skr51_cost_center = 0)
            OR (nominal_account_number BETWEEN 424000 AND 424999
                AND skr51_cost_center IN (1,2,3,6,7))
            OR (nominal_account_number BETWEEN 438000 AND 438999
                AND skr51_cost_center IN (1,2,3,6,7))
            OR nominal_account_number BETWEEN 498000 AND 499999
            OR (nominal_account_number BETWEEN 891000 AND 896999
                AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
          )
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
    """), (datum_von, datum_bis))
    
    test_skr51 = float(cursor.fetchone()[0] or 0)
    diff_skr51 = abs(test_skr51 - globalcube_ziel)
    
    print(f"   Test (skr51_cost_center statt 5. Stelle): {test_skr51:>20,.2f} € (Diff: {diff_skr51:>10,.2f} €)")
    print()
    
    # Prüfe: Gibt es Kontenbereiche, die DRIVE zählt, aber Globalcube nicht?
    print("3. PRÜFE: Kontenbereiche, die möglicherweise ausgeschlossen werden sollten:")
    
    # Analysiere: Welche Kontenbereiche könnten problematisch sein?
    kontenbereiche = [
        ('400xxx KST 0', 400000, 400999, '0'),
        ('401xxx KST 0', 401000, 401999, '0'),
        ('402xxx KST 0', 402000, 402999, '0'),
        ('403xxx KST 0', 403000, 403999, '0'),
        ('404xxx KST 0', 404000, 404999, '0'),
        ('405xxx KST 0', 405000, 405999, '0'),
        ('406xxx KST 0', 406000, 406999, '0'),
        ('407xxx KST 0', 407000, 407999, '0'),
        ('408xxx KST 0', 408000, 408999, '0'),
        ('409xxx KST 0', 409000, 409999, '0'),
        ('498xxx', 498000, 498999, None),
        ('499xxx', 499000, 499999, None),
    ]
    
    print(f"{'Kontenbereich':<30} {'Wert (€)':>20} {'Nach Ausschluss':>20} {'Diff zu Ziel':>20}")
    print(f"{'-'*30} {'-'*20} {'-'*20} {'-'*20}")
    
    for name, von, bis, kst in kontenbereiche:
        if kst:
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN %s AND %s
                  AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = %s
                  AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
            """), (datum_von, datum_bis, von, bis, kst))
        else:
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN %s AND %s
                  AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
            """), (datum_von, datum_bis, von, bis))
        
        wert = float(cursor.fetchone()[0] or 0)
        
        if wert > 1000:  # Nur größere Bereiche testen
            nach_ausschluss = berechne_indirekte_kosten(conn, datum_von, datum_bis, [(von, bis)])
            diff = abs(nach_ausschluss - globalcube_ziel)
            status = "✅" if diff < 1000 else "❌"
            print(f"{status} {name:<28} {wert:>20,.2f} {nach_ausschluss:>20,.2f} {diff:>20,.2f}")
    
    print()

if __name__ == '__main__':
    datum_von = '2024-09-01'
    datum_bis = '2025-09-01'
    target_diff = 21840.34
    
    conn = get_db()
    try:
        # 1. Analysiere Komponenten
        komponenten = analysiere_indirekte_kosten_komponenten(conn, datum_von, datum_bis)
        
        # 2. Analysiere Kontenbereiche
        gesamt = analysiere_kontenbereiche(conn, datum_von, datum_bis)
        
        # 3. Finde genau die 21.840,34 €
        finde_21840_euro(conn, datum_von, datum_bis, target_diff)
        
        # Zusammenfassung
        print("=" * 100)
        print("ZUSAMMENFASSUNG:")
        print("=" * 100)
        drive_aktuell = berechne_indirekte_kosten(conn, datum_von, datum_bis)
        globalcube_ziel = 2479617.08
        
        print(f"DRIVE indirekte Kosten:  {drive_aktuell:>20,.2f} €")
        print(f"Globalcube Ziel:          {globalcube_ziel:>20,.2f} €")
        print(f"Differenz:                {abs(drive_aktuell - globalcube_ziel):>20,.2f} €")
        print()
        print("✅ = Diff < 1.000 € (sehr nah am Ziel)")
        print("❌ = Diff >= 1.000 €")
        print()
        
    finally:
        conn.close()
