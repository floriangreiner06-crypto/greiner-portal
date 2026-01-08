"""
Analyse: Prüfe, ob Kosten mit 6. Ziffer '2' fälschlich zugeordnet werden
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

print("=" * 100)
print("ANALYSE: Kosten-Zuordnung nach 6. Ziffer")
print("Zeitraum: Dezember 2025")
print("=" * 100)

monat = 12
jahr = 2025
datum_von = f"{jahr}-{monat:02d}-01"
datum_bis = f"{jahr+1}-01-01"

guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"

with db_session() as conn:
    cursor = conn.cursor()
    
    # Prüfe alle Stellantis-Kosten nach 6. Ziffer und branch_number
    print("\n" + "=" * 100)
    print("Stellantis Kosten: 6. Ziffer vs. branch_number")
    print("=" * 100)
    
    cursor.execute(convert_placeholders(f"""
        SELECT 
            substr(CAST(nominal_account_number AS TEXT), 6, 1) as ziffer_6,
            branch_number,
            COUNT(*) as anzahl,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as summe
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND subsidiary_to_company_ref = 1
          {guv_filter}
        GROUP BY substr(CAST(nominal_account_number AS TEXT), 6, 1), branch_number
        ORDER BY ziffer_6, branch_number
    """), (datum_von, datum_bis))
    
    print("\nKombinationen (6. Ziffer | branch_number):")
    for row in cursor.fetchall():
        r = row_to_dict(row)
        print(f"  6. Ziffer '{r['ziffer_6']}' | branch {r['branch_number']}: {r['anzahl']} Buchungen, Summe: {r['summe']:,.2f} €")
    
    # Prüfe speziell: branch_number=1 (Deggendorf) mit 6. Ziffer '2'
    print("\n" + "=" * 100)
    print("PROBLEM: Deggendorf (branch=1) mit 6. Ziffer '2'")
    print("=" * 100)
    
    cursor.execute(convert_placeholders(f"""
        SELECT 
            nominal_account_number,
            COUNT(*) as anzahl,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as summe
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND subsidiary_to_company_ref = 1
          AND branch_number = 1
          AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'
          {guv_filter}
        GROUP BY nominal_account_number
        ORDER BY summe DESC
        LIMIT 20
    """), (datum_von, datum_bis))
    
    print("\nTop 20 Konten (Deggendorf branch=1, aber 6. Ziffer='2'):")
    total = 0
    for row in cursor.fetchall():
        r = row_to_dict(row)
        total += r['summe']
        print(f"  Konto {r['nominal_account_number']}: {r['anzahl']} Buchungen, {r['summe']:,.2f} €")
    print(f"\n  Gesamt: {total:,.2f} €")
    print(f"  ⚠️  Diese Kosten werden aktuell NICHT Deggendorf zugeordnet (Filter sucht 6. Ziffer '1')")
    
    # Prüfe: branch_number=3 (Landau) mit 6. Ziffer '1'
    print("\n" + "=" * 100)
    print("PROBLEM: Landau (branch=3) mit 6. Ziffer '1'")
    print("=" * 100)
    
    cursor.execute(convert_placeholders(f"""
        SELECT 
            nominal_account_number,
            COUNT(*) as anzahl,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as summe
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND subsidiary_to_company_ref = 1
          AND branch_number = 3
          AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'
          {guv_filter}
        GROUP BY nominal_account_number
        ORDER BY summe DESC
        LIMIT 20
    """), (datum_von, datum_bis))
    
    print("\nTop 20 Konten (Landau branch=3, aber 6. Ziffer='1'):")
    total2 = 0
    for row in cursor.fetchall():
        r = row_to_dict(row)
        total2 += r['summe']
        print(f"  Konto {r['nominal_account_number']}: {r['anzahl']} Buchungen, {r['summe']:,.2f} €")
    print(f"\n  Gesamt: {total2:,.2f} €")
    print(f"  ⚠️  Diese Kosten werden aktuell NICHT Landau zugeordnet (Filter sucht 6. Ziffer '2')")
    
    print("\n" + "=" * 100)
    print("FAZIT")
    print("=" * 100)
    print(f"\nProblem: Die Filter-Logik verwendet nur die 6. Ziffer, ignoriert aber branch_number!")
    print(f"  - Deggendorf: Filtert nach 6. Ziffer '1', aber es gibt auch branch=1 mit 6. Ziffer '2'")
    print(f"  - Landau: Filtert nach 6. Ziffer '2', aber es gibt auch branch=3 mit 6. Ziffer '1'")
    print(f"\nLösung: Filter sollte branch_number UND 6. Ziffer kombinieren!")

