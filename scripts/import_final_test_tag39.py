#!/usr/bin/env python3
"""
Finaler Import-Test TAG 39
==========================
Importiert:
1. VR Bank Landau - Alle 2025 PDFs (Duplikate werden geskippt)
2. 3700057908 Festgeld - Alle PDFs

Features:
- IBAN-basierte Parser-Detection
- Duplikaterkennung via Hash
- Automatisches Backup
- Detailliertes Reporting
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime
import hashlib

# Projektpfad zum PYTHONPATH hinzufügen
sys.path.insert(0, '/opt/greiner-portal')

from parsers.parser_factory import ParserFactory

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'

def backup_db():
    """Erstellt Backup der Datenbank"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{DB_PATH}.backup_{timestamp}"
    
    import shutil
    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ Backup erstellt: {backup_path}")
    return backup_path

def get_pdf_hash(pdf_path):
    """Berechnet SHA256 Hash einer PDF"""
    sha256 = hashlib.sha256()
    with open(pdf_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def is_duplicate(conn, pdf_hash, konto_id):
    """Prüft ob PDF bereits importiert wurde"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM transaktionen 
        WHERE pdf_hash = ? AND konto_id = ?
    """, (pdf_hash, konto_id))
    count = cursor.fetchone()[0]
    return count > 0

def import_pdf(pdf_path, konto_id, conn):
    """Importiert eine PDF-Datei"""
    pdf_path = Path(pdf_path)
    
    # Hash berechnen
    pdf_hash = get_pdf_hash(pdf_path)
    
    # Duplikat-Check
    if is_duplicate(conn, pdf_hash, konto_id):
        return 0, 0  # Skip, already imported
    
    # Parser erstellen (mit IBAN-Detection!)
    parser = ParserFactory.create_parser(str(pdf_path))
    
    # Parsen
    transactions = parser.parse()
    
    if not transactions:
        return 0, 0
    
    # Transaktionen einfügen
    cursor = conn.cursor()
    imported = 0
    skipped = 0
    
    for trans in transactions:
        # Prüfe ob Transaktion schon existiert (Datum + Betrag + Verwendungszweck)
        cursor.execute("""
            SELECT id FROM transaktionen
            WHERE konto_id = ? 
            AND datum = ?
            AND betrag = ?
            AND verwendungszweck = ?
        """, (konto_id, trans.datum, trans.betrag, trans.verwendungszweck))
        
        if cursor.fetchone():
            skipped += 1
            continue
        
        # Einfügen
        cursor.execute("""
            INSERT INTO transaktionen (
                konto_id, datum, betrag, verwendungszweck,
                empfaenger_auftraggeber, iban, kategorie_id,
                buchungstext, pdf_quelle, pdf_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            konto_id,
            trans.datum,
            trans.betrag,
            trans.verwendungszweck,
            trans.empfaenger_auftraggeber,
            trans.iban,
            None,  # kategorie_id
            trans.buchungstext,
            str(pdf_path.name),
            pdf_hash
        ))
        imported += 1
    
    conn.commit()
    return imported, skipped

def main():
    print("=" * 70)
    print("FINALER IMPORT-TEST TAG 39")
    print("=" * 70)
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Backup
    backup_db()
    print()
    
    # Datenbankverbindung
    conn = sqlite3.connect(DB_PATH)
    
    # Statistik
    total_imported = 0
    total_skipped = 0
    total_files = 0
    
    # === 1. VR BANK LANDAU ===
    print("=" * 70)
    print("1. VR BANK LANDAU - Import aller 2025 PDFs")
    print("=" * 70)
    
    vrbank_landau_dir = Path('/mnt/buchhaltung/Buchhaltung/Kontoauszüge/VR Bank Landau')
    vrbank_landau_konto_id = 14
    
    # Alle 2025 PDFs finden
    pdfs_2025 = sorted([
        p for p in vrbank_landau_dir.glob('*.pdf')
        if '2025' in p.name or '.25.pdf' in p.name
    ])
    
    print(f"Gefunden: {len(pdfs_2025)} PDFs von 2025\n")
    
    for pdf_path in pdfs_2025:
        print(f"📄 {pdf_path.name}...", end=' ')
        try:
            imported, skipped = import_pdf(pdf_path, vrbank_landau_konto_id, conn)
            
            if imported == 0 and skipped == 0:
                print("⏭️  SKIP (Duplikat-PDF)")
            else:
                print(f"✅ {imported} neu, {skipped} duplikat")
                total_imported += imported
                total_skipped += skipped
            
            total_files += 1
            
        except Exception as e:
            print(f"❌ FEHLER: {e}")
    
    print()
    
    # === 2. 3700057908 FESTGELD ===
    print("=" * 70)
    print("2. 3700057908 FESTGELD - Import aller PDFs")
    print("=" * 70)
    
    festgeld_dir = Path('/mnt/buchhaltung/Buchhaltung/Kontoauszüge/Genobank Darlehenskonten')
    festgeld_konto_id = 23
    
    # Alle 3700057908 PDFs finden
    festgeld_pdfs = sorted([
        p for p in festgeld_dir.glob('3700057908*.pdf')
    ])
    
    print(f"Gefunden: {len(festgeld_pdfs)} PDFs\n")
    
    for pdf_path in festgeld_pdfs:
        print(f"📄 {pdf_path.name[:60]}...", end=' ')
        try:
            imported, skipped = import_pdf(pdf_path, festgeld_konto_id, conn)
            
            if imported == 0 and skipped == 0:
                print("⏭️  SKIP (Duplikat-PDF)")
            else:
                print(f"✅ {imported} neu, {skipped} duplikat")
                total_imported += imported
                total_skipped += skipped
            
            total_files += 1
            
        except Exception as e:
            print(f"❌ FEHLER: {e}")
    
    # Abschluss
    conn.close()
    
    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    print(f"📁 Verarbeitete PDFs:     {total_files}")
    print(f"✅ Neue Transaktionen:    {total_imported}")
    print(f"⏭️  Duplikate (geskippt): {total_skipped}")
    print(f"⏱️  Ende: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Status-Check
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\nKONTO-STATUS:")
    cursor.execute("""
        SELECT k.kontoname, COUNT(t.id) as anzahl,
               MAX(t.datum) as letztes_datum
        FROM konten k
        LEFT JOIN transaktionen t ON k.id = t.konto_id
        WHERE k.id IN (14, 23)
        GROUP BY k.id, k.kontoname
    """)
    
    for kontoname, anzahl, letztes_datum in cursor.fetchall():
        print(f"  {kontoname}: {anzahl} Transaktionen, letzte: {letztes_datum}")
    
    conn.close()
    print("\n✅ Import abgeschlossen!")

if __name__ == '__main__':
    main()
