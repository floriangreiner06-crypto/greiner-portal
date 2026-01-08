"""
Vergleich: Verschiedene Filter-Logiken für Kosten
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

print("=" * 100)
print("VERGLEICH: Verschiedene Filter-Logiken für Kosten")
print("Zeitraum: Dezember 2025")
print("=" * 100)

monat = 12
jahr = 2025
datum_von = f"{jahr}-{monat:02d}-01"
datum_bis = f"{jahr+1}-01-01"

guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"

with db_session() as conn:
    cursor = conn.cursor()
    
    # Global Cube Werte (aus Screenshots)
    gc_deg_kosten = -42.934 - 140.392 - 66.054  # Variable + Direkte + Indirekte
    gc_lan_kosten = -5.706 - 38.724 - 33.758
    
    print("\nGlobal Cube (aus Screenshots):")
    print(f"  Deggendorf Stellantis Kosten: {gc_deg_kosten:,.2f} €")
    print(f"  Landau Kosten: {gc_lan_kosten:,.2f} €")
    
    # Variante 1: Nur 6. Ziffer (ALT)
    print("\n" + "=" * 100)
    print("Variante 1: Nur 6. Ziffer (ALT)")
    print("=" * 100)
    
    # Deggendorf: 6. Ziffer '1'
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND subsidiary_to_company_ref = 1
          AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'
          {guv_filter}
    """), (datum_von, datum_bis))
    deg_alt = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Landau: 6. Ziffer '2'
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND subsidiary_to_company_ref = 1
          AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'
          {guv_filter}
    """), (datum_von, datum_bis))
    lan_alt = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    print(f"  Deggendorf: {deg_alt:,.2f} €")
    print(f"  Landau: {lan_alt:,.2f} €")
    print(f"  Differenz zu GC: Deg={deg_alt - abs(gc_deg_kosten):,.2f} €, Lan={lan_alt - abs(gc_lan_kosten):,.2f} €")
    
    # Variante 2: Nur branch_number (NEU)
    print("\n" + "=" * 100)
    print("Variante 2: Nur branch_number (NEU)")
    print("=" * 100)
    
    # Deggendorf: branch=1
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND subsidiary_to_company_ref = 1
          AND branch_number = 1
          {guv_filter}
    """), (datum_von, datum_bis))
    deg_neu = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Landau: branch=3
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND subsidiary_to_company_ref = 1
          AND branch_number = 3
          {guv_filter}
    """), (datum_von, datum_bis))
    lan_neu = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    print(f"  Deggendorf: {deg_neu:,.2f} €")
    print(f"  Landau: {lan_neu:,.2f} €")
    print(f"  Differenz zu GC: Deg={deg_neu - abs(gc_deg_kosten):,.2f} €, Lan={lan_neu - abs(gc_lan_kosten):,.2f} €")
    
    # Variante 3: branch_number UND 6. Ziffer (kombiniert)
    print("\n" + "=" * 100)
    print("Variante 3: branch_number UND 6. Ziffer kombiniert")
    print("=" * 100)
    
    # Deggendorf: branch=1 UND (6. Ziffer='1' OR 6. Ziffer='2')
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND subsidiary_to_company_ref = 1
          AND branch_number = 1
          AND substr(CAST(nominal_account_number AS TEXT), 6, 1) IN ('1', '2')
          {guv_filter}
    """), (datum_von, datum_bis))
    deg_komb = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Landau: branch=3 UND (6. Ziffer='1' OR 6. Ziffer='2')
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 499999
          AND subsidiary_to_company_ref = 1
          AND branch_number = 3
          AND substr(CAST(nominal_account_number AS TEXT), 6, 1) IN ('1', '2')
          {guv_filter}
    """), (datum_von, datum_bis))
    lan_komb = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    print(f"  Deggendorf: {deg_komb:,.2f} €")
    print(f"  Landau: {lan_komb:,.2f} €")
    print(f"  Differenz zu GC: Deg={deg_komb - abs(gc_deg_kosten):,.2f} €, Lan={lan_komb - abs(gc_lan_kosten):,.2f} €")
    
    print("\n" + "=" * 100)
    print("FAZIT")
    print("=" * 100)
    print("\nWelche Variante passt am besten zu Global Cube?")
    print(f"  Variante 1 (6. Ziffer): Deg={abs(deg_alt - abs(gc_deg_kosten)):,.2f} €, Lan={abs(lan_alt - abs(gc_lan_kosten)):,.2f} €")
    print(f"  Variante 2 (branch): Deg={abs(deg_neu - abs(gc_deg_kosten)):,.2f} €, Lan={abs(lan_neu - abs(gc_lan_kosten)):,.2f} €")
    print(f"  Variante 3 (kombiniert): Deg={abs(deg_komb - abs(gc_deg_kosten)):,.2f} €, Lan={abs(lan_komb - abs(gc_lan_kosten)):,.2f} €")

