#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser Factory fÃ¼r Bankenspiegel 3.0
====================================
Automatische Erkennung des richtigen Parsers basierend auf Dateinamen oder PDF-Inhalt

Usage:
    from parsers import ParserFactory
    
    parser = ParserFactory.create_parser('path/to/sparkasse.pdf')
    transactions = parser.parse()

Author: Claude AI
Version: 3.0
Date: 2025-11-06
"""

import logging
from pathlib import Path
from typing import Optional
import pdfplumber

from .base_parser import BaseParser
from .sparkasse_parser import SparkasseParser
from .vrbank_parser import VRBankParser
from .hypovereinsbank_parser import HypovereinsbankParser

logger = logging.getLogger(__name__)


class ParserFactory:
    """
    Factory-Klasse fÃ¼r automatische Parser-Auswahl
    
    Erkennt die Bank anhand von:
    1. Dateinamen (z.B. "sparkasse_2025.pdf")
    2. PDF-Inhalt (erste Seite)
    """
    
    # Bank-Keywords im Dateinamen
    FILENAME_PATTERNS = {
        'sparkasse': SparkasseParser,
        'sparkass': SparkasseParser,
        'genobank': VRBankParser,
        'vr bank': VRBankParser,
        'vr-bank': VRBankParser,
        'vrbank': VRBankParser,
        'volksbank': VRBankParser,
        'raiffeisenbank': VRBankParser,
        'hypovereinsbank': HypovereinsbankParser,
        'hypo': HypovereinsbankParser,
        'unicredit': HypovereinsbankParser,
    }
    
    # Bank-Keywords im PDF-Inhalt
    CONTENT_PATTERNS = {
        'Sparkasse': SparkasseParser,
        'VR GenoBank': VRBankParser,
        'Volksbank': VRBankParser,
        'Raiffeisenbank': VRBankParser,
        'HypoVereinsbank': HypovereinsbankParser,
        'UniCredit Bank': HypovereinsbankParser,
    }
    
    @classmethod
    def create_parser(cls, pdf_path: str, force_parser: Optional[str] = None) -> BaseParser:
        """
        Erstellt den passenden Parser fÃ¼r eine PDF-Datei
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            force_parser: Optional - erzwinge spezifischen Parser
                         ('sparkasse', 'vrbank', 'hypovereinsbank')
        
        Returns:
            Instanz des passenden Parsers
            
        Raises:
            FileNotFoundError: Wenn PDF nicht existiert
            ValueError: Wenn kein passender Parser gefunden
        """
        pdf_path_obj = Path(pdf_path)
        
        if not pdf_path_obj.exists():
            raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")
        
        # Force-Parser wenn angegeben
        if force_parser:
            return cls._get_forced_parser(pdf_path, force_parser)
        
        # 1. Versuch: Dateinamen-basierte Erkennung
        parser_class = cls._detect_by_filename(pdf_path_obj)
        if parser_class:
            logger.info(f"âœ“ Parser erkannt (Dateiname): {parser_class.__name__}")
            return parser_class(pdf_path)
        
        # 2. Versuch: Inhalt-basierte Erkennung
        parser_class = cls._detect_by_content(pdf_path)
        if parser_class:
            logger.info(f"âœ“ Parser erkannt (Inhalt): {parser_class.__name__}")
            return parser_class(pdf_path)
        
        # Fallback: Sparkasse (meistens funktioniert das Format)
        logger.warning(f"âš ï¸ Bank nicht erkannt - nutze Sparkasse-Parser als Fallback")
        return SparkasseParser(pdf_path)
    
    @classmethod
    def _get_forced_parser(cls, pdf_path: str, parser_type: str) -> BaseParser:
        """Gibt erzwungenen Parser zurÃ¼ck"""
        parser_map = {
            'sparkasse': SparkasseParser,
            'vrbank': VRBankParser,
            'hypovereinsbank': HypovereinsbankParser,
        }
        
        parser_class = parser_map.get(parser_type.lower())
        if not parser_class:
            raise ValueError(f"Unbekannter Parser-Typ: {parser_type}")
        
        logger.info(f"âœ“ Erzwungener Parser: {parser_class.__name__}")
        return parser_class(pdf_path)
    
    @classmethod
    def _detect_by_filename(cls, pdf_path: Path) -> Optional[type]:
        """
        Erkennt Parser anhand des Dateinamens
        
        Args:
            pdf_path: Path-Objekt zur PDF
            
        Returns:
            Parser-Klasse oder None
        """
        filename_lower = pdf_path.name.lower()
        
        for keyword, parser_class in cls.FILENAME_PATTERNS.items():
            if keyword in filename_lower:
                logger.debug(f"Match im Dateinamen: '{keyword}' -> {parser_class.__name__}")
                return parser_class
        
        return None
    
    @classmethod
    def _detect_by_content(cls, pdf_path: str) -> Optional[type]:
        """
        Erkennt Parser anhand des PDF-Inhalts
        
        Liest erste Seite und sucht nach Bank-Keywords
        
        Args:
            pdf_path: Pfad zur PDF
            
        Returns:
            Parser-Klasse oder None
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if not pdf.pages:
                    return None
                
                # Erste Seite lesen
                first_page_text = pdf.pages[0].extract_text()
                
                if not first_page_text:
                    return None
                
                # Nach Keywords suchen
                for keyword, parser_class in cls.CONTENT_PATTERNS.items():
                    if keyword in first_page_text:
                        logger.debug(f"Match im Inhalt: '{keyword}' -> {parser_class.__name__}")
                        return parser_class
                
                return None
        
        except Exception as e:
            logger.error(f"Fehler beim Lesen der PDF: {e}")
            return None
    
    @classmethod
    def get_supported_banks(cls) -> list:
        """
        Gibt Liste der unterstÃ¼tzten Banken zurÃ¼ck
        
        Returns:
            Liste von Bank-Namen
        """
        return [
            "Sparkasse",
            "VR-Bank / Genobank",
            "HypoVereinsbank"
        ]
    
    @classmethod
    def get_parser_info(cls) -> dict:
        """
        Gibt Informationen Ã¼ber verfÃ¼gbare Parser zurÃ¼ck
        
        Returns:
            Dictionary mit Parser-Informationen
        """
        return {
            'sparkasse': {
                'class': SparkasseParser,
                'name': 'Sparkasse',
                'keywords': ['sparkasse', 'sparkass'],
                'format': 'DD.MM.YYYY Text Betrag'
            },
            'vrbank': {
                'class': VRBankParser,
                'name': 'VR-Bank / Genobank',
                'keywords': ['genobank', 'vr bank', 'volksbank', 'raiffeisenbank'],
                'format': 'DD.MM. DD.MM. Text Betrag H/S'
            },
            'hypovereinsbank': {
                'class': HypovereinsbankParser,
                'name': 'HypoVereinsbank',
                'keywords': ['hypovereinsbank', 'hypo', 'unicredit'],
                'format': 'DD.MM.YYYY DD.MM.YYYY Text Betrag EUR'
            }
        }


# FÃ¼r Testing
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*70)
    print("PARSER FACTORY - UNTERSTÃœTZTE BANKEN")
    print("="*70)
    
    banks = ParserFactory.get_supported_banks()
    for i, bank in enumerate(banks, 1):
        print(f"{i}. {bank}")
    
    print("\n" + "="*70)
    print("PARSER DETAILS")
    print("="*70)
    
    info = ParserFactory.get_parser_info()
    for parser_id, details in info.items():
        print(f"\n{details['name']}:")
        print(f"  Keywords: {', '.join(details['keywords'])}")
        print(f"  Format: {details['format']}")
    
    # Test mit Datei (falls angegeben)
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"\n{'='*70}")
        print(f"TEST: {pdf_path}")
        print("="*70)
        
        try:
            parser = ParserFactory.create_parser(pdf_path)
            print(f"âœ“ GewÃ¤hlter Parser: {parser.__class__.__name__}")
            print(f"âœ“ Bank: {parser.bank_name}")
        except Exception as e:
            print(f"âœ— Fehler: {e}")
