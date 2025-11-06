#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Importer fÃ¼r Bankenspiegel 3.0
==================================
Haupt-Importer der PDFs findet, parst und in DB speichert

Features:
- Rekursive PDF-Suche
- Automatische Bank-Erkennung
- Batch-Import
- Progress-Tracking
- Detaillierte Statistiken
- Filter (Jahr, Bank, etc.)

Author: Claude AI
Version: 3.0
Date: 2025-11-06
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import time

from parsers import ParserFactory
from transaction_manager import TransactionManager

logger = logging.getLogger(__name__)


class PDFImporter:
    """
    Haupt-Importer fÃ¼r Bank-PDFs
    
    Findet PDFs, parst sie und speichert Transaktionen in DB
    
    Usage:
        importer = PDFImporter(
            pdf_directory='/pfad/zu/pdfs',
            db_path='data/greiner_controlling.db'
        )
        
        results = importer.import_all()
    """
    
    def __init__(
        self,
        pdf_directory: str,
        db_path: str = 'data/greiner_controlling.db',
        min_year: Optional[int] = None,
        bank_filter: Optional[str] = None,
        skip_duplicates: bool = True
    ):
        """
        Initialisiert den PDF Importer
        
        Args:
            pdf_directory: Verzeichnis mit PDFs (wird rekursiv durchsucht)
            db_path: Pfad zur Datenbank
            min_year: Optional - nur PDFs ab diesem Jahr
            bank_filter: Optional - nur diese Bank ('sparkasse', 'vrbank', 'hypovereinsbank')
            skip_duplicates: Duplikate Ã¼berspringen (default: True)
        """
        self.pdf_directory = Path(pdf_directory)
        self.db_path = db_path
        self.min_year = min_year
        self.bank_filter = bank_filter
        self.skip_duplicates = skip_duplicates
        
        if not self.pdf_directory.exists():
            raise FileNotFoundError(f"PDF-Verzeichnis nicht gefunden: {pdf_directory}")
        
        # Transaction Manager
        self.transaction_manager = TransactionManager(db_path)
        
        # Statistiken
        self.stats = {
            'total_pdfs': 0,
            'processed': 0,
            'skipped': 0,
            'errors': 0,
            'total_transactions': 0,
            'imported': 0,
            'duplicates': 0
        }
        
        logger.info(f"PDF Importer initialisiert")
        logger.info(f"  Verzeichnis: {self.pdf_directory}")
        logger.info(f"  Datenbank: {self.db_path}")
        if self.min_year:
            logger.info(f"  Min. Jahr: {self.min_year}")
        if self.bank_filter:
            logger.info(f"  Bank-Filter: {self.bank_filter}")
    
    def import_all(self) -> Dict:
        """
        Importiert alle PDFs im Verzeichnis
        
        Returns:
            Dictionary mit Statistiken
        """
        start_time = time.time()
        
        logger.info("=" * 70)
        logger.info("ðŸš€ BANKENSPIEGEL PDF IMPORT")
        logger.info("=" * 70)
        
        # PDFs finden
        pdf_files = self._find_pdfs()
        
        if not pdf_files:
            logger.warning("âŒ Keine PDFs gefunden!")
            return self.stats
        
        self.stats['total_pdfs'] = len(pdf_files)
        logger.info(f"\nðŸ“„ Gefundene PDFs: {len(pdf_files)}\n")
        
        # PDFs verarbeiten
        for i, pdf_path in enumerate(pdf_files, 1):
            logger.info(f"[{i}/{len(pdf_files)}] {pdf_path.name}")
            logger.info("-" * 70)
            
            try:
                result = self._import_single_pdf(pdf_path)
                
                if result['status'] == 'success':
                    self.stats['processed'] += 1
                    self.stats['total_transactions'] += result['transactions']
                    self.stats['imported'] += result['imported']
                    self.stats['duplicates'] += result['duplicates']
                elif result['status'] == 'skip':
                    self.stats['skipped'] += 1
                else:
                    self.stats['errors'] += 1
            
            except Exception as e:
                logger.error(f"âŒ Unerwarteter Fehler: {e}")
                self.stats['errors'] += 1
            
            logger.info("")
        
        # Zusammenfassung
        elapsed_time = time.time() - start_time
        self._log_summary(elapsed_time)
        
        return self.stats
    
    def import_single_file(self, pdf_path: str) -> Dict:
        """
        Importiert eine einzelne PDF-Datei
        
        Args:
            pdf_path: Pfad zur PDF
            
        Returns:
            Dictionary mit Ergebnis
        """
        logger.info("=" * 70)
        logger.info(f"ðŸ“„ IMPORT: {Path(pdf_path).name}")
        logger.info("=" * 70)
        
        result = self._import_single_pdf(Path(pdf_path))
        
        logger.info("\n" + "=" * 70)
        logger.info("âœ… IMPORT ABGESCHLOSSEN")
        logger.info("=" * 70)
        logger.info(f"Status: {result['status']}")
        logger.info(f"Transaktionen gefunden: {result['transactions']}")
        logger.info(f"Importiert: {result['imported']}")
        if result['duplicates'] > 0:
            logger.info(f"Duplikate: {result['duplicates']}")
        logger.info("=" * 70)
        
        return result
    
    def _find_pdfs(self) -> List[Path]:
        """
        Findet alle PDFs im Verzeichnis (rekursiv)
        
        Returns:
            Liste von PDF-Pfaden
        """
        logger.info("ðŸ” Suche PDFs...")
        
        # Alle PDFs finden
        all_pdfs = list(self.pdf_directory.rglob('*.pdf'))
        
        # Filter anwenden
        filtered_pdfs = []
        
        for pdf_path in all_pdfs:
            # Jahr-Filter
            if self.min_year:
                if not self._matches_year_filter(pdf_path):
                    continue
            
            # Bank-Filter
            if self.bank_filter:
                if not self._matches_bank_filter(pdf_path):
                    continue
            
            # Nur KontoauszÃ¼ge (keine Mitteilungen etc.)
            if not self._is_bank_statement(pdf_path):
                continue
            
            filtered_pdfs.append(pdf_path)
        
        return sorted(filtered_pdfs)
    
    def _matches_year_filter(self, pdf_path: Path) -> bool:
        """PrÃ¼ft ob PDF Jahr-Filter erfÃ¼llt"""
        import re
        
        # Suche Jahr im Dateinamen
        year_match = re.search(r'_(\d{4})_', pdf_path.name)
        if year_match:
            year = int(year_match.group(1))
            return year >= self.min_year
        
        # Wenn kein Jahr im Dateinamen, akzeptieren (wird spÃ¤ter geprÃ¼ft)
        return True
    
    def _matches_bank_filter(self, pdf_path: Path) -> bool:
        """PrÃ¼ft ob PDF Bank-Filter erfÃ¼llt"""
        filename_lower = pdf_path.name.lower()
        
        if self.bank_filter == 'sparkasse':
            return 'sparkasse' in filename_lower or 'sparkass' in filename_lower
        elif self.bank_filter == 'vrbank':
            return any(k in filename_lower for k in ['genobank', 'vr bank', 'vrbank', 'volksbank'])
        elif self.bank_filter == 'hypovereinsbank':
            return 'hypo' in filename_lower or 'unicredit' in filename_lower
        
        return True
    
    def _is_bank_statement(self, pdf_path: Path) -> bool:
        """PrÃ¼ft ob PDF ein Kontoauszug ist"""
        filename_lower = pdf_path.name.lower()
        
        # Positive Keywords
        positive = ['kontoauszug', 'auszug', 'konto_', 'umsatz']
        
        # Negative Keywords (ausschlieÃŸen)
        negative = ['mitteilung', 'info', 'werbung', 'newsletter']
        
        # Muss mindestens ein positives Keyword haben
        has_positive = any(k in filename_lower for k in positive)
        
        # Darf kein negatives Keyword haben
        has_negative = any(k in filename_lower for k in negative)
        
        return has_positive and not has_negative
    
    def _import_single_pdf(self, pdf_path: Path) -> Dict:
        """
        Importiert eine einzelne PDF
        
        Returns:
            Dictionary mit Ergebnis:
            {
                'status': 'success' | 'skip' | 'error',
                'transactions': Anzahl gefundener Transaktionen,
                'imported': Anzahl importierter Transaktionen,
                'duplicates': Anzahl Duplikate,
                'error': Fehlerme ldung (falls error)
            }
        """
        result = {
            'status': 'error',
            'transactions': 0,
            'imported': 0,
            'duplicates': 0,
            'error': None
        }
        
        try:
            # Parser erstellen (automatische Erkennung)
            parser = ParserFactory.create_parser(
                str(pdf_path),
                force_parser=self.bank_filter
            )
            
            # PDF parsen
            transactions = parser.parse()
            result['transactions'] = len(transactions)
            
            if not transactions:
                logger.info("âŠ˜ Keine Transaktionen gefunden")
                result['status'] = 'skip'
                return result
            
            logger.info(f"âœ“ {len(transactions)} Transaktionen gefunden")
            
            # In Datenbank speichern
            save_result = self.transaction_manager.save_transactions(
                transactions,
                pdf_path.name,
                skip_duplicates=self.skip_duplicates
            )
            
            result['imported'] = save_result['imported']
            result['duplicates'] = save_result['duplicates']
            
            if save_result['imported'] > 0:
                logger.info(f"âœ… {save_result['imported']} Transaktionen gespeichert")
            
            if save_result['duplicates'] > 0:
                logger.info(f"ðŸ“„ {save_result['duplicates']} Duplikate Ã¼bersprungen")
            
            if save_result['errors'] > 0:
                logger.warning(f"âš ï¸ {save_result['errors']} Fehler")
            
            result['status'] = 'success'
        
        except Exception as e:
            logger.error(f"âŒ Fehler beim Import: {e}")
            result['error'] = str(e)
            result['status'] = 'error'
        
        return result
    
    def _log_summary(self, elapsed_time: float):
        """Loggt Zusammenfassung"""
        logger.info("=" * 70)
        logger.info("ðŸ“Š IMPORT ABGESCHLOSSEN")
        logger.info("=" * 70)
        logger.info(f"PDFs gefunden:           {self.stats['total_pdfs']}")
        logger.info(f"PDFs verarbeitet:        {self.stats['processed']}")
        logger.info(f"PDFs Ã¼bersprungen:       {self.stats['skipped']}")
        logger.info(f"PDFs mit Fehler:         {self.stats['errors']}")
        logger.info("-" * 70)
        logger.info(f"Transaktionen gefunden:  {self.stats['total_transactions']}")
        logger.info(f"Transaktionen importiert: {self.stats['imported']}")
        logger.info(f"Duplikate Ã¼bersprungen:  {self.stats['duplicates']}")
        logger.info("-" * 70)
        logger.info(f"Dauer: {elapsed_time:.1f} Sekunden")
        logger.info("=" * 70)


# FÃ¼r Testing
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_importer.py <pdf_directory> [min_year] [bank_filter]")
        print("\nBeispiele:")
        print("  python pdf_importer.py /pfad/zu/pdfs")
        print("  python pdf_importer.py /pfad/zu/pdfs 2025")
        print("  python pdf_importer.py /pfad/zu/pdfs 2025 sparkasse")
        sys.exit(1)
    
    pdf_dir = sys.argv[1]
    min_year = int(sys.argv[2]) if len(sys.argv) > 2 else None
    bank_filter = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        importer = PDFImporter(
            pdf_directory=pdf_dir,
            min_year=min_year,
            bank_filter=bank_filter
        )
        
        results = importer.import_all()
        
        # Exit Code basierend auf Erfolg
        if results['errors'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
    
    except FileNotFoundError as e:
        print(f"\nâŒ Fehler: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nâŒ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
