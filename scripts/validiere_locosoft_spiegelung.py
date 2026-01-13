#!/usr/bin/env python3
"""
Validiert Locosoft-Spiegelung: Prüft ob alle Daten korrekt von Locosoft PostgreSQL 
nach DRIVE PostgreSQL gespiegelt wurden.

Vergleich:
- Locosoft PostgreSQL: journal_accountings (Original)
- DRIVE PostgreSQL: loco_journal_accountings (Spiegel)
"""
import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session, db_session, row_to_dict
from api.db_connection import convert_placeholders
import psycopg2
import json
import os

def vergleiche_spiegelung():
    """Vergleicht Locosoft PostgreSQL mit DRIVE PostgreSQL"""
    
    print("=" * 80)
    print("LOCOSOFT-SPIEGELUNG VALIDIERUNG")
    print("=" * 80)
    print()
    
    # Zeitraum: Sep-Dez 2025 (YTD)
    datum_von = '2025-09-01'
    datum_bis = '2026-01-01'
    
    print(f"Zeitraum: {datum_von} bis {datum_bis}")
    print()
    
    # Locosoft PostgreSQL (Original)
    print("📊 LOCOSOFT POSTGRESQL (Original)")
    print("-" * 80)
    
    # Direkte Verbindung zu Locosoft (um sicherzustellen, dass es funktioniert)
    credentials_path = '/opt/greiner-portal/config/credentials.json'
    if os.path.exists(credentials_path):
        with open(credentials_path, 'r') as f:
            creds = json.load(f)
            locosoft_creds = creds.get('locosoft_postgresql', {})
    else:
        locosoft_creds = {
            'host': '10.80.80.8',
            'port': 5432,
            'database': 'loco_auswertung_db',
            'user': 'loco_auswertung_benutzer',
            'password': 'loco'
        }
    
    loco_conn = psycopg2.connect(
        host=locosoft_creds.get('host', '10.80.80.8'),
        port=locosoft_creds.get('port', 5432),
        database=locosoft_creds.get('database', 'loco_auswertung_db'),
        user=locosoft_creds.get('user', 'loco_auswertung_benutzer'),
        password=locosoft_creds.get('password', 'loco')
    )
    
    try:
        loco_cursor = loco_conn.cursor()
        
        # Gesamt-Statistik
        loco_cursor.execute(convert_placeholders("""
            SELECT 
                COUNT(*) as anzahl,
                SUM(posted_value) as summe,
                MIN(accounting_date) as min_datum,
                MAX(accounting_date) as max_datum,
                COUNT(DISTINCT nominal_account_number) as anzahl_konten
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
        """), (datum_von, datum_bis))
        
        loco_row = loco_cursor.fetchone()
        if loco_row:
            loco_stat = {
                'anzahl': loco_row[0] if len(loco_row) > 0 else 0,
                'summe': loco_row[1] if len(loco_row) > 1 else 0,
                'min_datum': loco_row[2] if len(loco_row) > 2 else None,
                'max_datum': loco_row[3] if len(loco_row) > 3 else None,
                'anzahl_konten': loco_row[4] if len(loco_row) > 4 else 0
            }
        else:
            loco_stat = {'anzahl': 0, 'summe': 0, 'min_datum': None, 'max_datum': None, 'anzahl_konten': 0}
        
        print(f"Anzahl Buchungen: {loco_stat.get('anzahl', 0):,}")
        print(f"Summe posted_value: {loco_stat.get('summe', 0):,} (in Cent)")
        print(f"Min Datum: {loco_stat.get('min_datum', 'N/A')}")
        print(f"Max Datum: {loco_stat.get('max_datum', 'N/A')}")
        print(f"Anzahl Konten: {loco_stat.get('anzahl_konten', 0)}")
        print()
        
        # Umsatz (8xxxxx)
        loco_cursor.execute(convert_placeholders("""
            SELECT 
                COUNT(*) as anzahl,
                SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END) as summe
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND ((nominal_account_number BETWEEN 800000 AND 889999)
                   OR (nominal_account_number BETWEEN 893200 AND 893299))
        """), (datum_von, datum_bis))
        
        loco_umsatz_row = loco_cursor.fetchone()
        if loco_umsatz_row:
            loco_umsatz = {'anzahl': loco_umsatz_row[0] or 0, 'summe': loco_umsatz_row[1] or 0}
        else:
            loco_umsatz = {'anzahl': 0, 'summe': 0}
        print(f"Umsatz (8xxxxx):")
        print(f"  Anzahl: {loco_umsatz.get('anzahl', 0):,}")
        print(f"  Summe: {(loco_umsatz.get('summe', 0) or 0)/100:,.2f} €")
        print()
        
        # Einsatz (7xxxxx)
        loco_cursor.execute(convert_placeholders("""
            SELECT 
                COUNT(*) as anzahl,
                SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) as summe
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 700000 AND 799999
        """), (datum_von, datum_bis))
        
        loco_einsatz_row = loco_cursor.fetchone()
        if loco_einsatz_row:
            loco_einsatz = {'anzahl': loco_einsatz_row[0] or 0, 'summe': loco_einsatz_row[1] or 0}
        else:
            loco_einsatz = {'anzahl': 0, 'summe': 0}
        print(f"Einsatz (7xxxxx):")
        print(f"  Anzahl: {loco_einsatz.get('anzahl', 0):,}")
        print(f"  Summe: {(loco_einsatz.get('summe', 0) or 0)/100:,.2f} €")
        print()
        
        # Kosten (4xxxxx)
        loco_cursor.execute(convert_placeholders("""
            SELECT 
                COUNT(*) as anzahl,
                SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) as summe
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 400000 AND 499999
        """), (datum_von, datum_bis))
        
        loco_kosten_row = loco_cursor.fetchone()
        if loco_kosten_row:
            loco_kosten = {'anzahl': loco_kosten_row[0] or 0, 'summe': loco_kosten_row[1] or 0}
        else:
            loco_kosten = {'anzahl': 0, 'summe': 0}
        print(f"Kosten (4xxxxx):")
        print(f"  Anzahl: {loco_kosten.get('anzahl', 0):,}")
        print(f"  Summe: {(loco_kosten.get('summe', 0) or 0)/100:,.2f} €")
        print()
        
        # Neutral (2xxxxx)
        loco_cursor.execute(convert_placeholders("""
            SELECT 
                COUNT(*) as anzahl,
                SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END) as summe
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 200000 AND 299999
        """), (datum_von, datum_bis))
        
        loco_neutral_row = loco_cursor.fetchone()
        if loco_neutral_row:
            loco_neutral = {'anzahl': loco_neutral_row[0] or 0, 'summe': loco_neutral_row[1] or 0}
        else:
            loco_neutral = {'anzahl': 0, 'summe': 0}
        print(f"Neutral (2xxxxx):")
        print(f"  Anzahl: {loco_neutral.get('anzahl', 0):,}")
        print(f"  Summe: {(loco_neutral.get('summe', 0) or 0)/100:,.2f} €")
        print()
    finally:
        loco_conn.close()
    
    # DRIVE PostgreSQL (Spiegel)
    print("=" * 80)
    print("📊 DRIVE POSTGRESQL (Spiegel)")
    print("-" * 80)
    
    with db_session() as drive_conn:
        drive_cursor = drive_conn.cursor()
        
        # Gesamt-Statistik
        drive_cursor.execute(convert_placeholders("""
            SELECT 
                COUNT(*) as anzahl,
                SUM(posted_value) as summe,
                MIN(accounting_date) as min_datum,
                MAX(accounting_date) as max_datum,
                COUNT(DISTINCT nominal_account_number) as anzahl_konten
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
        """), (datum_von, datum_bis))
        
        drive_row = drive_cursor.fetchone()
        drive_stat = row_to_dict(drive_row) if drive_row else {}
        
        print(f"Anzahl Buchungen: {drive_stat.get('anzahl', 0):,}")
        print(f"Summe posted_value: {drive_stat.get('summe', 0):,} (in Cent)")
        print(f"Min Datum: {drive_stat.get('min_datum', 'N/A')}")
        print(f"Max Datum: {drive_stat.get('max_datum', 'N/A')}")
        print(f"Anzahl Konten: {drive_stat.get('anzahl_konten', 0)}")
        print()
        
        # Umsatz (8xxxxx)
        drive_cursor.execute(convert_placeholders("""
            SELECT 
                COUNT(*) as anzahl,
                SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END) as summe
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND ((nominal_account_number BETWEEN 800000 AND 889999)
                   OR (nominal_account_number BETWEEN 893200 AND 893299))
        """), (datum_von, datum_bis))
        
        drive_umsatz_row = drive_cursor.fetchone()
        drive_umsatz = row_to_dict(drive_umsatz_row) if drive_umsatz_row else {}
        print(f"Umsatz (8xxxxx):")
        print(f"  Anzahl: {drive_umsatz.get('anzahl', 0):,}")
        print(f"  Summe: {(drive_umsatz.get('summe', 0) or 0)/100:,.2f} €")
        print()
        
        # Einsatz (7xxxxx)
        drive_cursor.execute(convert_placeholders("""
            SELECT 
                COUNT(*) as anzahl,
                SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) as summe
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 700000 AND 799999
        """), (datum_von, datum_bis))
        
        drive_einsatz_row = drive_cursor.fetchone()
        drive_einsatz = row_to_dict(drive_einsatz_row) if drive_einsatz_row else {}
        print(f"Einsatz (7xxxxx):")
        print(f"  Anzahl: {drive_einsatz.get('anzahl', 0):,}")
        print(f"  Summe: {(drive_einsatz.get('summe', 0) or 0)/100:,.2f} €")
        print()
        
        # Kosten (4xxxxx)
        drive_cursor.execute(convert_placeholders("""
            SELECT 
                COUNT(*) as anzahl,
                SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) as summe
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 400000 AND 499999
        """), (datum_von, datum_bis))
        
        drive_kosten_row = drive_cursor.fetchone()
        drive_kosten = row_to_dict(drive_kosten_row) if drive_kosten_row else {}
        print(f"Kosten (4xxxxx):")
        print(f"  Anzahl: {drive_kosten.get('anzahl', 0):,}")
        print(f"  Summe: {(drive_kosten.get('summe', 0) or 0)/100:,.2f} €")
        print()
        
        # Neutral (2xxxxx)
        drive_cursor.execute(convert_placeholders("""
            SELECT 
                COUNT(*) as anzahl,
                SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END) as summe
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 200000 AND 299999
        """), (datum_von, datum_bis))
        
        drive_neutral_row = drive_cursor.fetchone()
        drive_neutral = row_to_dict(drive_neutral_row) if drive_neutral_row else {}
        print(f"Neutral (2xxxxx):")
        print(f"  Anzahl: {drive_neutral.get('anzahl', 0):,}")
        print(f"  Summe: {(drive_neutral.get('summe', 0) or 0)/100:,.2f} €")
        print()
    
    # Vergleich
    print("=" * 80)
    print("📊 VERGLEICH")
    print("-" * 80)
    print()
    
    # Gesamt
    diff_anzahl = drive_stat.get('anzahl', 0) - loco_stat.get('anzahl', 0)
    diff_summe = (drive_stat.get('summe', 0) or 0) - (loco_stat.get('summe', 0) or 0)
    diff_konten = drive_stat.get('anzahl_konten', 0) - loco_stat.get('anzahl_konten', 0)
    
    print(f"Gesamt:")
    print(f"  Anzahl Buchungen: {diff_anzahl:+,} ({'✅' if diff_anzahl == 0 else '❌'})")
    print(f"  Summe posted_value: {diff_summe:+,} Cent ({'✅' if diff_summe == 0 else '❌'})")
    print(f"  Anzahl Konten: {diff_konten:+,} ({'✅' if diff_konten == 0 else '❌'})")
    print()
    
    # Umsatz
    diff_umsatz_anzahl = drive_umsatz.get('anzahl', 0) - loco_umsatz.get('anzahl', 0)
    diff_umsatz_summe = (drive_umsatz.get('summe', 0) or 0) - (loco_umsatz.get('summe', 0) or 0)
    
    print(f"Umsatz (8xxxxx):")
    print(f"  Anzahl: {diff_umsatz_anzahl:+,} ({'✅' if diff_umsatz_anzahl == 0 else '❌'})")
    print(f"  Summe: {diff_umsatz_summe/100:+,.2f} € ({'✅' if abs(diff_umsatz_summe) < 1 else '❌'})")
    print()
    
    # Einsatz
    diff_einsatz_anzahl = drive_einsatz.get('anzahl', 0) - loco_einsatz.get('anzahl', 0)
    diff_einsatz_summe = (drive_einsatz.get('summe', 0) or 0) - (loco_einsatz.get('summe', 0) or 0)
    
    print(f"Einsatz (7xxxxx):")
    print(f"  Anzahl: {diff_einsatz_anzahl:+,} ({'✅' if diff_einsatz_anzahl == 0 else '❌'})")
    print(f"  Summe: {diff_einsatz_summe/100:+,.2f} € ({'✅' if abs(diff_einsatz_summe) < 1 else '❌'})")
    print()
    
    # Kosten
    diff_kosten_anzahl = drive_kosten.get('anzahl', 0) - loco_kosten.get('anzahl', 0)
    diff_kosten_summe = (drive_kosten.get('summe', 0) or 0) - (loco_kosten.get('summe', 0) or 0)
    
    print(f"Kosten (4xxxxx):")
    print(f"  Anzahl: {diff_kosten_anzahl:+,} ({'✅' if diff_kosten_anzahl == 0 else '❌'})")
    print(f"  Summe: {diff_kosten_summe/100:+,.2f} € ({'✅' if abs(diff_kosten_summe) < 1 else '❌'})")
    print()
    
    # Neutral
    diff_neutral_anzahl = drive_neutral.get('anzahl', 0) - loco_neutral.get('anzahl', 0)
    diff_neutral_summe = (drive_neutral.get('summe', 0) or 0) - (loco_neutral.get('summe', 0) or 0)
    
    print(f"Neutral (2xxxxx):")
    print(f"  Anzahl: {diff_neutral_anzahl:+,} ({'✅' if diff_neutral_anzahl == 0 else '❌'})")
    print(f"  Summe: {diff_neutral_summe/100:+,.2f} € ({'✅' if abs(diff_neutral_summe) < 1 else '❌'})")
    print()
    
    # Fazit
    print("=" * 80)
    print("📋 FAZIT")
    print("=" * 80)
    print()
    
    if diff_anzahl == 0 and abs(diff_summe) < 1:
        print("✅ Locosoft-Spiegelung ist KORREKT!")
        print("   → Problem liegt in der Filter-Logik, nicht in der Daten-Spiegelung")
    else:
        print("❌ Locosoft-Spiegelung ist FEHLERHAFT!")
        print("   → Daten fehlen oder sind falsch gespiegelt")
        print("   → Sync-Script muss überprüft werden")

if __name__ == '__main__':
    vergleiche_spiegelung()
