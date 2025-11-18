#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genobank Tagesauszug Parser
============================
Parser für Genobank-Tagesauszüge (alle Monate, alle Jahre)

PDF-Format Merkmale:
- IBAN: "IBAN DE27741900000000057908" (ohne Leerzeichen)
- Startsaldo: "(Startsaldo) +123.456,78 EUR" (Betrag auf nächster Zeile)
- Endsaldo: "(Endsaldo) +190.438,80 EUR" (Betrag auf nächster Zeile)
- Tägliche Auszüge (nicht monatlich)

Verwendet für Konten:
- 57908 (DE27741900000000057908)
- 1501500 (DE68741900000001501500)
- Weitere Konten mit diesem Format

Beispiel-Dateinamen:
- "Genobank Auszug Auto Greiner 17.11.25.pdf"
- "Genobank Auszug Auto Greiner 05.09.25.pdf"

Author: Claude AI
Version: 1.0
Date: 2025-11-18
"""

from parsers.genobank.genobank_base import GenobankBaseParser, Transaction
from typing import List, Optional
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class GenobankTagesauszugParser(GenobankBaseParser):
    """
    Parser für Genobank-Tagesauszüge
    
    Erkennt:
    - IBAN ohne Leerzeichen (Format: DE + 20 Ziffern)
    - Startsaldo: "(Startsaldo)" + Betrag auf nächster Zeile
    - Endsaldo: "(Endsaldo)" + Betrag auf nächster Zeile
    - Transaktionen zwischen Startsaldo und Endsaldo
    
    Funktioniert für ALLE Monate und Jahre!
    """
    
    def __init__(self, pdf_path: str):
        super().__init__(pdf_path)
        self.startsaldo: Optional[float] = None
        self.endsaldo: Optional[float] = None
    
    def extract_endsaldo(self, text: str) -> Optional[float]:
        """
        Extrahiert Endsaldo aus Tagesauszug
        
        Format: "(Endsaldo)" auf einer Zeile, Betrag auf nächster Zeile
        Beispiel:
            Zeile N:   "(Endsaldo)"
            Zeile N+1: "+190.438,80 EUR" oder "+190.438,80EUR"
        
        Args:
            text: PDF-Text
            
        Returns:
            Endsaldo als Float oder None
        """
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Suche "(Endsaldo)" und hole nächste Zeile
            if '(Endsaldo)' in line:
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    # Pattern: +190.438,80 EUR oder -123.456,78 EUR
                    # OHNE Leerzeichen vor EUR möglich: +190.438,80EUR
                    match = re.search(r'([+\-]?[\d.,]+)\s*EUR', next_line)
                    if match:
                        betrag_str = match.group(1).replace('+', '').strip()
                        try:
                            endsaldo = self.parse_german_amount(betrag_str)
                            logger.info(f"✓ Endsaldo gefunden: {endsaldo:,.2f} EUR")
                            return endsaldo
                        except Exception as e:
                            logger.warning(f"⚠️ Fehler beim Endsaldo-Parsing: {e}")
        
        logger.warning("⚠️ Kein Endsaldo gefunden")
        return None
    
    def extract_startsaldo(self, text: str) -> Optional[float]:
        """
        Extrahiert Startsaldo aus Tagesauszug
        
        Format: "(Startsaldo)" auf einer Zeile, Betrag auf nächster Zeile
        
        Args:
            text: PDF-Text
            
        Returns:
            Startsaldo als Float oder None
        """
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Suche "(Startsaldo)" und hole nächste Zeile
            if '(Startsaldo)' in line:
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    match = re.search(r'([+\-]?[\d.,]+)\s*EUR', next_line)
                    if match:
                        betrag_str = match.group(1).replace('+', '').strip()
                        try:
                            startsaldo = self.parse_german_amount(betrag_str)
                            logger.debug(f"✓ Startsaldo gefunden: {startsaldo:,.2f} EUR")
                            return startsaldo
                        except Exception as e:
                            logger.warning(f"⚠️ Fehler beim Startsaldo-Parsing: {e}")
        
        return None
    
    def parse(self) -> List[Transaction]:
        """
        Parst Tagesauszug und extrahiert Transaktionen
        
        Returns:
            Liste von Transaction-Objekten
        """
        logger.info(f"📄 Parse Tagesauszug: {self.pdf_path.name}")
        
        # 1. PDF-Text extrahieren
        text = self.extract_text_from_pdf()
        if not text:
            logger.error("❌ Kein Text in PDF gefunden")
            return []
        
        # 2. IBAN extrahieren
        self.iban = self.extract_iban_genobank(text)
        if not self.iban:
            logger.error("❌ Keine IBAN gefunden")
            self.errors.append("Keine IBAN gefunden")
            return []
        
        # 3. Startsaldo extrahieren
        self.startsaldo = self.extract_startsaldo(text)
        
        # 4. Endsaldo extrahieren
        self.endsaldo = self.extract_endsaldo(text)
        
        # 5. Transaktionen extrahieren
        self.transactions = self._parse_transactions(text)
        
        # 6. IBAN zu allen Transaktionen hinzufügen
        for tx in self.transactions:
            tx.iban = self.iban
        
        # 7. Summary loggen
        self.log_summary()
        
        return self.transactions
    
    def _parse_transactions(self, text: str) -> List[Transaction]:
        """
        Extrahiert Transaktionen aus Text
        
        Format: Buchungsdatum | Valutadatum | Verwendungszweck | Betrag
        
        Args:
            text: PDF-Text
            
        Returns:
            Liste von Transaktionen
        """
        transactions = []
        lines = text.split('\n')
        
        # Finde Start der Transaktions-Tabelle (nach Startsaldo)
        in_transaction_section = False
        
        for line in lines:
            # Start: Nach "(Startsaldo)"
            if '(Startsaldo)' in line:
                in_transaction_section = True
                continue
            
            # Ende: Bei "(Endsaldo)"
            if '(Endsaldo)' in line:
                in_transaction_section = False
                break
            
            if not in_transaction_section:
                continue
            
            # Parse Transaktions-Zeile
            # Format: DD.MM.YYYY DD.MM.YYYY Verwendungszweck +/-Betrag EUR
            # Beispiel: "11.11.2025 11.11.2025 TV Landau | Re. 123 +98,90 EUR"
            
            # Pattern für Datum am Anfang
            date_pattern = r'^(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\.\d{2}\.\d{4})\s+'
            match = re.match(date_pattern, line)
            
            if match:
                buchungsdatum_str = match.group(1)
                valutadatum_str = match.group(2)
                
                # Rest der Zeile nach Datum
                rest = line[match.end():].strip()
                
                # Betrag am Ende finden (Format: +/-123.456,78 EUR)
                betrag_pattern = r'([+\-]?[\d.,]+)\s*EUR\s*$'
                betrag_match = re.search(betrag_pattern, rest)
                
                if betrag_match:
                    betrag_str = betrag_match.group(1).replace('+', '').strip()
                    
                    # Verwendungszweck ist alles zwischen Datum und Betrag
                    verwendungszweck = rest[:betrag_match.start()].strip()
                    
                    # Parse Datum und Betrag
                    try:
                        buchungsdatum = self.parse_german_date(buchungsdatum_str)
                        valutadatum = self.parse_german_date(valutadatum_str)
                        betrag = self.parse_german_amount(betrag_str)
                        
                        if buchungsdatum and valutadatum:
                            tx = Transaction(
                                buchungsdatum=buchungsdatum,
                                valutadatum=valutadatum,
                                verwendungszweck=verwendungszweck,
                                betrag=betrag
                            )
                            transactions.append(tx)
                            logger.debug(f"✓ Transaktion: {tx}")
                    
                    except Exception as e:
                        logger.warning(f"⚠️ Fehler beim Parsen: {line} - {e}")
                        self.errors.append(f"Parse-Fehler: {line[:50]}")
        
        logger.info(f"✓ {len(transactions)} Transaktionen gefunden")
        return transactions
