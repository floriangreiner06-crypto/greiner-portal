#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VR Bank Landau-Mengkofen Parser für Bankenspiegel
================================================
Parser für VR-Bank Landau-Mengkofen PDF-Kontoauszüge

Format:
    TV Landau a.d. Isar                              +98,90 EUR
    DE44742500000000005777                           11.11.2025
    Re. 23109800 Kd.Nr. 1022644 EREF: NXSID:1638729

Endsaldo-Format (2 Zeilen):
    (Endsaldo)
    +2.831,40EUR  ← OHNE Leerzeichen!

Author: Claude AI
Version: 1.2
Date: 2025-11-14
"""

import pdfplumber
import re
import logging
from typing import List, Optional
from datetime import datetime
from .base_parser import BaseParser, Transaction

logger = logging.getLogger(__name__)


class VRBankLandauParser(BaseParser):
    """Parser für VR-Bank Landau-Mengkofen Kontoauszüge"""

    def __init__(self, pdf_path: str):
        """Initialisiert Parser"""
        super().__init__(pdf_path)
        self.endsaldo: Optional[float] = None

    @property
    def bank_name(self) -> str:
        return "VR Bank Landau-Mengkofen"

    def parse(self) -> List[Transaction]:
        """Parst VR Bank Landau PDF und extrahiert Transaktionen"""
        logger.info(f"📄 Parse {self.bank_name}: {self.pdf_path.name}")

        try:
            with pdfplumber.open(str(self.pdf_path)) as pdf:
                full_text = self._extract_full_text(pdf)

                # IBAN extrahieren
                self.iban = self._extract_iban_vrbank_landau(full_text)
                if not self.iban:
                    logger.warning(f"⚠️ Keine IBAN gefunden in {self.pdf_path.name}")

                # Transaktionen parsen
                self.transactions = self._parse_transactions(full_text)

                # Endsaldo extrahieren - Format: "(Endsaldo)\n+2.831,40EUR"
                endsaldo_match = re.search(
                    r'\(Endsaldo\).*?\n\s*([-+]?[\d.,]+)\s*EUR',
                    full_text,
                    re.DOTALL
                )
                if endsaldo_match:
                    self.endsaldo = self.parse_german_amount(endsaldo_match.group(1))
                    logger.debug(f"✓ Endsaldo: {self.endsaldo} EUR")

                logger.info(f"📊 {self.bank_name}: {len(self.transactions)} Transaktionen, Summe: {sum(t.betrag for t in self.transactions):.2f} EUR")
                return self.transactions

        except Exception as e:
            logger.error(f"❌ Fehler beim Parsen: {e}")
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

    def _extract_iban_vrbank_landau(self, text: str) -> Optional[str]:
        """Extrahiert Konto-IBAN aus VR Bank Landau PDF Header"""
        pattern = r'^IBAN\s+(DE\d{20})'
        for line in text.split('\n'):
            match = re.match(pattern, line.strip())
            if match:
                iban = match.group(1)
                logger.debug(f"IBAN gefunden: {iban}")
                return iban
        return self.extract_iban(text)

    def _parse_transactions(self, full_text: str) -> List[Transaction]:
        """Parst Transaktionen aus dem Text"""
        transactions = []
        lines = full_text.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Zeile 1: Name + Betrag
            betrag_pattern = r'^(.+?)\s+([-+]?\d{1,3}(?:\.\d{3})*,\d{2})\s+EUR$'
            match = re.match(betrag_pattern, line)

            if match:
                empfaenger = match.group(1).strip()
                betrag_str = match.group(2)

                if i + 1 >= len(lines):
                    i += 1
                    continue

                datum_line = lines[i + 1].strip()

                # Zeile 2: IBAN + Datum
                datum_pattern = r'^(DE\d{20})?\s*(\d{2}\.\d{2}\.\d{4})$'
                datum_match = re.search(datum_pattern, datum_line)

                if not datum_match:
                    i += 1
                    continue

                datum_str = datum_match.group(2)
                buchungsdatum = self.parse_german_date(datum_str)

                if not buchungsdatum:
                    logger.warning(f"⚠️ Ungültiges Datum: {datum_str}")
                    i += 1
                    continue

                betrag = self.parse_german_amount(betrag_str)

                # Zeile 3: Verwendungszweck (optional)
                verwendungszweck = empfaenger
                if i + 2 < len(lines):
                    zweck_line = lines[i + 2].strip()
                    if (zweck_line and
                        not zweck_line.startswith('(Startsaldo)') and
                        not zweck_line.startswith('(Endsaldo)') and
                        not re.match(betrag_pattern, zweck_line)):
                        verwendungszweck = f"{empfaenger} | {zweck_line}"

                transaction = Transaction(
                    buchungsdatum=buchungsdatum,
                    betrag=betrag,
                    verwendungszweck=verwendungszweck,
                    iban=self.iban,
                    valutadatum=buchungsdatum
                )

                transactions.append(transaction)
                logger.debug(f"✓ Transaktion: {buchungsdatum} | {betrag:>10.2f} | {empfaenger[:30]}")

                i += 3
            else:
                i += 1

        return transactions
