# -*- coding: utf-8 -*-
"""
HypoVereinsbank Parser für Bankenspiegel 3.0
============================================
Parser für HypoVereinsbank PDF-Kontoauszüge

Besonderheiten:
- Format: DD.MM.YYYY DD.MM.YYYY TEXT BETRAG EUR
- Betrag steht DIREKT in der ersten Zeile
- Verwendungszweck kann mehrzeilig sein
- Extrahiert Endsaldo (Kontostand am...)

Author: Claude AI
Version: 3.1
Date: 2025-11-14
"""

from .base_parser import BaseParser, Transaction
import pdfplumber
import re
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class HypoVereinsbankParser(BaseParser):
    """
    Parser für HypoVereinsbank PDF-Kontoauszüge

    Erkennt HypoVereinsbank/UniCredit Formate
    """

    def __init__(self, pdf_path: str):
        """Initialisiert Parser"""
        super().__init__(pdf_path)
        self.endsaldo = None

    @property
    def bank_name(self) -> str:
        """Name der Bank"""
        return "HypoVereinsbank"

    def parse(self) -> List[Transaction]:
        """
        Parst HypoVereinsbank PDF und extrahiert Transaktionen

        Returns:
            Liste von Transaction-Objekten
        """
        self.transactions = []

        try:
            with pdfplumber.open(str(self.pdf_path)) as pdf:

                # Vollständigen Text für IBAN und Endsaldo
                full_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"

                # IBAN extrahieren
                if full_text:
                    # HypoVereinsbank Format: "IBAN DE..."
                    iban_match = re.search(r'IBAN\s+(DE\d{20})', full_text)
                    if iban_match:
                        self.iban = iban_match.group(1)
                    else:
                        # Fallback: Standard IBAN-Suche
                        self.iban = self.extract_iban(full_text)

                    # Endsaldo extrahieren (Format: "Kontostand am DD.MM.YYYY\n62.954,41 EUR")
                    endsaldo_match = re.search(
                        r'Kontostand am\s+\d{2}\.\d{2}\.\d{4}\s+([\d.,]+)\s*EUR',
                        full_text,
                    )
                    if endsaldo_match:
                        self.endsaldo = self.parse_german_amount(endsaldo_match.group(1))
                        logger.debug(f"✓ Endsaldo gefunden: {self.endsaldo} EUR")
                    else:
                        logger.debug(f"⚠️ Kein Endsaldo gefunden in {self.pdf_path.name}")

                if not self.iban:
                    logger.warning(f"⚠️ Keine IBAN gefunden in {self.pdf_path.name}")

                # Alle Seiten durchgehen für Transaktionen
                for page in pdf.pages:
                    text = page.extract_text()

                    if not text:
                        continue

                    lines = text.split('\n')

                    i = 0
                    while i < len(lines):
                        line = lines[i].strip()

                        # HypoVereinsbank Format:
                        # DD.MM.YYYY DD.MM.YYYY BUCHUNGSTEXT BETRAG EUR
                        # Betrag steht DIREKT in der ersten Zeile!

                        # Pattern: Zwei Datumsangaben, dann Text, dann Betrag mit EUR
                        match = re.match(
                            r'^(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\.\d{2}\.\d{4})\s+(.+?)\s+([-]?\d{1,3}(?:\.\d{3})*,\d{2})\s+EUR\s*$',
                            line
                        )

                        if match:
                            buchungsdatum_str = match.group(1)
                            valutadatum_str = match.group(2)
                            transaktionstyp = match.group(3).strip()
                            betrag_str = match.group(4)

                            # Parse Daten
                            buchungsdatum = self.parse_german_date(buchungsdatum_str)
                            valutadatum = self.parse_german_date(valutadatum_str)

                            if not buchungsdatum:
                                logger.warning(f"⚠️ Ungültiges Buchungsdatum: {buchungsdatum_str}")
                                i += 1
                                continue

                            if not valutadatum:
                                valutadatum = buchungsdatum  # Fallback

                            # Parse Betrag
                            betrag = self.parse_german_amount(betrag_str)

                            # Sammle Verwendungszweck aus Folgezeilen
                            verwendungszweck_lines = [transaktionstyp]
                            i += 1

                            # Sammle alle Zeilen bis zur nächsten Buchung
                            while i < len(lines):
                                next_line = lines[i].strip()

                                # Stop wenn nächste Buchungszeile beginnt
                                if re.match(r'^\d{2}\.\d{2}\.\d{4}\s+\d{2}\.\d{2}\.\d{4}', next_line):
                                    break

                                # Stop bei Seitenumbruch oder Footer
                                if not next_line or 'Seite' in next_line or 'https://' in next_line:
                                    i += 1
                                    break

                                # Stop bei typischen Footer-Elementen
                                if 'UniCredit' in next_line or 'HypoVereinsbank' in next_line:
                                    i += 1
                                    break

                                # Normale Verwendungszweck-Zeile
                                if next_line and not next_line.startswith('-----'):
                                    verwendungszweck_lines.append(next_line)

                                i += 1

                            # Kombiniere Verwendungszweck
                            verwendungszweck = ' '.join(verwendungszweck_lines)

                            # Säubere und kürze Text
                            verwendungszweck = self.clean_text(verwendungszweck)
                            verwendungszweck = self.truncate_text(verwendungszweck, 500)

                            # Erstelle Transaction-Objekt
                            transaction = Transaction(
                                buchungsdatum=buchungsdatum,
                                valutadatum=valutadatum,
                                verwendungszweck=verwendungszweck,
                                betrag=betrag,
                                iban=self.iban
                            )

                            self.transactions.append(transaction)
                            logger.debug(f"✓ Transaction: {transaction}")
                        else:
                            i += 1

                # Log Summary mit Endsaldo
                logger.info(f"✅ HypoVereinsbank: {len(self.transactions)} Transaktionen, Endsaldo: {self.endsaldo}")

                return self.transactions

        except Exception as e:
            error_msg = f"❌ Fehler beim Parsen von {self.pdf_path.name}: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return []


# Alias für beide Schreibweisen (wegen Typo in älteren Versionen)
Hypovereinsbank_Parser = HypoVereinsbankParser

# Alias für ältere Schreibweise (ohne Bindestriche)
HypovereinsbankParser = HypoVereinsbankParser
