#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genobank Universal Parser - für Monatsauszüge UND Tagesauszüge
===============================================================
Unterstützt zwei verschiedene Formate:

1. Standard-Format (Monatsauszüge):
   DD.MM. DD.MM. Vorgang... Betrag H/S
   
2. Tagesauszug-Format:
   Empfänger Name                    +Betrag EUR
   IBAN                              Datum
   Verwendungszweck

Author: Claude AI (basierend auf Tag 13 Erfahrungen)
Version: 1.0
Date: 2025-11-07
"""

import pdfplumber
import re
import logging
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class GenobankUniversalParser:
    """
    Universal-Parser für alle Genobank PDF-Formate
    
    Erkennt automatisch:
    - Standard-Format (Monatsauszüge)
    - Tagesauszug-Format ("Genobank Auszug...")
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.transactions = []
        self.format_type = None  # 'standard' oder 'tagesauszug'
        self.iban = None
        self.year = None
        
    def parse(self) -> List[Dict]:
        """
        Parst PDF und erkennt automatisch das Format
        
        Returns:
            Liste von Transaktions-Dictionaries
        """
        logger.info(f"📄 Parse Genobank PDF: {self.pdf_path.name}")
        
        try:
            with pdfplumber.open(str(self.pdf_path)) as pdf:
                full_text = self._extract_full_text(pdf)
                
                # Format-Erkennung
                self.format_type = self._detect_format(full_text)
                logger.info(f"✓ Format erkannt: {self.format_type}")
                
                # Jahr ermitteln
                self.year = self._extract_year(full_text)
                if not self.year:
                    self.year = datetime.now().year
                    logger.warning(f"⚠️ Kein Jahr gefunden - nutze {self.year}")
                
                # IBAN extrahieren
                self.iban = self._extract_iban(full_text)
                
                # Je nach Format parsen
                if self.format_type == 'tagesauszug':
                    self.transactions = self._parse_tagesauszug(full_text)
                else:
                    self.transactions = self._parse_standard(full_text)
                
                logger.info(f"✅ {len(self.transactions)} Transaktionen gefunden")
                return self.transactions
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Parsen: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_full_text(self, pdf) -> str:
        """Extrahiert Text von allen Seiten"""
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        return full_text
    
    def _detect_format(self, text: str) -> str:
        """
        Erkennt automatisch das PDF-Format
        
        Returns:
            'standard' oder 'tagesauszug'
        """
        # Tagesauszug-Indikatoren
        tagesauszug_indicators = [
            'Genobank Auszug',
            '(Startsaldo)',
            '(Endsaldo)'
        ]
        
        for indicator in tagesauszug_indicators:
            if indicator in text:
                return 'tagesauszug'
        
        # Standard-Format-Indikatoren
        standard_indicators = [
            r'\d{2}\.\d{2}\.\s+\d{2}\.\d{2}\.\s+.+\s+[\d.,]+\s+[HS]'
        ]
        
        for pattern in standard_indicators:
            if re.search(pattern, text):
                return 'standard'
        
        # Fallback: versuche zu erkennen anhand Dateinamen
        filename = self.pdf_path.name.lower()
        if 'auszug' in filename and 'genobank' in filename:
            # "Genobank Auszug Auto Greiner 03.11.25.pdf" Format
            return 'tagesauszug'
        
        return 'standard'  # Default
    
    def _extract_year(self, text: str) -> Optional[int]:
        """Extrahiert Jahr aus Dateinamen oder PDF-Text"""
        # Versuch 1: Dateiname (_2025_)
        filename = self.pdf_path.name
        year_match = re.search(r'_(\d{4})_', filename)
        if year_match:
            return int(year_match.group(1))
        
        # Versuch 2: Dateiname (03.11.25 am Ende)
        year_match = re.search(r'\.(\d{2})\.pdf$', filename)
        if year_match:
            yy = int(year_match.group(1))
            return 2000 + yy  # 25 -> 2025
        
        # Versuch 3: "erstellt am" im PDF
        year_match = re.search(r'erstellt am \d{2}\.\d{2}\.(\d{4})', text)
        if year_match:
            return int(year_match.group(1))
        
        # Versuch 4: Beliebiges 4-stelliges Jahr
        year_match = re.search(r'\b(202[0-9])\b', text)
        if year_match:
            return int(year_match.group(1))
        
        return None
    
    def _extract_iban(self, text: str) -> Optional[str]:
        """Extrahiert IBAN aus PDF"""
        # Pattern mit "IBAN:" Prefix
        pattern = r'IBAN:\s*(DE\s?\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2})'
        match = re.search(pattern, text)
        
        if match:
            iban = match.group(1).replace(' ', '')
            return iban
        
        # Fallback: Normales IBAN-Pattern
        pattern = r'(DE\d{20})'
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        
        return None
    
    def _parse_standard(self, text: str) -> List[Dict]:
        """
        Parst Standard-Format (Monatsauszüge)
        Format: DD.MM. DD.MM. Vorgang... Betrag H/S
        """
        transactions = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Standard-Pattern
            tx_pattern = r'^(\d{2}\.\d{2}\.)[\s]+(\d{2}\.\d{2}\.)[\s]+(.+?)\s+([\d.,]+)\s+([HS])$'
            match = re.match(tx_pattern, line)
            
            if match:
                datum_str = match.group(1)
                wert_str = match.group(2)
                vorgang = match.group(3).strip()
                betrag_str = match.group(4)
                soll_haben = match.group(5)
                
                # Datum parsen
                buchungsdatum = self._parse_german_date(datum_str, self.year)
                valutadatum = self._parse_german_date(wert_str, self.year)
                
                if not buchungsdatum or not valutadatum:
                    i += 1
                    continue
                
                # Betrag parsen
                betrag = self._parse_german_amount(betrag_str)
                if soll_haben == 'S':
                    betrag = -abs(betrag)
                else:
                    betrag = abs(betrag)
                
                # Sammle mehrzeiligen Verwendungszweck
                verwendungszweck_lines = [vorgang]
                j = i + 1
                while j < len(lines) and j < i + 10:
                    next_line = lines[j].strip()
                    if not next_line or re.match(r'^\d{2}\.\d{2}\.\s+\d{2}\.\d{2}\.', next_line):
                        break
                    verwendungszweck_lines.append(next_line)
                    j += 1
                
                verwendungszweck = ' '.join(verwendungszweck_lines)
                
                transaction = {
                    'buchungsdatum': buchungsdatum,
                    'valutadatum': valutadatum,
                    'verwendungszweck': verwendungszweck[:500],
                    'betrag': betrag,
                    'iban': self.iban,
                    'saldo_nach_buchung': None  # Wird später berechnet
                }
                transactions.append(transaction)
                logger.debug(f"✓ {datum_str} | {betrag:.2f} EUR ({soll_haben})")
                i = j
            else:
                i += 1
        
        return transactions
    
    def _parse_tagesauszug(self, text: str) -> List[Dict]:
        """
        Parst Tagesauszug-Format
        Format:
            Empfänger Name                    +Betrag EUR
            IBAN                              Datum
            Verwendungszweck
        """
        transactions = []
        lines = text.split('\n')
        
        # Datum aus Dateinamen extrahieren (DD.MM.YY)
        filename = self.pdf_path.name
        date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{2})', filename)
        if date_match:
            day, month, yy = date_match.groups()
            year = 2000 + int(yy)
            default_datum = datetime(year, int(month), int(day))
            logger.debug(f"Datum aus Dateinamen: {default_datum.strftime('%Y-%m-%d')}")
        else:
            default_datum = datetime.now()
            logger.warning("⚠️ Kein Datum im Dateinamen - nutze heute")
        
        # Startsaldo finden (über mehrere Zeilen!)
        startsaldo = None
        
        # Kombiniere alle Zeilen für Multiline-Regex
        full_text_search = '\n'.join(lines)
        if '(Startsaldo)' in full_text_search:
            # Regex mit \s* erlaubt Zeilenumbrüche zwischen Startsaldo und Betrag
            saldo_match = re.search(r'\(Startsaldo\)\s*\+?([-\d.,]+)\s*EUR', full_text_search)
            if saldo_match:
                startsaldo = self._parse_german_amount(saldo_match.group(1))
                logger.info(f"✅ Startsaldo gefunden: {startsaldo:.2f} EUR")
        
        if startsaldo is None:
            logger.warning("⚠️ Kein Startsaldo gefunden")
            startsaldo = 0.0
        
        current_saldo = startsaldo
        
        # Transaktionen parsen
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Betrag-Zeile finden: "Name/Text +/-Betrag EUR"
            betrag_pattern = r'^(.+?)\s+([-+]?[\d.,]+)\s+EUR\s*$'
            match = re.match(betrag_pattern, line)
            
            if match:
                empfaenger = match.group(1).strip()
                betrag_str = match.group(2)
                betrag = self._parse_german_amount(betrag_str.replace('+', '').replace('-', ''))
                
                # Vorzeichen prüfen
                if betrag_str.startswith('-'):
                    betrag = -abs(betrag)
                else:
                    betrag = abs(betrag)
                
                # Nächste Zeile: IBAN und Datum
                datum = default_datum
                verwendungszweck_lines = [empfaenger]
                
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    
                    # Suche nach Datum (DD.MM.YYYY)
                    datum_match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', next_line)
                    if datum_match:
                        day, month, year = datum_match.groups()
                        datum = datetime(int(year), int(month), int(day))
                    
                    # Sammle weitere Zeilen für Verwendungszweck
                    j = i + 1
                    while j < len(lines) and j < i + 5:
                        extra_line = lines[j].strip()
                        if not extra_line:
                            break
                        if re.match(betrag_pattern, extra_line):  # Nächste Transaktion
                            break
                        if '(Endsaldo)' in extra_line or 'Blatt' in extra_line:
                            break
                        verwendungszweck_lines.append(extra_line)
                        j += 1
                    
                    i = j
                
                verwendungszweck = ' '.join(verwendungszweck_lines)
                
                # Saldo akkumulieren
                current_saldo += betrag
                
                transaction = {
                    'buchungsdatum': datum,
                    'valutadatum': datum,
                    'verwendungszweck': verwendungszweck[:500],
                    'betrag': betrag,
                    'iban': self.iban,
                    'saldo_nach_buchung': current_saldo
                }
                transactions.append(transaction)
                logger.debug(f"✓ {datum.strftime('%d.%m.%Y')} | {betrag:+.2f} EUR | Saldo: {current_saldo:.2f}")
            else:
                i += 1
        
        # Endsaldo validieren
        endsaldo_pdf = None
        for line in lines:
            if '(Endsaldo)' in line:
                saldo_match = re.search(r'\+?([-\d.,]+)\s+EUR', line)
                if saldo_match:
                    endsaldo_pdf = self._parse_german_amount(saldo_match.group(1))
                    break
        
        if endsaldo_pdf is not None:
            if abs(current_saldo - endsaldo_pdf) < 0.01:
                logger.info(f"✅ Saldo-Validierung OK: {current_saldo:.2f} EUR")
            else:
                logger.warning(f"⚠️ Saldo-Differenz: DB={current_saldo:.2f} EUR, PDF={endsaldo_pdf:.2f} EUR")
        
        return transactions
    
    def _parse_german_date(self, date_str: str, year: int) -> Optional[datetime]:
        """Parst deutsches Datum DD.MM. mit Jahr"""
        try:
            # Entferne Leerzeichen und trailing dots
            date_str = date_str.strip().rstrip('.')
            
            # DD.MM format -> ergänze Jahr
            if re.match(r'^\d{2}\.\d{2}$', date_str):
                date_str = f"{date_str}.{year}"
            
            return datetime.strptime(date_str, '%d.%m.%Y')
        except:
            return None
    
    def _parse_german_amount(self, amount_str: str) -> float:
        """Parst deutschen Betrag (1.234,56)"""
        try:
            # Entferne Leerzeichen
            amount_str = amount_str.strip()
            # Entferne Tausender-Punkte
            amount_str = amount_str.replace('.', '')
            # Ersetze Komma durch Punkt
            amount_str = amount_str.replace(',', '.')
            # Entferne + Zeichen
            amount_str = amount_str.replace('+', '')
            return float(amount_str)
        except ValueError:
            logger.error(f"❌ Kann Betrag nicht parsen: {amount_str}")
            return 0.0


# Test-Funktion
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python genobank_universal_parser.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    try:
        parser = GenobankUniversalParser(pdf_path)
        transactions = parser.parse()
        
        print(f"\n{'='*70}")
        print(f"ERGEBNIS")
        print(f"{'='*70}")
        print(f"Format: {parser.format_type}")
        print(f"Jahr: {parser.year}")
        print(f"IBAN: {parser.iban}")
        print(f"Transaktionen: {len(transactions)}")
        
        if transactions:
            print(f"\nErste 5 Transaktionen:")
            for i, t in enumerate(transactions[:5], 1):
                print(f"{i}. {t['buchungsdatum'].strftime('%Y-%m-%d')} | "
                      f"{t['betrag']:+10.2f} EUR | "
                      f"{t['verwendungszweck'][:50]}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
