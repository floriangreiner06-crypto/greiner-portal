#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Parser für Bankenspiegel 3.0
=================================
Abstract Base Class für Bank-PDF-Parser

Enthält:
- Transaction Dataclass
- BaseParser ABC mit gemeinsamen Hilfsfunktionen
- Standardisierte Methoden für alle Parser

Author: Claude AI
Version: 3.0
Date: 2025-11-06
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class Transaction:
    """
    Standardisierte Transaktion für alle Banken
    
    Attributes:
        buchungsdatum: Datum der Buchung
        valutadatum: Wertstellungsdatum
        verwendungszweck: Beschreibung der Transaktion
        betrag: Betrag (positiv = Eingang, negativ = Ausgang)
        iban: IBAN des Kontos (optional)
        konto_id: Konto-ID aus Datenbank (wird später gesetzt)
    """
    buchungsdatum: datetime
    valutadatum: datetime
    verwendungszweck: str
    betrag: float
    iban: Optional[str] = None
    konto_id: Optional[int] = None
    
    def __str__(self) -> str:
        return (f"{self.buchungsdatum.strftime('%d.%m.%Y')} | "
                f"{self.betrag:>10.2f} EUR | {self.verwendungszweck[:50]}")


class BaseParser(ABC):
    """
    Abstract Base Class für Bank-PDF-Parser
    
    Bietet gemeinsame Funktionalität für alle Parser:
    - IBAN-Extraktion
    - Datums-Parsing
    - Betrags-Parsing (deutsch: 1.234,56)
    - Text-Cleaning
    - Statistiken
    
    Subclasses müssen implementieren:
    - bank_name: Property mit Bankname
    - parse(): Methode zum Parsen der PDF
    """
    
    def __init__(self, pdf_path: str):
        """
        Initialisiert Parser
        
        Args:
            pdf_path: Pfad zur PDF-Datei
        """
        self.pdf_path = Path(pdf_path)
        self.iban: Optional[str] = None
        self.transactions: List[Transaction] = []
        self.errors: List[str] = []
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")
    
    @property
    @abstractmethod
    def bank_name(self) -> str:
        """Name der Bank (muss von Subclass implementiert werden)"""
        pass
    
    @abstractmethod
    def parse(self) -> List[Transaction]:
        """
        Parst die PDF und extrahiert Transaktionen
        
        Returns:
            Liste von Transaction-Objekten
        """
        pass
    
    # ========================
    # HELPER METHODEN
    # ========================
    
    def extract_iban(self, text: str) -> Optional[str]:
        """
        Extrahiert IBAN aus Text
        
        Pattern: DE + 20 Ziffern (mit optionalen Leerzeichen)
        
        Args:
            text: Text zum Durchsuchen
            
        Returns:
            IBAN ohne Leerzeichen oder None
        """
        # Suche IBAN (DE + 20 Ziffern)
        iban_match = re.search(r'DE\s*\d{2}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{2}', text)
        
        if iban_match:
            iban = iban_match.group(0)
            # Entferne Leerzeichen
            iban = re.sub(r'\s+', '', iban)
            logger.debug(f"✓ IBAN gefunden: {iban}")
            return iban
        
        return None
    
    def parse_german_date(self, date_str: str, year: Optional[int] = None) -> Optional[datetime]:
        """
        Parst deutsches Datum (DD.MM.YYYY, DD.MM.YY oder DD.MM. mit Jahr)
        
        Args:
            date_str: Datum als String
            year: Optional - Jahr für DD.MM. Format (z.B. für VR-Bank)
            
        Returns:
            datetime Objekt oder None bei Fehler
        """
        try:
            # Versuche DD.MM.YYYY
            if len(date_str) == 10:
                return datetime.strptime(date_str, '%d.%m.%Y')
            # Versuche DD.MM.YY
            elif len(date_str) == 8:
                return datetime.strptime(date_str, '%d.%m.%y')
            # DD.MM. mit Jahr-Parameter (VR-Bank Format)
            elif len(date_str) == 6 and date_str.endswith('.') and year is not None:
                # DD.MM. -> DD.MM.YYYY
                return datetime.strptime(f"{date_str[:-1]}.{year}", '%d.%m.%Y')
            else:
                logger.warning(f"⚠️ Ungültiges Datumsformat: {date_str}")
                return None
        except ValueError as e:
            logger.warning(f"⚠️ Fehler beim Datum-Parsing: {date_str} - {e}")
            return None
    
    def parse_german_amount(self, amount_str: str) -> float:
        """
        Parst deutschen Betrag (1.234,56 -> 1234.56)
        
        Args:
            amount_str: Betrag als String
            
        Returns:
            Betrag als Float
        """
        try:
            # Entferne Tausender-Punkte und ersetze Komma durch Punkt
            amount_str = amount_str.replace('.', '').replace(',', '.')
            return float(amount_str)
        except ValueError as e:
            logger.error(f"❌ Fehler beim Betrag-Parsing: {amount_str} - {e}")
            return 0.0
    
    def clean_text(self, text: str) -> str:
        """
        Säubert Text von überflüssigen Zeichen
        
        - Multiple Leerzeichen -> Single Space
        - Führende/Trailing Leerzeichen
        - Zeilenumbrüche durch Leerzeichen
        
        Args:
            text: Zu säubernder Text
            
        Returns:
            Gesäuberter Text
        """
        # Zeilenumbrüche durch Leerzeichen
        text = text.replace('\n', ' ').replace('\r', ' ')
        # Multiple Spaces -> Single Space
        text = re.sub(r'\s+', ' ', text)
        # Trim
        return text.strip()
    
    def truncate_text(self, text: str, max_length: int = 500) -> str:
        """
        Kürzt Text auf maximale Länge
        
        Args:
            text: Zu kürzender Text
            max_length: Maximale Länge
            
        Returns:
            Gekürzter Text (mit ... falls gekürzt)
        """
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + '...'
    
    # ========================
    # STATISTIKEN & LOGGING
    # ========================
    
    def log_summary(self):
        """Loggt Zusammenfassung der geparsten Transaktionen"""
        if self.transactions:
            total = sum(t.betrag for t in self.transactions)
            logger.info(f"📊 {self.bank_name}: {len(self.transactions)} Transaktionen, "
                       f"Summe: {total:,.2f} EUR")
        if self.errors:
            logger.warning(f"⚠️ {len(self.errors)} Fehler beim Parsen")
    
    def get_statistics(self) -> Dict:
        """
        Gibt Statistiken über geparste Transaktionen zurück
        
        Returns:
            Dict mit Statistiken
        """
        if not self.transactions:
            return {
                'count': 0,
                'total_amount': 0.0,
                'date_range': 'Keine Transaktionen',
                'has_iban': bool(self.iban)
            }
        
        dates = [t.buchungsdatum for t in self.transactions]
        min_date = min(dates)
        max_date = max(dates)
        
        return {
            'count': len(self.transactions),
            'total_amount': sum(t.betrag for t in self.transactions),
            'date_range': f"{min_date.strftime('%d.%m.%Y')} - {max_date.strftime('%d.%m.%Y')}",
            'has_iban': bool(self.iban),
            'iban': self.iban
        }
