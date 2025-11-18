#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genobank Base Parser
====================
Gemeinsame Funktionen für Genobank-Parser

Verwendet von:
- GenobankTagesauszugParser (November-Format)
- GenobankKontoauszugParser (Monats-Format)

Author: Claude AI
Version: 1.0
Date: 2025-11-18
"""

from parsers.base_parser import BaseParser, Transaction
from typing import Optional, List
from datetime import datetime
import re
import logging
import pdfplumber

logger = logging.getLogger(__name__)


class GenobankBaseParser(BaseParser):
    """
    Basis-Klasse für alle Genobank-Parser
    
    Gemeinsame Funktionalität:
    - PDF-Text-Extraktion
    - IBAN-Extraktion (2 Formate)
    - Transaktions-Parsing
    """
    
    @property
    def bank_name(self) -> str:
        return "Genobank"
    
    def extract_text_from_pdf(self) -> str:
        """
        Extrahiert Text aus PDF mit pdfplumber
        
        Returns:
            Vollständiger Text der PDF
        """
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                return text
        except Exception as e:
            logger.error(f"❌ Fehler beim PDF-Lesen: {e}")
            self.errors.append(f"PDF-Fehler: {e}")
            return ""
    
    def extract_iban_genobank(self, text: str) -> Optional[str]:
        """
        Extrahiert IBAN aus Genobank-PDF
        
        Unterstützt 2 Formate:
        1. Tagesauszüge: "IBAN DE27741900000000057908"
        2. Kontoauszüge: "IBAN: DE96 7419 0000 1700 0579 08"
        
        WICHTIG: Sucht nur im Header (erste 1000 Zeichen)!
        
        Args:
            text: PDF-Text
            
        Returns:
            IBAN ohne Leerzeichen oder None
        """
        # Nur Header-Bereich durchsuchen (erste 1000 Zeichen)
        header = text[:1000]
        
        # Suche IBAN-Zeile
        for line in header.split('\n'):
            if 'IBAN' in line.upper():
                # Format 1: IBAN DE27741900000000057908 (ohne Leerzeichen)
                match1 = re.search(r'IBAN\s+(DE\d{20})', line)
                if match1:
                    iban = match1.group(1)
                    logger.debug(f"✓ IBAN gefunden (Format 1): {iban}")
                    return iban
                
                # Format 2: IBAN: DE96 7419 0000 1700 0579 08 (mit Leerzeichen)
                match2 = re.search(r'IBAN:\s+(DE\s*\d{2}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{2})', line)
                if match2:
                    iban = match2.group(1)
                    # Entferne Leerzeichen
                    iban = re.sub(r'\s+', '', iban)
                    logger.debug(f"✓ IBAN gefunden (Format 2): {iban}")
                    return iban
        
        logger.warning("⚠️ Keine IBAN im Header gefunden")
        return None
    
    def parse_transaction_table(self, text: str, start_marker: str, end_marker: str) -> List[Transaction]:
        """
        Parst Transaktions-Tabelle zwischen Start- und End-Marker
        
        Muss von Subclass überschrieben werden!
        
        Args:
            text: PDF-Text
            start_marker: Start der Transaktions-Tabelle
            end_marker: Ende der Transaktions-Tabelle
            
        Returns:
            Liste von Transaktionen
        """
        raise NotImplementedError("Subclass muss parse_transaction_table() implementieren!")
    
    def extract_endsaldo(self, text: str) -> Optional[float]:
        """
        Extrahiert Endsaldo aus PDF
        
        Muss von Subclass überschrieben werden!
        
        Args:
            text: PDF-Text
            
        Returns:
            Endsaldo als Float oder None
        """
        raise NotImplementedError("Subclass muss extract_endsaldo() implementieren!")
    
    def parse(self) -> List[Transaction]:
        """
        Standard-Parse-Methode
        
        Wird von Subclass überschrieben, aber kann als Vorlage dienen
        """
        raise NotImplementedError("Subclass muss parse() implementieren!")
