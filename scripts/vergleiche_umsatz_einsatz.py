"""
Vergleich: Umsatz und Einsatz für Deggendorf Stellantis und Landau
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import db_session, row_to_dict
from api.controlling_api import build_firma_standort_filter
from api.db_connection import convert_placeholders

print("=" * 100)
print("VERGLEICH: Umsatz und Einsatz - Deggendorf Stellantis vs. Landau")
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
    print("\nGlobal Cube (aus Screenshots):")
    print("  Deggendorf Stellantis:")
    print("    Umsatz: 1.156.863 €")
    print("    Einsatz: -983.377 € (aus Screenshot: 983.377 €)")
    print("    DB1: 173.486 €")
    print("    BE: -88.633 €")
    print("  Landau:")
    print("    Umsatz: 320.121 €")
    print("    Einsatz: -285.532 € (aus Screenshot: 285.532 €)")
    print("    DB1: 34.588 €")
    print("    BE: -30.861 €")
    
    # Deggendorf Stellantis
    print("\n" + "=" * 100)
    print("DEGGENDORF STELLANTIS (DRIVE)")
    print("=" * 100)
    
    firma_filter_umsatz, firma_filter_einsatz, _, _ = build_firma_standort_filter('1', '1')
    
    # Umsatz
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND ((nominal_account_number BETWEEN 800000 AND 889999)
               OR (nominal_account_number BETWEEN 893200 AND 893299))
          {firma_filter_umsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    umsatz_deg = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Einsatz
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          {firma_filter_einsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    einsatz_deg = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    db1_deg = umsatz_deg + einsatz_deg
    
    print(f"  Umsatz: {umsatz_deg:,.2f} €")
    print(f"  Einsatz: {einsatz_deg:,.2f} €")
    print(f"  DB1: {db1_deg:,.2f} €")
    print(f"  Vergleich GC: Umsatz diff={umsatz_deg - 1156863:,.2f} €, Einsatz diff={einsatz_deg - 983377:,.2f} €")
    
    # Landau
    print("\n" + "=" * 100)
    print("LANDAU (DRIVE)")
    print("=" * 100)
    
    firma_filter_umsatz, firma_filter_einsatz, _, _ = build_firma_standort_filter('1', '2')
    
    # Umsatz
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND ((nominal_account_number BETWEEN 800000 AND 889999)
               OR (nominal_account_number BETWEEN 893200 AND 893299))
          {firma_filter_umsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    umsatz_lan = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    # Einsatz
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 700000 AND 799999
          {firma_filter_einsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    einsatz_lan = float(row_to_dict(cursor.fetchone())['wert'] or 0)
    
    db1_lan = umsatz_lan + einsatz_lan
    
    print(f"  Umsatz: {umsatz_lan:,.2f} €")
    print(f"  Einsatz: {einsatz_lan:,.2f} €")
    print(f"  DB1: {db1_lan:,.2f} €")
    print(f"  Vergleich GC: Umsatz diff={umsatz_lan - 320121:,.2f} €, Einsatz diff={einsatz_lan - 285532:,.2f} €")

