#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IMPORT 2025 - Sauberer Import aller Kontoauszüge
================================================
Importiert systematisch alle 2025 PDFs mit den richtigen Parsern

Author: Claude AI
Date: 2025-11-13
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Projekt-Root
sys.path.insert(0, '/opt/greiner-portal')

# Parser imports
from parsers import SparkasseParser, HypoVereinsbankParser
from parsers.vrbank_parser import VRBankParser

# Pfade
BASE_DIR = "/mnt/buchhaltung/Buchhaltung/Kontoauszüge"
DB_PATH = "/opt/greiner-portal/data/greiner_controlling.db"

# Bank-zu-Parser Mapping
BANK_PARSERS = {
    'sparkasse': SparkasseParser,
    'hypovereinsbank': HypoVereinsbankParser,
    'genobank': None,  # TODO: GenobankParser wenn vorhanden
    'vr bank': VRBankParser,
}

def detect_bank_from_dirname(dirname: str) -> str:
    """Erkennt Bank aus Ordnername"""
    dirname_lower = dirname.lower()
    
    if 'sparkasse' in dirname_lower:
        return 'sparkasse'
    elif 'hypo' in dirname_lower:
        return 'hypovereinsbank'
    elif 'vr' in dirname_lower or 'landau' in dirname_lower:
        return 'vr bank'
    elif 'geno' in dirname_lower:
        return 'genobank'
    else:
        return None

def is_2025_pdf(filename: str) -> bool:
    """Prüft ob PDF aus 2025 ist (aus Dateiname)"""
    # Patterns: .01.25, .02.25, ..., .12.25
    # oder: .01.2025, .02.2025, etc.
    
    for month in range(1, 13):
        if f'.{month:02d}.25' in filename or f'.{month:02d}.2025' in filename:
            return True
        if f'.{month}.25' in filename:  # Auch ohne führende Null
            return True
    
    return '2025' in filename

def import_pdf(pdf_path: str, parser_class, conn: sqlite3.Connection) -> dict:
    """
    Importiert eine einzelne PDF
    
    Returns:
        Dict mit Statistik
    """
    result = {
        'pdf': os.path.basename(pdf_path),
        'parsed': 0,
        'imported': 0,
        'skipped': 0,
        'error': None
    }
    
    try:
        # Parse PDF
        parser = parser_class(pdf_path)
        transactions = parser.parse()
        result['parsed'] = len(transactions)
        
        if not transactions:
            logger.warning(f"   ⚠️ Keine Transaktionen in {result['pdf']}")
            return result
        
        # IBAN prüfen
        if not parser.iban:
            result['error'] = "Keine IBAN gefunden"
            logger.error(f"   ❌ Keine IBAN in {result['pdf']}")
            return result
        
        # Konto in DB finden
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, kontoname FROM konten WHERE iban = ?", 
            (parser.iban,)
        )
        konto_result = cursor.fetchone()
        
        if not konto_result:
            result['error'] = f"Konto für IBAN {parser.iban} nicht gefunden"
            logger.error(f"   ❌ Konto nicht gefunden: {parser.iban}")
            return result
        
        konto_id, kontoname = konto_result
        logger.info(f"   📊 {len(transactions)} Transaktionen für {kontoname}")
        
        # Transaktionen importieren (mit Duplikat-Check)
        for trans in transactions:
            # Check ob bereits existiert
            cursor.execute("""
                SELECT COUNT(*) FROM transaktionen 
                WHERE konto_id = ? 
                AND buchungsdatum = ? 
                AND betrag = ?
                AND verwendungszweck = ?
            """, (
                konto_id,
                trans.buchungsdatum.strftime('%Y-%m-%d'),
                trans.betrag,
                trans.verwendungszweck
            ))
            
            if cursor.fetchone()[0] > 0:
                result['skipped'] += 1
                continue
            
            # Importiere
            cursor.execute("""
                INSERT INTO transaktionen (
                    konto_id, buchungsdatum, valutadatum,
                    verwendungszweck, betrag, waehrung
                ) VALUES (?, ?, ?, ?, ?, 'EUR')
            """, (
                konto_id,
                trans.buchungsdatum.strftime('%Y-%m-%d'),
                trans.valutadatum.strftime('%Y-%m-%d'),
                trans.verwendungszweck,
                trans.betrag
            ))
            result['imported'] += 1
        
        # Commit nach jeder PDF
        if result['imported'] > 0:
            conn.commit()
            logger.info(f"   ✅ {result['imported']} neue Transaktionen importiert")
        
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"   ❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
    
    return result

def main():
    """Hauptfunktion - importiert alle 2025 PDFs"""
    
    print("\n" + "="*70)
    print("🚀 IMPORT 2025 - ALLE KONTOAUSZÜGE")
    print("="*70)
    
    # DB-Verbindung
    conn = sqlite3.connect(DB_PATH)
    
    # Backup
    backup_path = f"{DB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"📦 Erstelle Backup: {backup_path}")
    import shutil
    shutil.copy(DB_PATH, backup_path)
    
    # Statistik
    total_stats = {
        'banks': 0,
        'pdfs': 0,
        'imported': 0,
        'skipped': 0,
        'errors': 0
    }
    
    # Durchgehe alle Bank-Ordner
    for bank_dirname in sorted(os.listdir(BASE_DIR)):
        bank_path = os.path.join(BASE_DIR, bank_dirname)
        
        # Skip wenn kein Ordner
        if not os.path.isdir(bank_path):
            continue
        
        # Erkenne Bank
        bank_type = detect_bank_from_dirname(bank_dirname)
        
        if not bank_type:
            logger.warning(f"⚠️ Bank nicht erkannt: {bank_dirname}")
            continue
        
        # Parser holen
        parser_class = BANK_PARSERS.get(bank_type)
        
        if not parser_class:
            logger.warning(f"⚠️ Kein Parser für {bank_type}: {bank_dirname}")
            continue
        
        print(f"\n📁 {bank_dirname} ({bank_type}):")
        print("-" * 50)
        
        # Finde 2025 PDFs
        pdfs_2025 = []
        for filename in os.listdir(bank_path):
            if filename.endswith('.pdf') and is_2025_pdf(filename):
                pdfs_2025.append(filename)
        
        if not pdfs_2025:
            logger.info("   Keine 2025 PDFs gefunden")
            continue
        
        logger.info(f"   📄 {len(pdfs_2025)} PDFs aus 2025 gefunden")
        total_stats['banks'] += 1
        
        # Sortiere chronologisch (wenn möglich)
        pdfs_2025.sort()
        
        # Importiere jede PDF
        for pdf_file in pdfs_2025:
            pdf_path = os.path.join(bank_path, pdf_file)
            logger.info(f"\n   Verarbeite: {pdf_file}")
            
            result = import_pdf(pdf_path, parser_class, conn)
            
            total_stats['pdfs'] += 1
            total_stats['imported'] += result['imported']
            total_stats['skipped'] += result['skipped']
            if result['error']:
                total_stats['errors'] += 1
    
    # Finale Statistik
    print("\n" + "="*70)
    print("📊 IMPORT ABGESCHLOSSEN")
    print("="*70)
    print(f"✅ Banken verarbeitet:    {total_stats['banks']}")
    print(f"📄 PDFs verarbeitet:      {total_stats['pdfs']}")
    print(f"💾 Neue Transaktionen:    {total_stats['imported']}")
    print(f"⏭️  Duplikate übersprungen: {total_stats['skipped']}")
    print(f"❌ Fehler:                {total_stats['errors']}")
    
    # Zeige aktuelle Kontostände
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            k.kontoname,
            COUNT(t.id) as trans_count,
            MIN(t.buchungsdatum) as von,
            MAX(t.buchungsdatum) as bis
        FROM konten k
        LEFT JOIN transaktionen t ON k.id = t.konto_id
        WHERE k.aktiv = 1
        GROUP BY k.id
        HAVING trans_count > 0
        ORDER BY k.kontoname
    """)
    
    print("\n📊 KONTOSTÄNDE NACH IMPORT:")
    print("-" * 70)
    
    for row in cursor.fetchall():
        print(f"{row[0]:<30} {row[1]:>6} Trans. ({row[2]} bis {row[3]})")
    
    conn.close()
    
    print("\n✅ Import erfolgreich abgeschlossen!")
    print(f"📦 Backup verfügbar: {backup_path}")
    
    return total_stats

if __name__ == "__main__":
    try:
        stats = main()
        sys.exit(0 if stats['errors'] == 0 else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Import abgebrochen!")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Kritischer Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
