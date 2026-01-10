#!/usr/bin/env python3
"""
Identifiziert einzelne Buchungen, die die verbleibenden 4.591,87 € ausmachen
=============================================================================
Analysiert alle Buchungen detailliert, um spezifische Buchungen zu finden.
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

def analysiere_alle_buchungen(conn, datum_von: str, datum_bis: str):
    """Analysiert alle einzelnen Buchungen in direkten Kosten"""
    cursor = conn.cursor()
    
    print("=" * 120)
    print("ANALYSE: Alle einzelnen Buchungen in direkten Kosten")
    print("=" * 120)
    print()
    
    # Hole alle Buchungen
    cursor.execute(convert_placeholders("""
        SELECT 
            accounting_date,
            nominal_account_number,
            substr(CAST(nominal_account_number AS TEXT), 5, 1) as kst_stelle,
            COALESCE(skr51_cost_center, -1) as skr51_cc,
            debit_or_credit,
            posted_value / 100.0 as betrag,
            posting_text,
            document_number,
            document_type,
            subsidiary_to_company_ref
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
        ORDER BY nominal_account_number, accounting_date
    """), (datum_von, datum_bis))
    
    rows = cursor.fetchall()
    print(f"Anzahl Buchungen: {len(rows):,}")
    print()
    
    # Gruppiere nach verschiedenen Kriterien
    print("1. GRUPPIERUNG nach Kontenbereichen:")
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
        ORDER BY summe DESC
    """), (datum_von, datum_bis))
    
    print(f"{'Kontenbereich':<15} {'Anzahl':>12} {'Summe (€)':>20}")
    print(f"{'-'*15} {'-'*12} {'-'*20}")
    for row in cursor.fetchall():
        konten = row[0]
        anzahl = int(row[1])
        summe = float(row[2] or 0)
        print(f"{konten:<15} {anzahl:>12,} {summe:>20,.2f}")
    print()
    
    # Analysiere: Gibt es spezifische posting_text, die häufig vorkommen?
    print("2. GRUPPIERUNG nach posting_text (Top 20):")
    cursor.execute(convert_placeholders("""
        SELECT 
            COALESCE(posting_text, '(NULL)') as posting_text,
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
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
        GROUP BY posting_text
        ORDER BY summe DESC
        LIMIT 20
    """), (datum_von, datum_bis))
    
    print(f"{'posting_text':<60} {'Anzahl':>12} {'Summe (€)':>20}")
    print(f"{'-'*60} {'-'*12} {'-'*20}")
    for row in cursor.fetchall():
        text = (row[0] or '(NULL)')[:58]
        anzahl = int(row[1])
        summe = float(row[2] or 0)
        print(f"{text:<60} {anzahl:>12,} {summe:>20,.2f}")
    print()
    
    # Analysiere: Gibt es spezifische document_type?
    print("3. GRUPPIERUNG nach document_type:")
    cursor.execute(convert_placeholders("""
        SELECT 
            COALESCE(document_type, '(NULL)') as document_type,
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
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
        GROUP BY document_type
        ORDER BY summe DESC
    """), (datum_von, datum_bis))
    
    print(f"{'document_type':<30} {'Anzahl':>12} {'Summe (€)':>20}")
    print(f"{'-'*30} {'-'*12} {'-'*20}")
    for row in cursor.fetchall():
        doc_type = (row[0] or '(NULL)')[:28]
        anzahl = int(row[1])
        summe = float(row[2] or 0)
        print(f"{doc_type:<30} {anzahl:>12,} {summe:>20,.2f}")
    print()
    
    # Analysiere: Gibt es spezifische Standorte?
    print("4. GRUPPIERUNG nach Standort (subsidiary_to_company_ref):")
    cursor.execute(convert_placeholders("""
        SELECT 
            subsidiary_to_company_ref,
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
          AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
        GROUP BY subsidiary_to_company_ref
        ORDER BY summe DESC
    """), (datum_von, datum_bis))
    
    print(f"{'Standort':<15} {'Anzahl':>12} {'Summe (€)':>20}")
    print(f"{'-'*15} {'-'*12} {'-'*20}")
    for row in cursor.fetchall():
        standort = int(row[0] or 0)
        anzahl = int(row[1])
        summe = float(row[2] or 0)
        print(f"{standort:<15} {anzahl:>12,} {summe:>20,.2f}")
    print()

def finde_spezifische_buchungen(conn, datum_von: str, datum_bis: str, target_diff: float):
    """Findet spezifische Buchungen, die die Differenz erklären könnten"""
    cursor = conn.cursor()
    
    print("=" * 120)
    print("ANALYSE: Finde spezifische Buchungen, die die 4.591,87 € erklären")
    print("=" * 120)
    print()
    
    globalcube_ziel = 1736691.52
    drive_ohne_411 = 1741283.39
    aktueller_diff = drive_ohne_411 - globalcube_ziel
    
    print(f"DRIVE ohne 411xxx:         {drive_ohne_411:>20,.2f} €")
    print(f"Globalcube Ziel:            {globalcube_ziel:>20,.2f} €")
    print(f"Benötigte Reduktion:        {aktueller_diff:>20,.2f} €")
    print()
    
    # Hole alle Buchungen (ohne 411xxx) sortiert nach Betrag
    print("1. TOP 50 Buchungen (nach Betrag, ohne 411xxx):")
    cursor.execute(convert_placeholders("""
        SELECT 
            accounting_date,
            nominal_account_number,
            substr(CAST(nominal_account_number AS TEXT), 5, 1) as kst_stelle,
            COALESCE(skr51_cost_center, -1) as skr51_cc,
            debit_or_credit,
            posted_value / 100.0 as betrag,
            posting_text,
            document_number,
            document_type,
            subsidiary_to_company_ref
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
        ORDER BY ABS(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        ) DESC
        LIMIT 50
    """), (datum_von, datum_bis))
    
    print(f"{'Datum':<12} {'Konto':<10} {'KST':<6} {'Betrag (€)':>15} {'Text':<40} {'Doc':<15}")
    print(f"{'-'*12} {'-'*10} {'-'*6} {'-'*15} {'-'*40} {'-'*15}")
    
    rows = cursor.fetchall()
    for row in rows:
        datum = str(row[0] or '')
        konto = int(row[1] or 0)
        kst = row[2] or ''
        betrag = float(row[5] or 0)
        text = (str(row[6]) if row[6] else '(NULL)')[:38]
        doc = str(row[7]) if row[7] else '(NULL)'
        if len(doc) > 13:
            doc = doc[:13]
        print(f"{datum:<12} {konto:<10} {kst:<6} {betrag:>15,.2f} {text:<40} {doc:<15}")
    
    print()
    
    # Suche nach Buchungen, die nahe der Differenz sind (kumuliert)
    print("2. KUMULIERTE SUMME: Finde Buchungen, die zusammen ~4.591,87 € ergeben:")
    print("   (Teste verschiedene Kombinationen)")
    
    # Teste: Was wenn wir bestimmte Kontenbereiche zusätzlich ausschließen?
    test_bereiche = [
        ('410xxx', 410000, 410999),
        ('432xxx', 432000, 432999),
        ('436xxx', 436000, 436999),
        ('469xxx', 469000, 469999),
        ('489xxx', 489000, 489999),
    ]
    
    print(f"{'Ausschluss':<40} {'Nach Ausschluss':>20} {'Diff zu Ziel':>20}")
    print(f"{'-'*40} {'-'*20} {'-'*20}")
    
    for name, von, bis in test_bereiche:
        cursor.execute(convert_placeholders("""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 400000 AND 489999
              AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
              AND NOT (
                nominal_account_number BETWEEN 411000 AND 411999
                OR nominal_account_number BETWEEN 415100 AND 415199
                OR nominal_account_number BETWEEN 424000 AND 424999
                OR nominal_account_number BETWEEN 435500 AND 435599
                OR nominal_account_number BETWEEN 438000 AND 438999
                OR nominal_account_number BETWEEN 455000 AND 456999
                OR nominal_account_number BETWEEN 487000 AND 487099
                OR nominal_account_number BETWEEN 491000 AND 497999
                OR nominal_account_number BETWEEN %s AND %s
              )
              AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')
        """), (datum_von, datum_bis, von, bis))
        
        nach_ausschluss = float(cursor.fetchone()[0] or 0)
        diff = abs(nach_ausschluss - globalcube_ziel)
        status = "✅" if diff < 100 else "❌"
        print(f"{status} 411xxx + {name:<30} {nach_ausschluss:>20,.2f} {diff:>20,.2f}")
    
    print()
    
    # Analysiere: Gibt es Buchungen mit spezifischen Mustern?
    print("3. ANALYSE: Buchungen mit spezifischen Mustern:")
    
    # Teste: Buchungen mit bestimmten posting_text
    cursor.execute(convert_placeholders("""
        SELECT 
            posting_text,
            COUNT(*) as anzahl,
            COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as summe
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
          AND posting_text IS NOT NULL
        GROUP BY posting_text
        HAVING ABS(COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) - %s) <= %s * 0.5
        ORDER BY ABS(COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) - %s)
        LIMIT 10
    """), (datum_von, datum_bis, aktueller_diff, aktueller_diff, aktueller_diff))
    
    print(f"{'posting_text':<60} {'Anzahl':>12} {'Summe (€)':>20} {'Diff':>20}")
    print(f"{'-'*60} {'-'*12} {'-'*20} {'-'*20}")
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            text = (row[0] or '(NULL)')[:58]
            anzahl = int(row[1])
            summe = float(row[2] or 0)
            diff = abs(summe - aktueller_diff)
            print(f"{text:<60} {anzahl:>12,} {summe:>20,.2f} {diff:>20,.2f}")
    else:
        print("   Keine posting_text gefunden, die nahe der Differenz sind")
    print()

if __name__ == '__main__':
    datum_von = '2024-09-01'
    datum_bis = '2025-09-01'
    target_diff = 4591.87
    
    conn = get_db()
    try:
        # 1. Analysiere alle Buchungen
        analysiere_alle_buchungen(conn, datum_von, datum_bis)
        
        # 2. Finde spezifische Buchungen
        finde_spezifische_buchungen(conn, datum_von, datum_bis, target_diff)
        
    finally:
        conn.close()
