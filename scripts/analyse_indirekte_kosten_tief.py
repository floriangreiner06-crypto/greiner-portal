#!/usr/bin/env python3
"""
Tiefe Analyse: Indirekte Kosten -21.840,34 € Differenz
========================================================
Detaillierte Analyse aller Aspekte der indirekten Kosten.
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

def berechne_indirekte_kosten(conn, datum_von: str, datum_bis: str, exclude_ranges: list = None, include_ranges: list = None):
    """Berechnet indirekte Kosten mit optionalen Ausschlüssen und Hinzufügungen"""
    cursor = conn.cursor()
    
    exclude_sql = ""
    if exclude_ranges:
        exclude_conditions = []
        for von, bis in exclude_ranges:
            exclude_conditions.append(f"nominal_account_number BETWEEN {von} AND {bis}")
        if exclude_conditions:
            exclude_sql = "AND NOT (" + " OR ".join(exclude_conditions) + ")"
    
    include_sql = ""
    if include_ranges:
        include_conditions = []
        for von, bis in include_ranges:
            include_conditions.append(f"nominal_account_number BETWEEN {von} AND {bis}")
        if include_conditions:
            include_sql = "OR (" + " OR ".join(include_conditions) + ")"
    
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    
    base_conditions = """
        (nominal_account_number BETWEEN 400000 AND 499999
         AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
        OR (nominal_account_number BETWEEN 424000 AND 424999
            AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
        OR (nominal_account_number BETWEEN 438000 AND 438999
            AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
        OR nominal_account_number BETWEEN 498000 AND 499999
        OR (nominal_account_number BETWEEN 891000 AND 896999
            AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
    """
    
    if include_sql:
        where_clause = f"({base_conditions} {include_sql})"
    else:
        where_clause = f"({base_conditions})"
    
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND {where_clause}
          {exclude_sql}
          {guv_filter}
    """), (datum_von, datum_bis))
    
    row = cursor.fetchone()
    return float((row[0] if row else 0) or 0)

def analysiere_89xxxx_detailed(conn, datum_von: str, datum_bis: str):
    """Detaillierte Analyse von 89xxxx"""
    cursor = conn.cursor()
    
    print("=" * 100)
    print("ANALYSE: 89xxxx detailliert (ohne 8932xx)")
    print("=" * 100)
    print()
    
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    
    # 1. Nach 3-stelligen Kontenbereichen
    cursor.execute(convert_placeholders("""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 1, 3) || 'xxx' as konten_3stellig,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 891000 AND 896999
          AND NOT (nominal_account_number BETWEEN 893200 AND 893299)
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
        GROUP BY konten_3stellig
        ORDER BY wert DESC
    """), (datum_von, datum_bis))
    
    print(f"{'Kontenbereich':<15} {'Anzahl':>12} {'Wert (€)':>20}")
    print(f"{'-'*15} {'-'*12} {'-'*20}")
    rows = cursor.fetchall()
    gesamt_89 = 0
    for row in rows:
        konten = row[0]
        anzahl = int(row[1])
        wert = float(row[2] or 0)
        gesamt_89 += wert
        print(f"{konten:<15} {anzahl:>12,} {wert:>20,.2f}")
    print(f"{'-'*15} {'-'*12} {'-'*20}")
    print(f"{'GESAMT 89xxxx':<15} {'':>12} {gesamt_89:>20,.2f}")
    print()
    
    # 2. Nach 4-stelligen Kontenbereichen
    cursor.execute(convert_placeholders("""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 1, 4) || 'xx' as konten_4stellig,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 891000 AND 896999
          AND NOT (nominal_account_number BETWEEN 893200 AND 893299)
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
        GROUP BY konten_4stellig
        ORDER BY wert DESC
        LIMIT 20
    """), (datum_von, datum_bis))
    
    print(f"{'Konten (4stellig)':<20} {'Anzahl':>12} {'Wert (€)':>20}")
    print(f"{'-'*20} {'-'*12} {'-'*20}")
    for row in cursor.fetchall():
        konten = row[0]
        anzahl = int(row[1])
        wert = float(row[2] or 0)
        print(f"{konten:<20} {anzahl:>12,} {wert:>20,.2f}")
    print()
    
    return gesamt_89

def analysiere_4xxxx0_detailed(conn, datum_von: str, datum_bis: str):
    """Detaillierte Analyse von 4xxxx0 (KST 0)"""
    cursor = conn.cursor()
    
    print("=" * 100)
    print("ANALYSE: 4xxxx0 (KST 0) detailliert - Finde Kontenbereiche nahe 21.840,34 €")
    print("=" * 100)
    print()
    
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    target = 21840.34
    
    # Prüfe: Gibt es Kontenbereiche, die nahe 21.840,34 € sind?
    cursor.execute(convert_placeholders("""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 1, 3) || 'xxx' as konten_3stellig,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0'
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
        GROUP BY konten_3stellig
        HAVING ABS(COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) - %s) <= %s * 0.2
        ORDER BY ABS(COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) - %s)
    """), (datum_von, datum_bis, target, target, target))
    
    print(f"{'Kontenbereich':<20} {'Wert (€)':>20} {'Diff':>20}")
    print(f"{'-'*20} {'-'*20} {'-'*20}")
    rows = cursor.fetchall()
    for row in rows:
        konten = row[0]
        wert = float(row[2] or 0)
        diff = abs(wert - target)
        print(f"{konten:<20} {wert:>20,.2f} {diff:>20,.2f}")
    
    if not rows:
        print("   Keine Kontenbereiche gefunden, die nahe 21.840,34 € sind")
    print()
    
    # Prüfe: Gibt es Kontenbereiche, die zusammen 21.840,34 € ergeben?
    print("2. PRÜFE: Kombinationen von Kontenbereichen, die zusammen ~21.840,34 € ergeben:")
    cursor.execute(convert_placeholders("""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 1, 3) || 'xxx' as konten_3stellig,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0'
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
        GROUP BY konten_3stellig
        HAVING ABS(COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0)) > 5000
        ORDER BY wert DESC
    """), (datum_von, datum_bis))
    
    kontenbereiche = [(row[0], float(row[1] or 0)) for row in cursor.fetchall()]
    
    # Suche nach Kombinationen
    found = False
    for r in range(2, 5):
        for combo in combinations(kontenbereiche[:30], r):
            summe = sum(w for _, w in combo)
            if abs(summe - target) < 2000:
                found = True
                print(f"   ✅ Kombination von {r} Kontenbereichen = {summe:.2f} € (Diff: {abs(summe - target):.2f} €)")
                for konten, wert in combo:
                    print(f"      - {konten}: {wert:>15,.2f} €")
                print()
                break
        if found:
            break
    
    if not found:
        print("   ❌ Keine Kombination gefunden")
    print()

def analysiere_monatlich_indirekte(conn, jahr_start: int, monat_start: int, jahr_end: int, monat_end: int):
    """Monat-für-Monat-Analyse der indirekten Kosten"""
    cursor = conn.cursor()
    
    print("=" * 100)
    print("ANALYSE: Monat-für-Monat-Vergleich indirekte Kosten")
    print("=" * 100)
    print()
    
    monate = []
    from datetime import datetime
    current_date = datetime(jahr_start, monat_start, 1)
    end_date = datetime(jahr_end, monat_end, 1)
    
    while current_date <= end_date:
        monate.append((current_date.year, current_date.month))
        if current_date.month == 12:
            current_date = datetime(current_date.year + 1, 1, 1)
        else:
            current_date = datetime(current_date.year, current_date.month + 1, 1)
    
    print(f"{'Monat':<12} {'DRIVE (€)':>20} {'Diff zu Vormonat':>20}")
    print(f"{'-'*12} {'-'*20} {'-'*20}")
    
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    vorher = 0
    
    for jahr, monat in monate:
        datum_von = f"{jahr}-{monat:02d}-01"
        if monat == 12:
            datum_bis = f"{jahr+1}-01-01"
        else:
            datum_bis = f"{jahr}-{monat+1:02d}-01"
        
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
              {guv_filter}
        """), (datum_von, datum_bis))
        
        wert = float(cursor.fetchone()[0] or 0)
        diff = wert - vorher
        monat_name = f"{jahr}-{monat:02d}"
        print(f"{monat_name:<12} {wert:>20,.2f} {diff:>20,.2f}")
        vorher = wert
    
    print()

def test_varianten(conn, datum_von: str, datum_bis: str):
    """Testet verschiedene Varianten der indirekten Kosten"""
    cursor = conn.cursor()
    
    print("=" * 100)
    print("TEST: Verschiedene Varianten der indirekten Kosten")
    print("=" * 100)
    print()
    
    globalcube_ziel = 2479617.08
    
    # Variante 1: Aktuell (DRIVE)
    variant1 = berechne_indirekte_kosten(conn, datum_von, datum_bis)
    
    # Variante 2: Ohne 89xxxx
    variant2 = berechne_indirekte_kosten(conn, datum_von, datum_bis, exclude_ranges=[(891000, 896999)])
    
    # Variante 3: Ohne 891xxx
    variant3 = berechne_indirekte_kosten(conn, datum_von, datum_bis, exclude_ranges=[(891000, 891999)])
    
    # Variante 4: Ohne 896xxx
    variant4 = berechne_indirekte_kosten(conn, datum_von, datum_bis, exclude_ranges=[(896000, 896999)])
    
    # Variante 5: Ohne 89xxxx, aber mit bestimmten Kontenbereichen zusätzlich
    # Teste: Was wenn wir bestimmte Kontenbereiche zusätzlich zählen?
    
    print(f"{'Variante':<50} {'Wert (€)':>20} {'Diff zu Ziel':>20}")
    print(f"{'-'*50} {'-'*20} {'-'*20}")
    print(f"{'1. Aktuell (DRIVE)':<50} {variant1:>20,.2f} {abs(variant1 - globalcube_ziel):>20,.2f}")
    print(f"{'2. Ohne 89xxxx komplett':<50} {variant2:>20,.2f} {abs(variant2 - globalcube_ziel):>20,.2f}")
    print(f"{'3. Ohne 891xxx':<50} {variant3:>20,.2f} {abs(variant3 - globalcube_ziel):>20,.2f}")
    print(f"{'4. Ohne 896xxx':<50} {variant4:>20,.2f} {abs(variant4 - globalcube_ziel):>20,.2f}")
    print()
    
    # Teste: Was wenn wir bestimmte Kontenbereiche zusätzlich zählen?
    print("5. TEST: Zusätzliche Kontenbereiche:")
    print()
    
    # Prüfe: Gibt es Konten in 4xxxx0, die zusätzlich gezählt werden sollten?
    # Oder: Gibt es Konten, die ausgeschlossen werden sollten?
    
    # Teste: Was wenn wir bestimmte Kontenbereiche zusätzlich zählen?
    test_bereiche = [
        ('475xxx', 475000, 475999, '0'),
        ('481xxx', 481000, 481999, '0'),
        ('470xxx', 470000, 470999, '0'),
        ('415xxx', 415000, 415999, '0'),
        ('439xxx', 439000, 439999, '0'),
    ]
    
    print(f"{'Kontenbereich':<30} {'Wert (€)':>20} {'Mit Addition':>20} {'Diff zu Ziel':>20}")
    print(f"{'-'*30} {'-'*20} {'-'*20} {'-'*20}")
    
    for name, von, bis, kst in test_bereiche:
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
        
        wert = float(cursor.fetchone()[0] or 0)
        
        # Diese Konten sind bereits enthalten (KST 0), also macht es keinen Sinn, sie zusätzlich zu zählen
        # Aber: Vielleicht zählt Globalcube sie doppelt? Oder: Vielleicht zählt Globalcube sie nicht?
        
        # Teste: Was wenn wir diesen Bereich ausschließen?
        nach_ausschluss = berechne_indirekte_kosten(conn, datum_von, datum_bis, exclude_ranges=[(von, bis)])
        diff = abs(nach_ausschluss - globalcube_ziel)
        status = "✅" if diff < 1000 else "❌"
        print(f"{status} {name:<28} {wert:>20,.2f} {nach_ausschluss:>20,.2f} {diff:>20,.2f}")
    
    print()

def analysiere_posting_text(conn, datum_von: str, datum_bis: str):
    """Analysiert posting_text in indirekten Kosten"""
    cursor = conn.cursor()
    
    print("=" * 100)
    print("ANALYSE: posting_text in indirekten Kosten")
    print("=" * 100)
    print()
    
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    target = 21840.34
    
    # Prüfe: Gibt es posting_text, die zusammen nahe 21.840,34 € sind?
    cursor.execute(convert_placeholders("""
        SELECT 
            COALESCE(posting_text, '(NULL)') as posting_text,
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
        GROUP BY posting_text
        HAVING ABS(COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) - %s) <= %s * 0.3
        ORDER BY ABS(COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) - %s)
        LIMIT 20
    """), (datum_von, datum_bis, target, target, target))
    
    print(f"{'posting_text':<60} {'Anzahl':>12} {'Wert (€)':>20} {'Diff':>20}")
    print(f"{'-'*60} {'-'*12} {'-'*20} {'-'*20}")
    rows = cursor.fetchall()
    for row in rows:
        text = (str(row[0]) if row[0] else '(NULL)')[:58]
        anzahl = int(row[1])
        wert = float(row[2] or 0)
        diff = abs(wert - target)
        print(f"{text:<60} {anzahl:>12,} {wert:>20,.2f} {diff:>20,.2f}")
    
    if not rows:
        print("   Keine posting_text gefunden, die nahe 21.840,34 € sind")
    print()

if __name__ == '__main__':
    datum_von = '2024-09-01'
    datum_bis = '2025-09-01'
    
    conn = get_db()
    try:
        # 1. Analysiere 89xxxx detailliert
        gesamt_89 = analysiere_89xxxx_detailed(conn, datum_von, datum_bis)
        
        # 2. Analysiere 4xxxx0 detailliert
        analysiere_4xxxx0_detailed(conn, datum_von, datum_bis)
        
        # 3. Analysiere posting_text
        analysiere_posting_text(conn, datum_von, datum_bis)
        
        # 4. Monat-für-Monat
        analysiere_monatlich_indirekte(conn, 2024, 9, 2025, 8)
        
        # 5. Teste Varianten
        test_varianten(conn, datum_von, datum_bis)
        
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
        
    finally:
        conn.close()
