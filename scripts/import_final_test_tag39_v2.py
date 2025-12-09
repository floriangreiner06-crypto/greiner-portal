#!/usr/bin/env python3
"""
Finaler Import-Test TAG 39 v2
==============================
Importiert mit KORREKTEM Schema:
1. VR Bank Landau - Alle 2025 PDFs
2. 3700057908 Festgeld - Alle PDFs
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/opt/greiner-portal')
from parsers.parser_factory import ParserFactory

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'

def backup_db():
    """Backup erstellen"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{DB_PATH}.backup_{timestamp}"
    import shutil
    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ Backup: {backup_path}")
    return backup_path

def import_pdf(pdf_path, konto_id, conn):
    """PDF importieren"""
    pdf_path = Path(pdf_path)
    
    # Parser mit IBAN-Detection
    parser = ParserFactory.create_parser(str(pdf_path))
    transactions = parser.parse()
    
    if not transactions:
        return 0, 0
    
    cursor = conn.cursor()
    imported = 0
    skipped = 0
    
    for trans in transactions:
        # Duplikat-Check: buchungsdatum + betrag + verwendungszweck
        cursor.execute("""
            SELECT id FROM transaktionen
            WHERE konto_id = ? 
            AND buchungsdatum = ?
            AND betrag = ?
            AND verwendungszweck = ?
        """, (konto_id, trans.datum, trans.betrag, trans.verwendungszweck))
        
        if cursor.fetchone():
            skipped += 1
            continue
        
        # Insert mit korrekten Spaltennamen
        cursor.execute("""
            INSERT INTO transaktionen (
                konto_id, buchungsdatum, betrag, verwendungszweck,
                gegenkonto, buchungstext, pdf_quelle
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            konto_id,
            trans.datum,  # → buchungsdatum
            trans.betrag,
            trans.verwendungszweck,
            trans.iban or trans.empfaenger_auftraggeber,  # → gegenkonto
            trans.buchungstext,
            str(pdf_path.name)
        ))
        imported += 1
    
    conn.commit()
    return imported, skipped

def main():
    print("=" * 70)
    print("FINALER IMPORT-TEST TAG 39 v2 (Korrektes Schema)")
    print("=" * 70)
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    backup_db()
    print()
    
    conn = sqlite3.connect(DB_PATH)
    
    total_imported = 0
    total_skipped = 0
    total_files = 0
    
    # === 1. VR BANK LANDAU ===
    print("=" * 70)
    print("1. VR BANK LANDAU")
    print("=" * 70)
    
    vrbank_dir = Path('/mnt/buchhaltung/Buchhaltung/Kontoauszüge/VR Bank Landau')
    konto_id = 14
    
    pdfs = sorted([p for p in vrbank_dir.glob('*.pdf') if '2025' in p.name or '.25.pdf' in p.name])
    print(f"Gefunden: {len(pdfs)} PDFs\n")
    
    for pdf in pdfs:
        print(f"📄 {pdf.name[:50]}...", end=' ')
        try:
            imported, skipped = import_pdf(pdf, konto_id, conn)
            
            if imported == 0 and skipped == 0:
                print("⏭️  LEER")
            elif imported == 0:
                print(f"⏭️  {skipped} Duplikate")
            else:
                print(f"✅ {imported} neu, {skipped} dup")
                total_imported += imported
                total_skipped += skipped
            
            total_files += 1
        except Exception as e:
            print(f"❌ {str(e)[:40]}")
    
    print()
    
    # === 2. 3700057908 FESTGELD ===
    print("=" * 70)
    print("2. 3700057908 FESTGELD")
    print("=" * 70)
    
    festgeld_dir = Path('/mnt/buchhaltung/Buchhaltung/Kontoauszüge/Genobank Darlehenskonten')
    festgeld_konto_id = 23
    
    festgeld_pdfs = sorted(festgeld_dir.glob('3700057908*.pdf'))
    print(f"Gefunden: {len(festgeld_pdfs)} PDFs\n")
    
    for pdf in festgeld_pdfs:
        print(f"📄 {pdf.name[:50]}...", end=' ')
        try:
            imported, skipped = import_pdf(pdf, festgeld_konto_id, conn)
            
            if imported == 0 and skipped == 0:
                print("⏭️  LEER")
            elif imported == 0:
                print(f"⏭️  {skipped} Duplikate")
            else:
                print(f"✅ {imported} neu, {skipped} dup")
                total_imported += imported
                total_skipped += skipped
            
            total_files += 1
        except Exception as e:
            print(f"❌ {str(e)[:40]}")
    
    conn.close()
    
    # ZUSAMMENFASSUNG
    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    print(f"📁 PDFs verarbeitet:      {total_files}")
    print(f"✅ Neue Transaktionen:    {total_imported}")
    print(f"⏭️  Duplikate (geskippt): {total_skipped}")
    print("=" * 70)
    
    # Konto-Status
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n📊 KONTO-STATUS:")
    cursor.execute("""
        SELECT k.kontoname, COUNT(t.id) as anzahl,
               MAX(t.buchungsdatum) as letztes
        FROM konten k
        LEFT JOIN transaktionen t ON k.id = t.konto_id
        WHERE k.id IN (14, 23)
        GROUP BY k.id, k.kontoname
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} Transaktionen, letzte: {row[2]}")
    
    conn.close()
    print("\n✅ Import abgeschlossen!\n")

if __name__ == '__main__':
    main()
