#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HypoVereinsbank PDF Parser fÃ¼r Bankenspiegel 3.0
================================================
Parser fÃ¼r HypoVereinsbank KontoauszÃ¼ge (PDF)

Format:
    DD.MM.YYYY DD.MM.YYYY Transaktionstyp Betrag EUR
    Verwendungszweck Zeile 2
    Verwendungszweck Zeile 3

Features:
- Betrag steht AM ENDE der Buchungszeile
- Mehrzeiliger Verwendungszweck
- IBAN-Extraktion

Author: Claude AI
Version: 3.0
Date: 2025-11-06
"""

import pdfplumber
import re
import logging
from typing import List
from .base_parser import BaseParser, Transaction

logger = logging.getLogger(__name__)


class HypovereinsbankParser(BaseParser):
    """
    Parser fÃ¼r HypoVereinsbank KontoauszÃ¼ge
    
    Format-Beispiel:
        01.01.2025 02.01.2025 SEPA-Ãœberweisung 1.234,56 EUR
        Max Mustermann
        Verwendungszweck
        
    Besonderheiten:
    - Betrag steht DIREKT in der Buchungszeile am Ende
    - Format: DD.MM.YYYY DD.MM.YYYY TEXT BETRAG EUR
    - Verwendungszweck oft mehrzeilig in Folgezeilen
    
    Usage:
        parser = HypovereinsbankParser('path/to/hypovereinsbank.pdf')
        transactions = parser.parse()
    """
    
    @property
    def bank_name(self) -> str:
        return "HypoVereinsbank"
    
    def parse(self) -> List[Transaction]:
        """
        Parst HypoVereinsbank PDF und extrahiert Transaktionen
        
        Returns:
            Liste von Transaction-Objekten
        """
        logger.info(f"ðŸ“„ Parse {self.bank_name}: {self.pdf_path.name}")
        
        try:
            with pdfplumber.open(str(self.pdf_path)) as pdf:
                # IBAN aus erster Seite
                if pdf.pages:
                    first_text = pdf.pages[0].extract_text()
                    self.iban = self._extract_iban_hypovereinsbank(first_text)
                
                if not self.iban:
                    logger.warning(f"âš ï¸ Keine IBAN gefunden in {self.pdf_path.name}")
                
                # Transaktionen von allen Seiten parsen
                all_transactions = []
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    
                    if not text:
                        continue
                    
                    page_transactions = self._parse_page(text, page_num)
                    all_transactions.extend(page_transactions)
                
                self.transactions = all_transactions
                
                # Zusammenfassung loggen
                self.log_summary()
                
                return self.transactions
        
        except Exception as e:
            logger.error(f"âŒ Fehler beim Parsen: {e}")
            self.errors.append(str(e))
            return []
    
    def _extract_iban_hypovereinsbank(self, text: str) -> str:
        """
        Extrahiert IBAN aus HypoVereinsbank PDF
        
        Format: "IBAN DE89700222000020029293"
        """
        pattern = r'IBAN\s+(DE\d{20})'
        match = re.search(pattern, text)
        
        if match:
            iban = match.group(1)
            logger.debug(f"IBAN gefunden: {iban}")
            return iban
        
        # Fallback: Normales IBAN-Pattern
        return self.extract_iban(text)
    
    def _parse_page(self, text: str, page_num: int) -> List[Transaction]:
        """
        Parst Transaktionen von einer Seite
        
        HypoVereinsbank Format (WICHTIG!):
            DD.MM.YYYY DD.MM.YYYY BUCHUNGSTEXT BETRAG EUR
            
        Betrag steht AM ENDE der Zeile! Nicht in Folgezeilen!
        """
        transactions = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Pattern: Buchungszeile mit Betrag am Ende
            # DD.MM.YYYY DD.MM.YYYY TEXT BETRAG EUR
            pattern = r'^(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\.\d{2}\.\d{4})\s+(.+?)\s+([-]?\d{1,3}(?:\.\d{3})*,\d{2})\s+EUR\s*$'
            
            match = re.match(pattern, line)
            
            if match:
                buchungsdatum_str = match.group(1)
                valutadatum_str = match.group(2)
                transaktionstyp = match.group(3).strip()
                betrag_str = match.group(4)
                
                # Datum parsen
                buchungsdatum = self.parse_german_date(buchungsdatum_str)
                valutadatum = self.parse_german_date(valutadatum_str)
                
                if not buchungsdatum or not valutadatum:
                    logger.warning(f"âš ï¸ UngÃ¼ltiges Datum: {buchungsdatum_str} / {valutadatum_str}")
                    i += 1
                    continue
                
                # Betrag parsen
                betrag = self.parse_german_amount(betrag_str)
                
                # Sammle Verwendungszweck aus Folgezeilen
                verwendungszweck_lines = [transaktionstyp]
                i += 1
                
                # Sammle alle Zeilen bis zur nÃ¤chsten Buchung
                while i < len(lines):
                    next_line = lines[i].strip()
                    
                    # Stopp wenn nÃ¤chste Buchungszeile beginnt
                    if re.match(r'^\d{2}\.\d{2}\.\d{4}\s+\d{2}\.\d{2}\.\d{4}', next_line):
                        break
                    
                    # Stopp bei Seitenumbruch oder Footer
                    if not next_line or 'Seite' in next_line or 'https://' in next_line:
                        i += 1
                        break
                    
                    # Normale Verwendungszweck-Zeile
                    if next_line:
                        verwendungszweck_lines.append(next_line)
                    
                    i += 1
                
                # Verwendungszweck zusammensetzen
                verwendungszweck = ' '.join(verwendungszweck_lines)
                verwendungszweck = self.clean_text(verwendungszweck)
                verwendungszweck = self.truncate_text(verwendungszweck, 500)
                
                # Transaktion erstellen
                transaction = Transaction(
                    buchungsdatum=buchungsdatum,
                    valutadatum=valutadatum,
                    verwendungszweck=verwendungszweck,
                    betrag=betrag,
                    iban=self.iban
                )
                transactions.append(transaction)
                logger.debug(f"âœ“ Transaktion (S.{page_num}): {buchungsdatum_str} | {betrag:.2f} EUR")
                
            else:
                i += 1
        
        return transactions


# FÃ¼r Direktaufruf / Testing
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python hypovereinsbank_parser.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    try:
        parser = HypovereinsbankParser(pdf_path)
        transactions = parser.parse()
        
        print(f"\n{'='*70}")
        print(f"ERGEBNIS")
        print(f"{'='*70}")
        print(f"Transaktionen: {len(transactions)}")
        
        if transactions:
            print(f"\nErste 5 Transaktionen:")
            for i, t in enumerate(transactions[:5], 1):
                print(f"{i}. {t}")
            
            # Suche nach spezifischen Keywords (fÃ¼r Testing)
            keywords = ['AMAZON', 'EDEKA', 'SHELL']
            for keyword in keywords:
                matching = [t for t in transactions if keyword in t.verwendungszweck.upper()]
                if matching:
                    print(f"\n{keyword} Transaktionen: {len(matching)}")
                    for t in matching[:2]:
                        print(f"  - {t.buchungsdatum} | {t.betrag:,.2f} EUR | {t.verwendungszweck[:60]}")
        
        stats = parser.get_statistics()
        print(f"\nStatistiken:")
        print(f"  Anzahl: {stats['count']}")
        print(f"  Summe: {stats['total_amount']:,.2f} EUR")
        print(f"  Zeitraum: {stats['date_range']}")
        print(f"  IBAN: {stats['has_iban']}")
        
    except Exception as e:
        print(f"Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
