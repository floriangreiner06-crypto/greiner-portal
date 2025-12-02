#!/usr/bin/env python3
"""
HypoVereinsbank PDF Import für Bankenspiegel V2
Version: 2.2 (Korrektes Schema)
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Parser importieren
sys.path.insert(0, '/opt/greiner-portal/parsers')
from hypovereinsbank_parser_v2 import HypoVereinsbankParser


def get_db_connection(db_path='/opt/greiner-portal/data/greiner_controlling.db'):
    """Datenbankverbindung herstellen"""
    return sqlite3.connect(db_path)


def get_konto_id_by_iban(conn, iban):
    """Konto-ID anhand IBAN ermitteln"""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM konten WHERE iban = ?", (iban,))
    result = cursor.fetchone()
    return result[0] if result else None


def transaction_exists(conn, konto_id, buchungsdatum, betrag, verwendungszweck):
    """Prüfen ob Transaktion bereits existiert"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM transaktionen 
        WHERE konto_id = ? 
        AND buchungsdatum = ? 
        AND ABS(betrag - ?) < 0.01
        AND verwendungszweck = ?
    """, (konto_id, buchungsdatum, betrag, verwendungszweck))
    return cursor.fetchone()[0] > 0


def saldo_exists(conn, konto_id, datum):
    """Prüfen ob Saldo für Datum bereits existiert"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM salden WHERE konto_id = ? AND datum = ?",
        (konto_id, datum)
    )
    return cursor.fetchone()[0] > 0


def import_pdf(pdf_path, db_path='/opt/greiner-portal/data/greiner_controlling.db', dry_run=False):
    """PDF importieren"""
    print("=" * 80)
    print(f"IMPORT: {os.path.basename(pdf_path)}")
    print("=" * 80)
    
    # PDF parsen
    parser = HypoVereinsbankParser(pdf_path)
    result = parser.parse()
    
    print(f"\n📄 PDF-PARSING:")
    print(f"   IBAN: {result['iban']}")
    print(f"   Kontonummer: {result['kontonummer']}")
    print(f"   Saldo-Datum: {result['saldo_datum']}")
    print(f"   Endsaldo: {result['endsaldo']:,.2f} EUR")
    print(f"   Transaktionen: {len(result['transactions'])}")
    
    if dry_run:
        print("\n🔍 DRY-RUN MODE - Keine DB-Änderungen")
        return
    
    # Datenbank-Import
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    try:
        # Konto-ID ermitteln
        konto_id = get_konto_id_by_iban(conn, result['iban'])
        
        if not konto_id:
            print(f"\n❌ FEHLER: Konto mit IBAN {result['iban']} nicht in Datenbank gefunden!")
            return
        
        print(f"\n✅ Konto-ID: {konto_id}")
        
        # Transaktionen importieren
        tx_imported = 0
        tx_skipped = 0
        
        dateiname = os.path.basename(pdf_path)
        
        for tx in result['transactions']:
            # Duplikat-Check
            if transaction_exists(conn, konto_id, tx['buchungsdatum'], 
                                tx['betrag'], tx['verwendungszweck']):
                tx_skipped += 1
                continue
            
            # Transaktion einfügen (NUR existierende Spalten!)
            cursor.execute("""
                INSERT INTO transaktionen (
                    konto_id,
                    buchungsdatum,
                    valutadatum,
                    betrag,
                    verwendungszweck,
                    import_quelle,
                    import_datei
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                konto_id,
                tx['buchungsdatum'],
                tx['valutadatum'],
                tx['betrag'],
                tx['verwendungszweck'],
                'MT940',
                dateiname
            ))
            
            tx_imported += 1
        
        print(f"\n💾 TRANSAKTIONEN:")
        print(f"   Importiert: {tx_imported}")
        print(f"   Übersprungen (Duplikate): {tx_skipped}")
        
        # Saldo importieren
        if result['endsaldo'] is not None and result['saldo_datum']:
            if not saldo_exists(conn, konto_id, result['saldo_datum']):
                cursor.execute("""
                    INSERT INTO salden (
                        konto_id,
                        datum,
                        saldo,
                        quelle,
                        import_datei
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    konto_id,
                    result['saldo_datum'],
                    result['endsaldo'],
                    'MT940',
                    dateiname
                ))
                print(f"\n💰 SALDO:")
                print(f"   {result['saldo_datum']}: {result['endsaldo']:,.2f} EUR importiert")
            else:
                print(f"\n⏭️  SALDO:")
                print(f"   {result['saldo_datum']}: Bereits vorhanden (übersprungen)")
        
        # Commit
        conn.commit()
        print("\n✅ IMPORT ERFOLGREICH!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()


def import_directory(directory, db_path='/opt/greiner-portal/data/greiner_controlling.db', dry_run=False):
    """Alle PDFs aus einem Verzeichnis importieren"""
    pdf_files = list(Path(directory).glob('*.pdf'))
    
    if not pdf_files:
        print(f"Keine PDF-Dateien in {directory} gefunden.")
        return
    
    print(f"\n🔍 Gefundene PDFs: {len(pdf_files)}")
    print("=" * 80)
    
    for pdf_file in sorted(pdf_files):
        import_pdf(str(pdf_file), db_path, dry_run)
        print()
    
    print("=" * 80)
    print("✅ ALLE IMPORTS ABGESCHLOSSEN")
    print("=" * 80)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='HypoVereinsbank PDF Import')
    parser.add_argument('path', help='PDF-Datei oder Verzeichnis')
    parser.add_argument('--db', default='/opt/greiner-portal/data/greiner_controlling.db',
                        help='Pfad zur Datenbank')
    parser.add_argument('--dry-run', action='store_true',
                        help='Nur Parsing, keine DB-Änderungen')
    
    args = parser.parse_args()
    
    if os.path.isfile(args.path):
        import_pdf(args.path, args.db, args.dry_run)
    elif os.path.isdir(args.path):
        import_directory(args.path, args.db, args.dry_run)
    else:
        print(f"❌ FEHLER: {args.path} ist weder Datei noch Verzeichnis!")
        sys.exit(1)
