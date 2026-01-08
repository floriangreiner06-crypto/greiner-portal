"""
Detaillierte Analyse: GW August 2025 - Deggendorf (nur Stellantis)
===================================================================
Prüft alle Konten und Buchungen
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

datum_von = "2025-08-01"
datum_bis = "2025-09-01"

print("=" * 80)
print("Detaillierte Analyse: GW August 2025 - Deggendorf (nur Stellantis)")
print("=" * 80)

firma_filter_umsatz = "AND branch_number = 1 AND subsidiary_to_company_ref = 1"
firma_filter_einsatz = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 1"
guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"

with db_session() as conn:
    cursor = conn.cursor()
    
    # 1. Umsatz-Konten (820000-829999) - Top 10
    print("\n1. TOP 10 UMSATZ-KONTEN (820000-829999):")
    cursor.execute(convert_placeholders(f"""
        SELECT 
            nominal_account_number,
            SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz,
            COUNT(*) as anzahl
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 820000 AND 829999
          {firma_filter_umsatz}
          {guv_filter}
        GROUP BY nominal_account_number
        ORDER BY ABS(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END)) DESC
        LIMIT 10
    """), (datum_von, datum_bis))
    
    umsatz_konten = cursor.fetchall()
    umsatz_gesamt = 0
    for row in umsatz_konten:
        konto = row[0]
        umsatz = float(row[1] or 0)
        anzahl = int(row[2] or 0)
        umsatz_gesamt += umsatz
        print(f"  {konto}: {umsatz:>15,.2f} € ({anzahl} Buchungen)")
    print(f"  {'GESAMT':<10}: {umsatz_gesamt:>15,.2f} €")
    
    # 2. Einsatz-Konten (720000-729999) - Top 10
    print("\n2. TOP 10 EINSATZ-KONTEN (720000-729999):")
    cursor.execute(convert_placeholders(f"""
        SELECT 
            nominal_account_number,
            SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as einsatz,
            COUNT(*) as anzahl
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 720000 AND 729999
          {firma_filter_einsatz}
          {guv_filter}
        GROUP BY nominal_account_number
        ORDER BY ABS(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END)) DESC
        LIMIT 10
    """), (datum_von, datum_bis))
    
    einsatz_konten = cursor.fetchall()
    einsatz_gesamt = 0
    for row in einsatz_konten:
        konto = row[0]
        einsatz = float(row[1] or 0)
        anzahl = int(row[2] or 0)
        einsatz_gesamt += einsatz
        print(f"  {konto}: {einsatz:>15,.2f} € ({anzahl} Buchungen)")
    print(f"  {'GESAMT':<10}: {einsatz_gesamt:>15,.2f} €")
    
    # 3. DB1
    db1 = umsatz_gesamt - einsatz_gesamt
    print(f"\n3. DB1-BERECHNUNG:")
    print(f"  Umsatz: {umsatz_gesamt:>15,.2f} €")
    print(f"  Einsatz: {einsatz_gesamt:>15,.2f} €")
    print(f"  DB1: {db1:>15,.2f} €")
    print(f"\n  Benutzer-Angabe: 206.675,00 €")
    print(f"  Differenz: {db1 - 206675:>15,.2f} €")
    
    # 4. Prüfe ob es negative Umsätze gibt (Korrekturbuchungen?)
    print("\n4. NEGATIVE UMSATZ-BUCHUNGEN (mögliche Korrekturen):")
    cursor.execute(convert_placeholders(f"""
        SELECT 
            nominal_account_number,
            SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz,
            COUNT(*) as anzahl
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 820000 AND 829999
          {firma_filter_umsatz}
          {guv_filter}
        GROUP BY nominal_account_number
        HAVING SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) < 0
        ORDER BY umsatz ASC
        LIMIT 10
    """), (datum_von, datum_bis))
    
    negative = cursor.fetchall()
    if negative:
        for row in negative:
            konto = row[0]
            umsatz = float(row[1] or 0)
            anzahl = int(row[2] or 0)
            print(f"  {konto}: {umsatz:>15,.2f} € ({anzahl} Buchungen)")
    else:
        print("  Keine negativen Umsatz-Buchungen gefunden")
    
    # 5. Prüfe G&V-Abschlussbuchungen (sollten ausgeschlossen sein)
    print("\n5. G&V-ABSCHLUSSBUCHUNGEN (sollten ausgeschlossen sein):")
    cursor.execute(convert_placeholders(f"""
        SELECT 
            COUNT(*) as anzahl,
            SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 820000 AND 829999
          {firma_filter_umsatz}
          AND posting_text LIKE '%%G&V-Abschluss%%'
    """), (datum_von, datum_bis))
    
    row = cursor.fetchone()
    if row:
        anzahl = int(row[0] or 0)
        umsatz_guv = float(row[1] or 0) if row[1] else 0
        print(f"  Anzahl: {anzahl} Buchungen")
        print(f"  Umsatz: {umsatz_guv:,.2f} €")
        if umsatz_guv != 0:
            print(f"  ⚠️  WARNUNG: G&V-Abschlussbuchungen enthalten {umsatz_guv:,.2f} €!")

