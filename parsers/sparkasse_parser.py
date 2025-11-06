#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sparkasse PDF Parser fÃ¼r Bankenspiegel 3.0
==========================================
Parser fÃ¼r Sparkasse KontoauszÃ¼ge (PDF)

Format:
    DD.MM.YYYY Verwendungszweck... Betrag

Features:
- Mehrzeiliger Verwendungszweck
- IBAN-Extraktion
- Duplikats-Check vorbereitet

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


class SparkasseParser(BaseParser):
    """
    Parser fÃ¼r Sparkasse KontoauszÃ¼ge
    
    Format-Beispiel:
        01.01.2025 SEPA-Ãœberweisung Max Mustermann 1.234,56
        Verwendungszweck Zeile 2
        Verwendungszweck Zeile 3
        
    Usage:
        parser = SparkasseParser('path/to/sparkasse.pdf')
        transactions = parser.parse()
    """
    
    @property
    def bank_name(self) -> str:
        return "Sparkasse"
    
    def parse(self) -> List[Transaction]:
        """
        Parst Sparkasse PDF und extrahiert Transaktionen
        
        Returns:
            Liste von Transaction-Objekten
        """
        logger.info(f"ðŸ“„ Parse {self.bank_name}: {self.pdf_path.name}")
        
        try:
            with pdfplumber.open(str(self.pdf_path)) as pdf:
                # Text von allen Seiten sammeln
                full_text = self._extract_full_text(pdf)
                
                # IBAN extrahieren
                self.iban = self.extract_iban(full_text)
                
                if not self.iban:
                    logger.warning(f"âš ï¸ Keine IBAN gefunden in {self.pdf_path.name}")
                
                # Transaktionen parsen
                self.transactions = self._parse_transactions(full_text)
                
                # Zusammenfassung loggen
                self.log_summary()
                
                return self.transactions
        
        except Exception as e:
            logger.error(f"âŒ Fehler beim Parsen: {e}")
            self.errors.append(str(e))
            return []
    
    def _extract_full_text(self, pdf) -> str:
        """Extrahiert Text von allen Seiten"""
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        return full_text
    
    def _parse_transactions(self, full_text: str) -> List[Transaction]:
        """
        Parst Transaktionen aus dem Text
        
        Sparkasse-Format:
            DD.MM.YYYY Text... Betrag
            
        Betrag steht AM ENDE der Zeile, davor steht der Verwendungszweck.
        Folgezeilen ohne Datum gehÃ¶ren zum Verwendungszweck.
        """
        transactions = []
        lines = full_text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Suche nach Zeile die mit Datum beginnt
            # Pattern: DD.MM.YYYY rest_der_zeile
            date_match = re.match(r'^(\d{2}\.\d{2}\.\d{4})(.+)', line)
            
            if date_match:
                datum = date_match.group(1)
                rest = date_match.group(2).strip()
                
                # Ãœberspringe "Kontostand am..." Zeilen
                if 'Kontostand am' in rest or not rest:
                    i += 1
                    continue
                
                # Suche Betrag am Ende der Zeile
                # Pattern: Betrag mit Tausender-Punkt und Komma
                betrag_match = re.search(r'([-]?\d{1,3}(?:\.\d{3})*,\d{2})$', line)
                
                if betrag_match:
                    betrag_str = betrag_match.group(1)
                    betrag = self.parse_german_amount(betrag_str)
                    
                    # Verwendungszweck = alles zwischen Datum und Betrag
                    verwendungszweck = line[len(datum):betrag_match.start()].strip()
                    
                    # Sammle zusÃ¤tzliche Zeilen (Verwendungszweck kann mehrzeilig sein)
                    zusatz_lines = []
                    j = i + 1
                    
                    while j < len(lines) and j < i + 10:  # Max 10 Zeilen vorausschauen
                        next_line = lines[j].strip()
                        
                        # Stopp wenn nÃ¤chste Transaktion beginnt
                        if re.match(r'^\d{2}\.\d{2}\.\d{4}', next_line):
                            break
                        
                        # Stopp bei leeren Zeilen oder Footer
                        if not next_line or 'Sparkasse' in next_line or 'Vorstand' in next_line:
                            break
                        
                        zusatz_lines.append(next_line)
                        j += 1
                    
                    # Verwendungszweck zusammensetzen
                    if zusatz_lines:
                        verwendungszweck = verwendungszweck + " " + " ".join(zusatz_lines)
                    
                    # Text sÃ¤ubern und kÃ¼rzen
                    verwendungszweck = self.clean_text(verwendungszweck)
                    verwendungszweck = self.truncate_text(verwendungszweck, 500)
                    
                    # Datum konvertieren
                    buchungsdatum = self.parse_german_date(datum)
                    valutadatum = buchungsdatum  # Sparkasse hat oft nur ein Datum
                    
                    if buchungsdatum:
                        transaction = Transaction(
                            buchungsdatum=buchungsdatum,
                            valutadatum=valutadatum,
                            verwendungszweck=verwendungszweck,
                            betrag=betrag,
                            iban=self.iban
                        )
                        transactions.append(transaction)
                        logger.debug(f"âœ“ Transaktion: {datum} | {betrag:.2f} EUR")
                    else:
                        self.errors.append(f"UngÃ¼ltiges Datum: {datum}")
                    
                    # Springe zu nÃ¤chster mÃ¶glichen Transaktion
                    i = j
                    continue
            
            i += 1
        
        logger.info(f"âœ… {self.bank_name}: {len(transactions)} Transaktionen gefunden")
        return transactions


# FÃ¼r Direktaufruf / Testing
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python sparkasse_parser.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    try:
        parser = SparkasseParser(pdf_path)
        transactions = parser.parse()
        
        print(f"\n{'='*70}")
        print(f"ERGEBNIS")
        print(f"{'='*70}")
        print(f"Transaktionen: {len(transactions)}")
        
        if transactions:
            print(f"\nErste 5 Transaktionen:")
            for i, t in enumerate(transactions[:5], 1):
                print(f"{i}. {t}")
        
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
