#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sparkasse Online-Banking Export Parser
======================================
Spezieller Parser für "Umsätze - Druckansicht" PDFs

Format:
  Name
  Details...
  DD.MM.YYYYDD.MM.YYYY ±BETRAG EUR
"""

import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

DB_PATH = Path("/opt/greiner-portal/data/greiner_controlling.db")

def parse_sparkasse_online_pdf(pdf_path: Path):
    """Parst Sparkasse Online-Banking PDF"""
    import pdfplumber
    
    transactions = []
    
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            lines = text.split('\n')
            
            # Suche nach Transaktionen
            # Pattern: DD.MM.YYYYDD.MM.YYYY ±BETRAG EUR
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Suche nach Datums-Betrag-Zeile
                # Format: 06.11.202506.11.2025 -500,00 EUR
                match = re.search(
                    r'(\d{2}\.\d{2}\.\d{4})(\d{2}\.\d{2}\.\d{4})\s+([-+]?[\d.,]+)\s*EUR',
                    line
                )
                
                if match:
                    buchungsdatum_str = match.group(1)
                    wertstellung_str = match.group(2)
                    betrag_str = match.group(3)
                    
                    # Parse Datum
                    try:
                        buchungsdatum = datetime.strptime(buchungsdatum_str, '%d.%m.%Y').date()
                        valutadatum = datetime.strptime(wertstellung_str, '%d.%m.%Y').date()
                    except:
                        i += 1
                        continue
                    
                    # Parse Betrag
                    betrag_str = betrag_str.replace('.', '').replace(',', '.')
                    betrag = float(betrag_str)
                    
                    # Sammle Verwendungszweck (vorherige Zeilen)
                    verwendungszweck_lines = []
                    
                    # Gehe 1-5 Zeilen zurück und sammle Text
                    for j in range(max(0, i-5), i):
                        prev_line = lines[j].strip()
                        
                        # Skip Header-Zeilen
                        if any(skip in prev_line for skip in ['Umsätze', 'Kontostand', 'BUCHUNG', 'Sichteinlagen', 'Sparkasse']):
                            continue
                        
                        # Skip Leerzeilen
                        if not prev_line:
                            continue
                        
                        # Skip Zeilen mit nur Datum/Betrag
                        if re.match(r'^\d{2}\.\d{2}\.\d{4}', prev_line):
                            continue
                        
                        verwendungszweck_lines.append(prev_line)
                    
                    # Verwendungszweck zusammensetzen
                    verwendungszweck = ' '.join(verwendungszweck_lines[-3:])  # Max 3 Zeilen
                    
                    if verwendungszweck:
                        transactions.append({
                            'buchungsdatum': buchungsdatum,
                            'valutadatum': valutadatum,
                            'verwendungszweck': verwendungszweck[:500],
                            'betrag': betrag,
                            'pdf_quelle': pdf_path.name
                        })
                        
                        logger.info(f"  ✓ {buchungsdatum} | {betrag:>10.2f} EUR | {verwendungszweck[:50]}...")
                
                i += 1
    
    return transactions

def import_to_db(transactions, konto_id, dry_run=False):
    """Importiert Transaktionen in DB"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    imported = 0
    duplicates = 0
    
    for trans in transactions:
        # Duplikat-Check
        cursor.execute("""
            SELECT COUNT(*) FROM transaktionen
            WHERE konto_id = ? AND buchungsdatum = ? AND betrag = ?
        """, (konto_id, trans['buchungsdatum'], trans['betrag']))
        
        if cursor.fetchone()[0] > 0:
            duplicates += 1
            logger.debug(f"  ⊘ Duplikat: {trans['buchungsdatum']} | {trans['betrag']:.2f} EUR")
            continue
        
        if not dry_run:
            cursor.execute("""
                INSERT INTO transaktionen (
                    konto_id, buchungsdatum, valutadatum,
                    verwendungszweck, betrag, waehrung,
                    pdf_quelle, importiert_am
                ) VALUES (?, ?, ?, ?, ?, 'EUR', ?, ?)
            """, (
                konto_id,
                trans['buchungsdatum'],
                trans['valutadatum'],
                trans['verwendungszweck'],
                trans['betrag'],
                trans['pdf_quelle'],
                datetime.now()
            ))
        
        imported += 1
    
    if not dry_run:
        conn.commit()
    
    conn.close()
    
    return {'imported': imported, 'duplicates': duplicates}

def main():
    dry_run = '--dry-run' in sys.argv
    
    print("="*70)
    print("🚀 SPARKASSE ONLINE-BANKING IMPORT")
    print("="*70)
    if dry_run:
        print("⚠️  DRY-RUN MODUS\n")
    
    # Sparkasse-Konto-ID
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM konten 
        WHERE iban LIKE '%76003647%' OR kontoname LIKE '%Sparkasse%'
        LIMIT 1
    """)
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        print("❌ Sparkasse-Konto nicht gefunden!")
        return
    
    konto_id = result[0]
    print(f"✅ Konto-ID: {konto_id}\n")
    
    # PDFs finden
    pdf_dir = Path("/mnt/buchhaltung/Buchhaltung/Kontoauszüge/Sparkasse/")
    pdf_files = sorted(pdf_dir.glob("*Auszug*11.25*.pdf"))
    
    if not pdf_files:
        print("⚠️  Keine PDFs gefunden")
        return
    
    print(f"📄 {len(pdf_files)} PDF-Dateien gefunden\n")
    
    total_imported = 0
    total_duplicates = 0
    
    for pdf_file in pdf_files:
        print(f"📄 {pdf_file.name}")
        print("-"*70)
        
        transactions = parse_sparkasse_online_pdf(pdf_file)
        
        if not transactions:
            print("  ⚠️  Keine Transaktionen gefunden\n")
            continue
        
        stats = import_to_db(transactions, konto_id, dry_run)
        
        print(f"  ✅ Gefunden: {len(transactions)}")
        print(f"  ✅ Importiert: {stats['imported']}")
        print(f"  ⊘ Duplikate: {stats['duplicates']}\n")
        
        total_imported += stats['imported']
        total_duplicates += stats['duplicates']
    
    print("="*70)
    print("✅ IMPORT ABGESCHLOSSEN")
    print("="*70)
    print(f"Importiert:  {total_imported}")
    print(f"Duplikate:   {total_duplicates}")

if __name__ == "__main__":
    main()
