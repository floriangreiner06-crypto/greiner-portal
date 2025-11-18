#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genobank Online-Banking Parser (Version 1.0)
==============================================

Spezialisierter Parser für Genobank Online-Banking Exports.
Format: "Umsätze" mit "(Endsaldo)" - ähnlich Sparkasse.

Beispiel:
BIC GENODEF1DGV Datum 20.10.2025
IBAN DE68741900000001501500
Umsätze
Filterparameter 17.10.2025 - 17.10.2025
VR-Giro Business
(Endsaldo)
+136.434,69EUR

Autor: Claude (Tag 60)
Datum: 2025-11-18
"""

import re
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import pdfplumber

from .base_parser import BaseParser, Transaction

logger = logging.getLogger(__name__)


class GenobankOnlineParser(BaseParser):
    """
    Parser für Genobank Online-Banking Umsätze.
    
    Format: Online-Banking Export (nicht klassischer Kontoauszug)
    Endsaldo: "(Endsaldo)\n+BETRAG EUR"
    """
    
    def __init__(self, pdf_path: str):
        super().__init__(pdf_path)
        self.endsaldo: Optional[float] = None
    
    @property
    def bank_name(self) -> str:
        """Name der Bank"""
        return "Genobank"
    
    def extract_iban(self) -> Optional[str]:
        """Extrahiert IBAN aus PDF-Header"""
        try:
            with pdfplumber.open(str(self.pdf_path)) as pdf:
                if not pdf.pages:
                    return None
                
                text = pdf.pages[0].extract_text()[:1000]
                
                # Pattern: IBAN DE + 20 Ziffern
                pattern = r'IBAN\s*(DE\d{2}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{2})'
                match = re.search(pattern, text)
                
                if match:
                    iban = match.group(1).replace(' ', '')
                    logger.debug(f"IBAN extrahiert: {iban}")
                    return iban
                
                return None
                
        except Exception as e:
            logger.error(f"Fehler bei IBAN-Extraktion: {e}")
            return None
    
    def extract_endsaldo(self, text: str) -> Optional[float]:
        """
        Extrahiert Endsaldo aus Online-Banking Export.
        
        Format: "(Endsaldo)\n+136.434,69EUR"
        """
        try:
            # Pattern: (Endsaldo) gefolgt von Betrag
            pattern = r'\(Endsaldo\)\s*([+-]?[\d.,]+)\s*EUR'
            
            match = re.search(pattern, text, re.IGNORECASE)
            
            if match:
                betrag_str = match.group(1)
                # Parse Betrag (deutsches Format)
                betrag_str = betrag_str.replace('.', '').replace(',', '.')
                endsaldo = float(betrag_str)
                
                logger.info(f"Endsaldo: {endsaldo:.2f} EUR")
                return endsaldo
            
            logger.debug("Kein Endsaldo gefunden")
            return None
            
        except Exception as e:
            logger.error(f"Fehler bei Endsaldo-Extraktion: {e}")
            return None
    
    def parse(self) -> List[Transaction]:
        """
        Parst Genobank Online-Banking PDF.
        
        Returns:
            Liste von Transaction-Objekten
        """
        transactions = []
        
        try:
            with pdfplumber.open(str(self.pdf_path)) as pdf:
                # Sammle Text
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                
                if not full_text:
                    logger.warning(f"Kein Text in {self.pdf_path.name}")
                    return []
                
                # IBAN extrahieren
                self.iban = self.extract_iban()
                
                # Endsaldo extrahieren
                self.endsaldo = self.extract_endsaldo(full_text)
                
                # Parse Transaktionen
                lines = full_text.split('\n')
                
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    # Suche nach Betragszeile: "+1.002,90 EUR" oder "-500,00 EUR"
                    betrag_match = re.search(r'([+-][\d.,]+)\s+EUR$', line)
                    
                    if betrag_match:
                        betrag_str = betrag_match.group(1)
                        
                        # Parse Betrag
                        betrag_clean = betrag_str.replace('.', '').replace(',', '.')
                        try:
                            betrag = float(betrag_clean)
                        except ValueError:
                            i += 1
                            continue
                        
                        # Suche Datum (in gleicher oder vorherigen Zeilen)
                        buchungsdatum = None
                        
                        # Prüfe Zeile mit Betrag
                        datum_match = re.search(r'\b(\d{2}\.\d{2}\.\d{4})\b', line)
                        if datum_match:
                            try:
                                buchungsdatum = datetime.strptime(datum_match.group(1), '%d.%m.%Y').date()
                            except:
                                pass
                        
                        # Falls nicht gefunden, prüfe vorherige Zeilen
                        if not buchungsdatum:
                            for j in range(max(0, i-3), i):
                                datum_match = re.search(r'\b(\d{2}\.\d{2}\.\d{4})\b', lines[j])
                                if datum_match:
                                    try:
                                        buchungsdatum = datetime.strptime(datum_match.group(1), '%d.%m.%Y').date()
                                        break
                                    except:
                                        pass
                        
                        # Sammle Verwendungszweck
                        verwendungszweck_lines = []
                        
                        for j in range(max(0, i-5), i):
                            prev_line = lines[j].strip()
                            
                            # Skip Header/Footer
                            skip_patterns = [
                                'Umsätze', 'Filterparameter', 'Buchungsdatum',
                                'IBAN', 'BIC', 'Kontoinhaber', 'Datum', 'Uhrzeit',
                                'Endsaldo', 'VR-Giro'
                            ]
                            
                            if any(skip in prev_line for skip in skip_patterns):
                                continue
                            
                            if not prev_line:
                                continue
                            
                            # Skip Datumszeilen
                            if re.match(r'^\d{2}\.\d{2}\.\d{4}', prev_line):
                                continue
                            
                            verwendungszweck_lines.append(prev_line)
                        
                        verwendungszweck = ' '.join(verwendungszweck_lines[-3:])
                        
                        if buchungsdatum and verwendungszweck:
                            transaction = Transaction(
                                buchungsdatum=buchungsdatum,
                                valutadatum=buchungsdatum,
                                verwendungszweck=verwendungszweck[:500],
                                betrag=betrag,
                                iban=self.iban
                            )
                            
                            transactions.append(transaction)
                            
                            logger.debug(
                                f"TX: {buchungsdatum} | {betrag:>10.2f} EUR | "
                                f"{verwendungszweck[:50]}..."
                            )
                    
                    i += 1
                
                logger.info(
                    f"{self.pdf_path.name}: {len(transactions)} Transaktionen"
                    + (f", Endsaldo: {self.endsaldo:.2f} EUR" if self.endsaldo else "")
                )
                
        except Exception as e:
            logger.error(f"Fehler beim Parsen von {self.pdf_path}: {e}", exc_info=True)
            return []
        
        return transactions


# Convenience-Funktion
def parse_genobank_online(pdf_path: str) -> List[Transaction]:
    """
    Convenience-Funktion zum direkten Parsen.
    
    Args:
        pdf_path: Pfad zur PDF-Datei
    
    Returns:
        Liste von Transaction-Objekten
    """
    parser = GenobankOnlineParser(pdf_path)
    return parser.parse()
