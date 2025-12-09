#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bank-PDF Import CLI - Bankenspiegel 3.0
=======================================
Benutzerfreundliches Kommandozeilen-Interface für PDF-Import
Usage:
    python import_bank_pdfs.py --help
Author: Claude AI
Version: 3.0.1
Date: 2025-11-10
"""
import argparse
import logging
import sys
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from parsers.parser_factory import ParserFactory
from scripts.imports.pdf_importer import PDFImporter
from scripts.imports.transaction_manager import TransactionManager

def setup_logging(verbose: bool = False):
    """Konfiguriert Logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def main():
    """Hauptfunktion"""
    parser = argparse.ArgumentParser(
        description='Bank-PDF Import für Bankenspiegel 3.0'
    )
    
    parser.add_argument(
        'pdf_path',
        type=str,
        help='Pfad zur PDF-Datei oder Verzeichnis mit PDFs'
    )
    
    parser.add_argument(
        '--bank',
        type=str,
        choices=['hypovereinsbank', 'sparkasse', 'vrbank', 'auto'],
        default='auto',
        help='Bank-Typ (auto = automatische Erkennung)'
    )
    
    parser.add_argument(
        '--konto-id',
        type=int,
        help='Konto-ID in der Datenbank'
    )
    
    parser.add_argument(
        '--db',
        type=str,
        default='data/greiner_controlling.db',
        help='Pfad zur SQLite-Datenbank'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Ausführliche Ausgabe'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test-Modus (keine DB-Änderungen)'
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("Bank-PDF Import gestartet")
    logger.info("=" * 80)
    
    # PDF-Pfad validieren
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        logger.error(f"Pfad existiert nicht: {pdf_path}")
        sys.exit(1)
    
    # PDF-Dateien sammeln
    if pdf_path.is_file():
        pdf_files = [pdf_path]
    else:
        pdf_files = list(pdf_path.glob('*.pdf'))
        if not pdf_files:
            logger.error(f"Keine PDF-Dateien gefunden in: {pdf_path}")
            sys.exit(1)
    
    logger.info(f"Gefundene PDF-Dateien: {len(pdf_files)}")
    
    # Importer initialisieren
    importer = PDFImporter(db_path=args.db)
    
    # Jede PDF verarbeiten
    erfolg = 0
    fehler = 0
    
    for pdf_file in pdf_files:
        logger.info(f"\nVerarbeite: {pdf_file.name}")
        
        try:
            if args.dry_run:
                logger.info("  [DRY-RUN] Würde importiert werden")
                erfolg += 1
            else:
                result = importer.import_pdf(
                    pdf_path=str(pdf_file),
                    bank_type=args.bank,
                    konto_id=args.konto_id
                )
                
                if result:
                    logger.info(f"  ✓ Erfolgreich importiert")
                    erfolg += 1
                else:
                    logger.warning(f"  ⚠ Import fehlgeschlagen")
                    fehler += 1
                    
        except Exception as e:
            logger.error(f"  ✗ Fehler: {e}")
            fehler += 1
    
    # Zusammenfassung
    logger.info("\n" + "=" * 80)
    logger.info("Import abgeschlossen")
    logger.info("=" * 80)
    logger.info(f"Erfolgreich: {erfolg}")
    logger.info(f"Fehler:      {fehler}")
    logger.info(f"Gesamt:      {len(pdf_files)}")
    
    sys.exit(0 if fehler == 0 else 1)

if __name__ == '__main__':
    main()
