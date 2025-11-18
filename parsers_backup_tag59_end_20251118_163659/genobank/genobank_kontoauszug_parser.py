#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genobank Kontoauszug Parser
============================
Parser für Genobank-Kontoauszüge (alle Monate, alle Jahre)

PDF-Format Merkmale:
- IBAN: "IBAN: DE96 7419 0000 1700 0579 08" (mit Leerzeichen und BIC)
- Endsaldo: "neuer Kontostand vom 30.09.2024  14.854,72 H"
  (H = Haben/positiv, S = Soll/negativ)
- Monatliche Auszüge (nicht täglich)

Verwendet für Konten:
- 1700057908 (Festgeld)
- 4700057908 (Darlehen)
- 22225 (Immo KK)
- 120057908 (KfW)
- 20057908 (Darlehen)
- Weitere Konten mit diesem Format

Beispiel-Dateinamen:
- "1700057908_2025_Nr.009_Kontoauszug_vom_2025.09.30_20251001065458.pdf"
- "4700057908_2025_Nr.077_Kontoauszug_vom_2025.09.30_20241001064954.pdf"

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


class GenobankKontoauszugParser(GenobankBaseParser):
    """
    Parser für Genobank-Kontoauszüge (monatlich)
    
    Erkennt:
    - IBAN mit Leerzeichen (Format: "IBAN: DE96 7419 0000...")
    - Endsaldo: "neuer Kontostand vom DD.MM.YYYY  Betrag H/S"
    - Transaktionen in Tabellen-Format
    
    Funktioniert für ALLE Monate und Jahre!
    """
    
    def __init__(self, pdf_path: str):
        super().__init__(pdf_path)
        self.endsaldo: Optional[float] = None
        self.endsaldo_datum: Optional[datetime] = None
    
    def extract_endsaldo(self, text: str) -> Optional[float]:
        """
        Extrahiert Endsaldo aus Kontoauszug
        
        Format: "neuer Kontostand vom 30.09.2024  14.854,72 H"
                "neuer Kontostand vom 30.09.2024  1.234,56 S"
        
        H = Haben (positiv)
        S = Soll (negativ)
        
        Args:
            text: PDF-Text
            
        Returns:
            Endsaldo als Float oder None
        """
        # Pattern: "neuer Kontostand vom DD.MM.YYYY  Betrag H/S"
        pattern = r'neuer Kontostand vom\s+(\d{2}\.\d{2}\.\d{4})\s+([\d.,]+)\s+([HS])'
        match = re.search(pattern, text)
        
        if match:
            datum_str = match.group(1)
            betrag_str = match.group(2)
            hs_flag = match.group(3)
            
            try:
                # Datum parsen
                self.endsaldo_datum = self.parse_german_date(datum_str)
                
                # Betrag parsen
                betrag = self.parse_german_amount(betrag_str)
                
                # H = Haben (positiv), S = Soll (negativ)
                if hs_flag == 'S':
                    betrag = -betrag
                
                logger.info(f"✓ Endsaldo gefunden: {betrag:,.2f} EUR (Datum: {datum_str}, {hs_flag})")
                return betrag
            
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Endsaldo-Parsing: {e}")
        
        logger.warning("⚠️ Kein Endsaldo gefunden")
        return None
    
    def parse(self) -> List[Transaction]:
        """
        Parst Kontoauszug und extrahiert Transaktionen
        
        Returns:
            Liste von Transaction-Objekten
        """
        logger.info(f"📄 Parse Kontoauszug: {self.pdf_path.name}")
        
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
        
        # 3. Endsaldo extrahieren
        self.endsaldo = self.extract_endsaldo(text)
        
        # 4. Transaktionen extrahieren
        self.transactions = self._parse_transactions(text)
        
        # 5. IBAN zu allen Transaktionen hinzufügen
        for tx in self.transactions:
            tx.iban = self.iban
        
        # 6. Summary loggen
        self.log_summary()
        
        return self.transactions
    
    def _parse_transactions(self, text: str) -> List[Transaction]:
        """
        Extrahiert Transaktionen aus Kontoauszug
        
        Format: Buchung | Valuta | Vorgang | Soll | Haben
        
        Args:
            text: PDF-Text
            
        Returns:
            Liste von Transaktionen
        """
        transactions = []
        lines = text.split('\n')
        
        # Finde Transaktions-Bereich
        # Start: Nach Header mit "Buchung", "Valuta", "Vorgang"
        # Ende: Vor "neuer Kontostand"
        
        in_transaction_section = False
        
        for line in lines:
            # Start: Zeile mit "Buchung" und "Valuta" (Tabellen-Header)
            if 'Buchung' in line and 'Valuta' in line and 'Vorgang' in line:
                in_transaction_section = True
                continue
            
            # Ende: Bei "neuer Kontostand"
            if 'neuer Kontostand' in line:
                in_transaction_section = False
                break
            
            if not in_transaction_section:
                continue
            
            # Parse Transaktions-Zeile
            # Format: DD.MM. DD.MM. Verwendungszweck [Soll] [Haben]
            # Beispiel: "01.09. 01.09. Überweisung von Konto 57908  1.234,56"
            
            # Pattern für Datum am Anfang (ohne Jahr!)
            date_pattern = r'^(\d{2}\.\d{2}\.)\s+(\d{2}\.\d{2}\.)\s+'
            match = re.match(date_pattern, line)
            
            if match:
                buchungsdatum_str = match.group(1)  # z.B. "01.09."
                valutadatum_str = match.group(2)
                
                # Rest der Zeile nach Datum
                rest = line[match.end():].strip()
                
                # Betrag am Ende finden (Format: 123.456,78)
                # Kann Soll ODER Haben sein
                betrag_pattern = r'([\d.,]+)\s*$'
                betrag_match = re.search(betrag_pattern, rest)
                
                if betrag_match:
                    betrag_str = betrag_match.group(1)
                    
                    # Verwendungszweck ist alles zwischen Datum und Betrag
                    verwendungszweck = rest[:betrag_match.start()].strip()
                    
                    # Bestimme ob Soll oder Haben
                    # Heuristik: Wenn "Lastschrift" oder "Überweisung an" -> Soll (negativ)
                    #            Wenn "Gutschrift" oder "Überweisung von" -> Haben (positiv)
                    betrag = self.parse_german_amount(betrag_str)
                    
                    if any(keyword in verwendungszweck.lower() for keyword in ['lastschrift', 'überweisung an', 'auszahlung']):
                        betrag = -abs(betrag)  # Negativ (Ausgang)
                    # Standard: Positiv (Eingang)
                    
                    # Jahr aus Endsaldo-Datum ableiten (falls vorhanden)
                    year = self.endsaldo_datum.year if self.endsaldo_datum else datetime.now().year
                    
                    # Parse Datum (ohne Jahr)
                    try:
                        buchungsdatum = self.parse_german_date(buchungsdatum_str, year=year)
                        valutadatum = self.parse_german_date(valutadatum_str, year=year)
                        
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
