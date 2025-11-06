#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bank-PDF Import CLI - Bankenspiegel 3.0
=======================================
Benutzerfreundliches Kommandozeilen-Interface fÃ¼r PDF-Import

Usage:
    python import_bank_pdfs.py --help

Author: Claude AI
Version: 3.0
Date: 2025-11-06
"""

import argparse
import logging
import sys
from pathlib import Path

from pdf_importer import PDFImporter
from parsers import ParserFactory
from transaction_manager import TransactionManager


def setup_logging(verbose: bool = False):
    """Konfiguriert Logging"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bank_import.log')
        ]
    )


def cmd_import(args):
    """Haupt-Import-Kommando"""
    importer = PDFImporter(
        pdf_directory=args.directory,
        db_path=args.database,
        min_year=args.min_year,
        bank_filter=args.bank,
        skip_duplicates=not args.allow_duplicates
    )
    
    if args.file:
        # Einzelne Datei
        result = importer.import_single_file(args.file)
        return 0 if result['status'] == 'success' else 1
    else:
        # Alle PDFs im Verzeichnis
        results = importer.import_all()
        return 0 if results['errors'] == 0 else 1


def cmd_test(args):
    """Test-Kommando - parst PDF ohne DB-Import"""
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 70)
    logger.info("ðŸ§ª TEST-MODUS (kein DB-Import)")
    logger.info("=" * 70)
    
    try:
        # Parser erstellen
        parser = ParserFactory.create_parser(
            args.file,
            force_parser=args.bank
        )
        
        logger.info(f"Parser: {parser.__class__.__name__}")
        logger.info(f"Bank: {parser.bank_name}")
        logger.info("")
        
        # Parsen
        transactions = parser.parse()
        
        if not transactions:
            logger.warning("âŒ Keine Transaktionen gefunden")
            return 1
        
        logger.info(f"\nâœ… {len(transactions)} Transaktionen gefunden\n")
        
        # Erste 10 anzeigen
        logger.info("Erste 10 Transaktionen:")
        logger.info("-" * 70)
        for i, t in enumerate(transactions[:10], 1):
            logger.info(f"{i:2d}. {t.buchungsdatum} | {t.betrag:>12,.2f} EUR | {t.verwendungszweck[:50]}")
        
        if len(transactions) > 10:
            logger.info(f"... und {len(transactions) - 10} weitere")
        
        # Statistiken
        stats = parser.get_statistics()
        logger.info("\n" + "=" * 70)
        logger.info("STATISTIKEN")
        logger.info("=" * 70)
        logger.info(f"Anzahl:     {stats['count']}")
        logger.info(f"Summe:      {stats['total_amount']:,.2f} EUR")
        logger.info(f"Zeitraum:   {stats['date_range'][0]} bis {stats['date_range'][1]}" if stats['date_range'] else "N/A")
        logger.info(f"IBAN:       {parser.iban or 'Nicht gefunden'}")
        
        return 0
    
    except Exception as e:
        logger.error(f"âŒ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_info(args):
    """Info-Kommando - zeigt Datenbank-Informationen"""
    logger = logging.getLogger(__name__)
    
    try:
        manager = TransactionManager(args.database)
        
        logger.info("=" * 70)
        logger.info("ðŸ“Š DATENBANK-INFORMATIONEN")
        logger.info("=" * 70)
        
        # Validierung
        logger.info("\n1. Validierung:")
        validation = manager.validate_database()
        all_valid = validation.pop('all_valid')
        
        for key, value in sorted(validation.items()):
            status = "âœ“" if value else "âœ—"
            logger.info(f"   {status} {key.replace('_', ' ').title()}")
        
        if not all_valid:
            logger.error("\nâŒ Datenbank-Struktur ist nicht vollstÃ¤ndig!")
            return 1
        
        # Konten
        logger.info("\n2. VerfÃ¼gbare Konten:")
        accounts = manager.get_account_info()
        
        if not accounts:
            logger.warning("   Keine Konten gefunden")
        else:
            for acc in accounts:
                active = "âœ“" if acc['aktiv'] else "âœ—"
                logger.info(f"   {active} {acc['bank_name']:30} | {acc['kontoname']:30} | {acc['iban']}")
        
        # Statistiken
        logger.info("\n3. Transaktions-Statistiken:")
        stats = manager.get_transaction_stats()
        logger.info(f"   Gesamt:     {stats['count']:,} Transaktionen")
        logger.info(f"   Summe:      {stats['total_amount']:,.2f} EUR")
        logger.info(f"   Zeitraum:   {stats['date_from']} bis {stats['date_to']}")
        
        # Pro Bank
        logger.info("\n4. Pro Bank:")
        for acc in accounts[:10]:  # Max 10
            stats = manager.get_transaction_stats(konto_id=acc['id'])
            if stats['count'] > 0:
                logger.info(f"   {acc['bank_name']:30} | {stats['count']:6,} Trans. | {stats['total_amount']:>15,.2f} EUR")
        
        logger.info("=" * 70)
        return 0
    
    except FileNotFoundError as e:
        logger.error(f"âŒ {e}")
        return 1
    except Exception as e:
        logger.error(f"âŒ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_list_banks(args):
    """Listet unterstÃ¼tzte Banken"""
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 70)
    logger.info("ðŸ¦ UNTERSTÃœTZTE BANKEN")
    logger.info("=" * 70)
    
    banks = ParserFactory.get_supported_banks()
    for i, bank in enumerate(banks, 1):
        logger.info(f"{i}. {bank}")
    
    logger.info("\n" + "=" * 70)
    logger.info("PARSER-DETAILS")
    logger.info("=" * 70)
    
    info = ParserFactory.get_parser_info()
    for parser_id, details in info.items():
        logger.info(f"\n{details['name']}:")
        logger.info(f"  ID:       {parser_id}")
        logger.info(f"  Keywords: {', '.join(details['keywords'])}")
        logger.info(f"  Format:   {details['format']}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Bank-PDF Import fÃ¼r Bankenspiegel 3.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Alle PDFs importieren
  %(prog)s import /pfad/zu/pdfs

  # Nur ab 2025
  %(prog)s import /pfad/zu/pdfs --min-year 2025

  # Nur Sparkasse
  %(prog)s import /pfad/zu/pdfs --bank sparkasse

  # Einzelne Datei testen (ohne DB-Import)
  %(prog)s test sparkasse_2025.pdf

  # Datenbank-Info anzeigen
  %(prog)s info

  # UnterstÃ¼tzte Banken auflisten
  %(prog)s list-banks
        """
    )
    
    # Global Arguments
    parser.add_argument(
        '--database', '-d',
        default='data/greiner_controlling.db',
        help='Pfad zur Datenbank (default: data/greiner_controlling.db)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='AusfÃ¼hrliche Ausgabe (Debug-Level)'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='VerfÃ¼gbare Kommandos')
    
    # IMPORT Command
    import_parser = subparsers.add_parser('import', help='Importiert PDFs in Datenbank')
    import_parser.add_argument(
        'directory',
        help='Verzeichnis mit PDFs (wird rekursiv durchsucht)'
    )
    import_parser.add_argument(
        '--file', '-f',
        help='Einzelne Datei importieren (statt ganzes Verzeichnis)'
    )
    import_parser.add_argument(
        '--min-year',
        type=int,
        help='Nur PDFs ab diesem Jahr'
    )
    import_parser.add_argument(
        '--bank', '-b',
        choices=['sparkasse', 'vrbank', 'hypovereinsbank'],
        help='Nur diese Bank importieren'
    )
    import_parser.add_argument(
        '--allow-duplicates',
        action='store_true',
        help='Duplikate erlauben (Standard: Duplikate werden Ã¼bersprungen)'
    )
    
    # TEST Command
    test_parser = subparsers.add_parser('test', help='Testet PDF-Parsing (ohne DB-Import)')
    test_parser.add_argument(
        'file',
        help='PDF-Datei zum Testen'
    )
    test_parser.add_argument(
        '--bank', '-b',
        choices=['sparkasse', 'vrbank', 'hypovereinsbank'],
        help='Parser erzwingen (statt automatische Erkennung)'
    )
    
    # INFO Command
    info_parser = subparsers.add_parser('info', help='Zeigt Datenbank-Informationen')
    
    # LIST-BANKS Command
    list_parser = subparsers.add_parser('list-banks', help='Listet unterstÃ¼tzte Banken')
    
    # Parse Arguments
    args = parser.parse_args()
    
    # Setup Logging
    setup_logging(args.verbose)
    
    # Execute Command
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'import':
        return cmd_import(args)
    elif args.command == 'test':
        return cmd_test(args)
    elif args.command == 'info':
        return cmd_info(args)
    elif args.command == 'list-banks':
        return cmd_list_banks(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
