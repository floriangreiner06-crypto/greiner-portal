#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sparkasse Parser für Bankenspiegel 3.0
======================================
Parser für Sparkasse PDF-Kontoauszüge

Neues Format (2025):
- Zwei Daten direkt hintereinander: 03.11.202503.11.2025
- Dann Betrag: -21.460,00 EUR

Endsaldo-Format:
- Kontostand am 13.11.2025:    16.207,46 EUR*

Author: Claude AI
Version: 3.2
Date: 2025-11-14
"""

from .base_parser import BaseParser, Transaction
import pdfplumber
import re
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class SparkasseParser(BaseParser):
    """Parser für Sparkasse PDF-Kontoauszüge"""

    def __init__(self, pdf_path: str):
        """Initialisiert Parser"""
        super().__init__(pdf_path)
        self.endsaldo: Optional[float] = None

    @property
    def bank_name(self) -> str:
        """Name der Bank"""
        return "Sparkasse"

    def parse(self) -> List[Transaction]:
        """
        Parst Sparkasse PDF und extrahiert Transaktionen

        Returns:
            Liste von Transaction-Objekten
        """
        self.transactions = []

        try:
            with pdfplumber.open(str(self.pdf_path)) as pdf:

                # Sammle Text von allen Seiten
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"

                # IBAN extrahieren
                self.iban = self.extract_iban(full_text)
                if not self.iban:
                    logger.warning(f"⚠️ Keine IBAN gefunden in {self.pdf_path.name}")

                # Endsaldo extrahieren (Format: "Kontostand am 13.11.2025:    16.207,46 EUR*")
                endsaldo_match = re.search(
                    r'Kontostand am\s+\d{2}\.\d{2}\.\d{4}:\s+([\d.,]+)\s+EUR',
                    full_text
                )
                if endsaldo_match:
                    self.endsaldo = self.parse_german_amount(endsaldo_match.group(1))
                    logger.debug(f"✓ Endsaldo: {self.endsaldo} EUR")

                lines = full_text.split('\n')

                for i, line in enumerate(lines):
                    line_stripped = line.strip()

                    # NEUES FORMAT: Zwei Daten direkt hintereinander, dann Betrag
                    # Pattern: 03.11.202503.11.2025 -21.460,00 EUR
                    match = re.match(
                        r'^(\d{2}\.\d{2}\.\d{4})(\d{2}\.\d{2}\.\d{4})\s+([-+]?\d{1,3}(?:\.\d{3})*,\d{2})\s+EUR',
                        line_stripped
                    )

                    if match:
                        buchungsdatum_str = match.group(1)
                        valutadatum_str = match.group(2)
                        betrag_str = match.group(3)

                        # Parse Datum
                        buchungsdatum = self.parse_german_date(buchungsdatum_str)
                        valutadatum = self.parse_german_date(valutadatum_str)

                        if not buchungsdatum:
                            logger.warning(f"⚠️ Ungültiges Datum: {buchungsdatum_str}")
                            continue

                        if not valutadatum:
                            valutadatum = buchungsdatum

                        # Parse Betrag
                        betrag = self.parse_german_amount(betrag_str.replace('+', ''))

                        # Verwendungszweck ist in den Zeilen davor
                        verwendungszweck_lines = []

                        # Schaue 1-2 Zeilen zurück für Empfänger/Absender
                        for j in range(max(0, i-2), i):
                            prev_line = lines[j].strip()
                            # Skip Überschriften und leere Zeilen
                            if (prev_line and
                                not prev_line.startswith('BUCHUNG') and
                                not prev_line.startswith('Kontostand') and
                                not prev_line.startswith('Umsätze')):
                                verwendungszweck_lines.append(prev_line)

                        # Schaue auch Zeilen danach für weitere Details
                        j = i + 1
                        while j < len(lines) and j < i + 3:
                            next_line = lines[j].strip()

                            # Stop bei neuer Transaktion
                            if re.match(r'^\d{2}\.\d{2}\.\d{4}\d{2}\.\d{2}\.\d{4}', next_line):
                                break

                            # Sammle Verwendungszweck-Details
                            if next_line and '|' in next_line:
                                verwendungszweck_lines.append(next_line)
                            elif next_line and not next_line.startswith('Kontostand'):
                                verwendungszweck_lines.append(next_line)

                            j += 1

                        # Kombiniere Verwendungszweck
                        verwendungszweck = ' '.join(verwendungszweck_lines) if verwendungszweck_lines else "Buchung"

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

                    # ALTES FORMAT als Fallback
                    elif re.match(r'^(\d{2}\.\d{2}\.\d{4})([^0-9].+)', line_stripped):
                        date_match = re.match(r'^(\d{2}\.\d{2}\.\d{4})(.+)', line_stripped)
                        if date_match:
                            datum_str = date_match.group(1)
                            rest = date_match.group(2).strip()

                            # Skip Kontostand-Zeilen
                            if 'Kontostand am' in rest:
                                continue

                            # Suche Betrag am Ende
                            betrag_match = re.search(r'([-]?\d{1,3}(?:\.\d{3})*,\d{2})$', line_stripped)

                            if betrag_match:
                                betrag_str = betrag_match.group(1)

                                # Parse Datum
                                buchungsdatum = self.parse_german_date(datum_str)
                                if not buchungsdatum:
                                    continue

                                # Parse Betrag
                                betrag = self.parse_german_amount(betrag_str)

                                # Verwendungszweck
                                verwendungszweck = line_stripped[len(datum_str):betrag_match.start()].strip()

                                # Erstelle Transaction
                                transaction = Transaction(
                                    buchungsdatum=buchungsdatum,
                                    valutadatum=buchungsdatum,
                                    verwendungszweck=self.truncate_text(self.clean_text(verwendungszweck), 500),
                                    betrag=betrag,
                                    iban=self.iban
                                )

                                self.transactions.append(transaction)

                # Log Summary
                logger.info(f"✅ {self.bank_name}: {len(self.transactions)} Transaktionen, Endsaldo: {self.endsaldo}")

                return self.transactions

        except Exception as e:
            error_msg = f"❌ Fehler beim Parsen von {self.pdf_path.name}: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            import traceback
            traceback.print_exc()
            return []
