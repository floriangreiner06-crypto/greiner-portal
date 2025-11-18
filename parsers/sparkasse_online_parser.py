#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sparkasse Online-Banking Parser (Version 2.0)
==============================================

Spezialisierter Parser für Sparkasse "Umsätze - Druckansicht" PDFs.
Dies ist das Online-Banking Export-Format, NICHT klassische Kontoauszüge.

PDF-Format:
-----------
Umsätze - Druckansicht
Sichteinlagen
DE63 7415 0000 0760 0364 67 24,35 EUR *
AUTOHAUS GREINER GMBH & CO. KG
1 Umsatz vom 01.10.2025 bis 01.10.2025
Kontostand am 01.10.2025: 15.727,94 EUR*

BUCHUNGWERTSTELLUNG
Name/Beschreibung
Details... 01.10.202501.10.2025 +14.490,00 EUR

Pattern: DD.MM.YYYYDD.MM.YYYY ±BETRAG EUR
         (Buchungsdatum direkt mit Wertstellung ohne Leerzeichen)

Autor: Claude (Tag 60) - basierend auf funktionierendem Backup
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


class SparkasseOnlineParser(BaseParser):
    """
    Parser für Sparkasse Online-Banking Umsätze (Druckansicht).
    
    Eigenschaften:
    - Format: Online-Banking Export (nicht klassischer Kontoauszug)
    - Pattern: DD.MM.YYYYDD.MM.YYYY ±BETRAG EUR
    - Endsaldo-Erkennung: "Kontostand am DD.MM.YYYY: BETRAG EUR*"
    - IBAN-Extraktion aus Header
    """
    
    def __init__(self, pdf_path: str):
        super().__init__(pdf_path)
        self.endsaldo: Optional[float] = None
        self.kontostand_datum: Optional[str] = None
        self.anfangssaldo: Optional[float] = None
    
    @property
    def bank_name(self) -> str:
        """Name der Bank"""
        return "Sparkasse"
    
    def extract_iban(self) -> Optional[str]:
        """
        Extrahiert IBAN aus PDF-Header.
        
        Format im PDF: DE63 7415 0000 0760 0364 67 24,35 EUR *
        """
        try:
            with pdfplumber.open(str(self.pdf_path)) as pdf:
                if not pdf.pages:
                    return None
                
                # Erste Seite, erste 1000 Zeichen
                text = pdf.pages[0].extract_text()[:1000]
                
                # Pattern: DE + 20 Ziffern (mit optionalen Leerzeichen)
                pattern = r'DE\d{2}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{2}'
                match = re.search(pattern, text)
                
                if match:
                    iban = match.group().replace(' ', '')
                    logger.debug(f"IBAN extrahiert: {iban}")
                    return iban
                
                logger.warning(f"Keine IBAN in {self.pdf_path.name} gefunden")
                return None
                
        except Exception as e:
            logger.error(f"Fehler bei IBAN-Extraktion: {e}")
            return None
    
    def extract_endsaldo(self, text: str) -> Optional[float]:
        """
        Extrahiert Endsaldo aus PDF.
        
        Format: "Kontostand am 01.10.2025: 15.727,94 EUR*"
        """
        try:
            # Pattern: Kontostand am DD.MM.YYYY: BETRAG EUR*
            pattern = r'Kontostand\s+am\s+(\d{2}\.\d{2}\.\d{4}):\s*([-+]?[\d.,]+)\s*EUR'
            
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            if matches:
                # Nimm letzten Kontostand (= Endsaldo)
                datum_str, betrag_str = matches[-1]
                
                # Parse Betrag
                betrag_str = betrag_str.replace('.', '').replace(',', '.')
                endsaldo = float(betrag_str)
                
                self.kontostand_datum = datum_str
                logger.info(f"Endsaldo: {endsaldo:.2f} EUR (am {datum_str})")
                
                # Anfangssaldo ist der erste Kontostand
                if len(matches) > 1:
                    anfang_datum, anfang_betrag = matches[0]
                    self.anfangssaldo = float(anfang_betrag.replace('.', '').replace(',', '.'))
                    logger.debug(f"Anfangssaldo: {self.anfangssaldo:.2f} EUR (am {anfang_datum})")
                
                return endsaldo
            
            logger.warning("Kein Endsaldo im PDF gefunden")
            return None
            
        except Exception as e:
            logger.error(f"Fehler bei Endsaldo-Extraktion: {e}")
            return None
    
    def parse(self) -> List[Transaction]:
        """
        Parst Sparkasse Online-Banking PDF.
        
        Returns:
            Liste von Transaction-Objekten
        """
        transactions = []
        
        try:
            with pdfplumber.open(str(self.pdf_path)) as pdf:
                # Sammle Text aller Seiten
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                
                if not full_text:
                    logger.warning(f"Kein Text in {self.pdf_path.name} extrahiert (möglicherweise gescanntes PDF)")
                    return []
                
                # Prüfe ob es eine Mitteilung ohne Umsätze ist
                if any(phrase in full_text for phrase in [
                    'Keine Suchergebnisse',
                    'keine Umsätze',
                    '0 Umsätze'
                ]):
                    logger.info(f"{self.pdf_path.name}: Mitteilung ohne Umsätze (wird übersprungen)")
                    # Endsaldo trotzdem extrahieren
                    self.iban = self.extract_iban()
                    self.endsaldo = self.extract_endsaldo(full_text)
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
                    
                    # Suche nach Transaktions-Pattern
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
                        except ValueError as e:
                            logger.debug(f"Ungültiges Datum: {e}")
                            i += 1
                            continue
                        
                        # Parse Betrag
                        betrag_str = betrag_str.replace('.', '').replace(',', '.')
                        try:
                            betrag = float(betrag_str)
                        except ValueError:
                            logger.debug(f"Ungültiger Betrag: {betrag_str}")
                            i += 1
                            continue
                        
                        # Sammle Verwendungszweck (vorherige Zeilen)
                        verwendungszweck_lines = []
                        
                        # Gehe 1-5 Zeilen zurück und sammle Text
                        for j in range(max(0, i-5), i):
                            prev_line = lines[j].strip()
                            
                            # Skip Header/Footer-Zeilen
                            skip_patterns = [
                                'Umsätze', 'Kontostand', 'BUCHUNG', 'WERTSTELLUNG',
                                'Sichteinlagen', 'Sparkasse', 'Druckaufbereitung',
                                'angezeigte Kontostand', 'rechtsverbindlich'
                            ]
                            
                            if any(skip in prev_line for skip in skip_patterns):
                                continue
                            
                            # Skip Leerzeilen
                            if not prev_line:
                                continue
                            
                            # Skip Zeilen mit nur Datum/Betrag
                            if re.match(r'^\d{2}\.\d{2}\.\d{4}', prev_line):
                                continue
                            
                            # Skip IBAN-Zeilen
                            if re.match(r'^DE\d{2}', prev_line):
                                continue
                            
                            verwendungszweck_lines.append(prev_line)
                        
                        # Verwendungszweck zusammensetzen (max letzte 3 Zeilen)
                        verwendungszweck = ' '.join(verwendungszweck_lines[-3:])
                        
                        # Nur Transaktionen mit Verwendungszweck
                        if verwendungszweck:
                            # Erstelle Transaction mit korrekten Feldern
                            transaction = Transaction(
                                buchungsdatum=buchungsdatum,
                                valutadatum=valutadatum,
                                verwendungszweck=verwendungszweck[:500],
                                betrag=betrag,
                                iban=self.iban
                            )
                            
                            transactions.append(transaction)
                            
                            logger.debug(
                                f"TX: {transaction.buchungsdatum} | {betrag:>10.2f} EUR | "
                                f"{verwendungszweck[:50]}..."
                            )
                    
                    i += 1
                
                logger.info(
                    f"{self.pdf_path.name}: {len(transactions)} Transaktionen, "
                    f"Endsaldo: {self.endsaldo:.2f} EUR" if self.endsaldo else "kein Endsaldo"
                )
                
        except Exception as e:
            logger.error(f"Fehler beim Parsen von {self.pdf_path}: {e}", exc_info=True)
            return []
        
        return transactions
    
    def __repr__(self):
        return (
            f"SparkasseOnlineParser("
            f"pdf='{self.pdf_path.name}', "
            f"iban='{self.iban}', "
            f"endsaldo={self.endsaldo}, "
            f"transactions={len(self.parse())})"
        )


# Convenience-Funktion für direkten Import
def parse_sparkasse_online(pdf_path: str) -> List[Transaction]:
    """
    Convenience-Funktion zum direkten Parsen.
    
    Args:
        pdf_path: Pfad zur PDF-Datei
    
    Returns:
        Liste von Transaction-Objekten
    """
    parser = SparkasseOnlineParser(pdf_path)
    return parser.parse()
