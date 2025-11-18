#!/usr/bin/env python3
"""
Oktober/November 2025 Import mit neuer IBAN-Factory
====================================================

Importiert PDFs aus Oktober und November 2025.
Nutzt die neue IBANParserFactory (Tag 60).

Usage:
    python3 import_oktober_november_2025.py

Autor: Claude (Tag 60)
Datum: 2025-11-18
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

import sqlite3
from pathlib import Path
from datetime import datetime

from parsers.iban_parser_factory import IBANParserFactory

DB = Path("/opt/greiner-portal/data/greiner_controlling.db")
PDF_DIR = Path("/mnt/buchhaltung/Buchhaltung/Kontoauszüge")

def print_separator(title=""):
    if title:
        print(f"\n{'='*90}")
        print(f"  {title}")
        print(f"{'='*90}")
    else:
        print(f"{'='*90}")

def import_pdf(pdf_path: Path) -> int:
    """
    Importiert ein PDF mit neuer IBAN-Factory.
    
    Returns:
        Anzahl importierter Transaktionen
    """
    try:
        # Nutze neue Factory
        parser = IBANParserFactory.get_parser(str(pdf_path))
        
        if not parser:
            print(f"  ⊘ {pdf_path.name}: Kein Parser gefunden")
            return 0
        
        # Parse PDF
        transactions = parser.parse()
        
        if not transactions:
            # Prüfe ob Mitteilung
            if hasattr(parser, 'endsaldo') and parser.endsaldo is not None:
                print(f"  ⊘ {pdf_path.name}: 0 TX (Mitteilung, Endsaldo: {parser.endsaldo:.2f} EUR)")
            else:
                print(f"  ⊘ {pdf_path.name}: 0 TX")
            return 0
        
        # IBAN → Konto-ID
        if not parser.iban:
            print(f"  ❌ {pdf_path.name}: Keine IBAN extrahiert")
            return 0
        
        conn = sqlite3.connect(str(DB))
        cursor = conn.cursor()
        
        # Finde Konto-ID
        cursor.execute("SELECT id FROM konten WHERE iban = ?", (parser.iban,))
        row = cursor.fetchone()
        
        if not row:
            print(f"  ⊘ {pdf_path.name}: IBAN {parser.iban} nicht in DB")
            conn.close()
            return 0
        
        konto_id = row[0]
        imported = 0
        duplicates = 0
        
        for tx in transactions:
            # Duplikat-Check
            cursor.execute("""
                SELECT COUNT(*) FROM transaktionen
                WHERE konto_id = ? AND buchungsdatum = ? AND betrag = ?
            """, (konto_id, tx.buchungsdatum, tx.betrag))
            
            if cursor.fetchone()[0] > 0:
                duplicates += 1
                continue
            
            # Insert
            cursor.execute("""
                INSERT INTO transaktionen (
                    konto_id, buchungsdatum, valutadatum,
                    verwendungszweck, betrag, waehrung, importiert_am
                )
                VALUES (?, ?, ?, ?, ?, 'EUR', ?)
            """, (
                konto_id,
                tx.buchungsdatum,
                tx.valutadatum,
                tx.verwendungszweck[:500],
                tx.betrag,
                datetime.now()
            ))
            imported += 1
        
        conn.commit()
        conn.close()
        
        # Ausgabe
        if imported > 0:
            print(f"  ✅ {pdf_path.name}: {imported} TX importiert, {duplicates} Duplikate")
        elif duplicates > 0:
            print(f"  ⊘ {pdf_path.name}: {duplicates} Duplikate (bereits importiert)")
        
        return imported
        
    except Exception as e:
        print(f"  ❌ {pdf_path.name}: {e}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    print_separator("📥 OKTOBER/NOVEMBER 2025 IMPORT")
    print(f"Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"PDF-Verzeichnis: {PDF_DIR}")
    
    # Statistiken
    stats = {
        'pdfs_gesamt': 0,
        'pdfs_verarbeitet': 0,
        'pdfs_fehler': 0,
        'transaktionen_importiert': 0,
        'banken': {}
    }
    
    # Durchsuche alle Bank-Verzeichnisse
    for bank_dir in sorted(PDF_DIR.iterdir()):
        if not bank_dir.is_dir():
            continue
        
        # Suche Oktober/November PDFs
        oktober_pdfs = list(bank_dir.glob("*10.25*.pdf")) + list(bank_dir.glob("*10-25*.pdf"))
        november_pdfs = list(bank_dir.glob("*11.25*.pdf")) + list(bank_dir.glob("*11-25*.pdf"))
        
        # Auch spezielle Formate (Genobank etc.)
        for pdf in bank_dir.glob("*.pdf"):
            name_lower = pdf.name.lower()
            # 2025.10 oder 2025.11 oder 2025-10 oder 2025-11
            if any(x in name_lower for x in ['2025.10', '2025-10', '2025_10']):
                if pdf not in oktober_pdfs:
                    oktober_pdfs.append(pdf)
            if any(x in name_lower for x in ['2025.11', '2025-11', '2025_11']):
                if pdf not in november_pdfs:
                    november_pdfs.append(pdf)
        
        monat_pdfs = oktober_pdfs + november_pdfs
        
        if not monat_pdfs:
            continue
        
        print(f"\n📁 {bank_dir.name} ({len(monat_pdfs)} PDFs)")
        print("-" * 90)
        
        stats['banken'][bank_dir.name] = 0
        
        for pdf in sorted(monat_pdfs):
            stats['pdfs_gesamt'] += 1
            imported = import_pdf(pdf)
            
            if imported >= 0:
                stats['pdfs_verarbeitet'] += 1
                stats['transaktionen_importiert'] += imported
                stats['banken'][bank_dir.name] += imported
            else:
                stats['pdfs_fehler'] += 1
    
    # ZUSAMMENFASSUNG
    print_separator("📊 IMPORT-ZUSAMMENFASSUNG")
    print(f"PDFs gefunden:           {stats['pdfs_gesamt']}")
    print(f"PDFs verarbeitet:        {stats['pdfs_verarbeitet']}")
    print(f"PDFs mit Fehler:         {stats['pdfs_fehler']}")
    print(f"Transaktionen importiert: {stats['transaktionen_importiert']}")
    
    print(f"\n📋 Pro Bank:")
    print("-" * 90)
    for bank, count in sorted(stats['banken'].items()):
        if count > 0:
            print(f"  {bank:40s}: {count:5d} Transaktionen")
    
    print_separator()
    
    if stats['transaktionen_importiert'] > 0:
        print(f"✅ IMPORT ERFOLGREICH: {stats['transaktionen_importiert']} Transaktionen importiert")
    else:
        print(f"⊘ Keine neuen Transaktionen (alles bereits importiert)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Import abgebrochen")
    except Exception as e:
        print(f"\n\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
