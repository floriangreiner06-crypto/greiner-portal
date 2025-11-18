#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VR-Bank / Genobank PDF Parser für Bankenspiegel 3.0
===================================================
Parser für VR-Bank und Genobank Kontoauszüge (PDF)

Format:
    DD.MM. DD.MM. Vorgang... Betrag H/S
    (H = Haben/Positiv, S = Soll/Negativ)

Features:
- Mehrzeiliger Verwendungszweck
- H/S Erkennung (Haben/Soll)
- Jahr-Extraktion aus Dateinamen oder PDF
- IBAN-Extraktion
- Endsaldo-Extraktion

Author: Claude AI
Version: 3.1
Date: 2025-11-14
"""

import pdfplumber
import re
import logging
from typing import List, Optional
from .base_parser import BaseParser, Transaction

logger = logging.getLogger(__name__)


class VRBankParser(BaseParser):
    """
    Parser für VR-Bank / Genobank Kontoauszüge

    Format-Beispiel:
        01.01. 02.01. SEPA-Überweisung Max Mustermann 1.234,56 H
        Verwendungszweck Zeile 2

    Besonderheiten:
    - Datum ohne Jahr (nur DD.MM.)
    - Betrag mit H (Haben/+) oder S (Soll/-)
    - Jahr muss aus Dateinamen oder PDF extrahiert werden
    - Endsaldo: "neuer Kontostand vom DD.MM.YYYY\nBETRAG H/S"

    Usage:
        parser = VRBankParser('path/to/vrbank.pdf')
        transactions = parser.parse()
    """

    def __init__(self, pdf_path: str):
        super().__init__(pdf_path)
        self.year: Optional[int] = None
        self.endsaldo: Optional[float] = None

    @property
    def bank_name(self) -> str:
        return "VR-Bank/Genobank"

    def parse(self) -> List[Transaction]:
        """
        Parst VR-Bank PDF und extrahiert Transaktionen

        Returns:
            Liste von Transaction-Objekten
        """
        logger.info(f"📄 Parse {self.bank_name}: {self.pdf_path.name}")

        try:
            with pdfplumber.open(str(self.pdf_path)) as pdf:
                # Text von allen Seiten sammeln
                full_text = self._extract_full_text(pdf)

                # IBAN extrahieren
                self.iban = self._extract_iban_vrbank(full_text)

                if not self.iban:
                    logger.warning(f"⚠️ Keine IBAN gefunden in {self.pdf_path.name}")

                # Jahr ermitteln (wichtig für Datum-Parsing!)
                self.year = self._extract_year(full_text)

                if not self.year:
                    logger.warning(f"⚠️ Kein Jahr gefunden - nutze aktuelles Jahr")
                    from datetime import datetime
                    self.year = datetime.now().year

                logger.debug(f"Jahr: {self.year}")

                # Transaktionen parsen
                self.transactions = self._parse_transactions(full_text)

                # Endsaldo extrahieren (Format: "neuer Kontostand vom DD.MM.YYYY\n39.049,69 H")
                endsaldo_match = re.search(
                    r'neuer Kontostand vom\s+\d{2}\.\d{2}\.\d{4}\s+([\d.,]+)\s+([HS])',
                    full_text,
                )
                if endsaldo_match:
                    betrag = self.parse_german_amount(endsaldo_match.group(1))
                    haben_soll = endsaldo_match.group(2)
                    # H = Haben (positiv), S = Soll (negativ)
                    self.endsaldo = betrag if haben_soll == 'H' else -betrag
                    logger.debug(f"✓ Endsaldo: {self.endsaldo} EUR ({haben_soll})")
                else:
                    logger.debug(f"⚠️ Kein Endsaldo gefunden")

                # Zusammenfassung loggen
                logger.info(f"✅ {self.bank_name}: {len(self.transactions)} Transaktionen, Endsaldo: {self.endsaldo}")

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

    def _extract_iban_vrbank(self, text: str) -> Optional[str]:
        """
        Extrahiert IBAN aus VR-Bank PDF

        VR-Bank Format: "IBAN: DE89 7002 2200 ..."
        """
        # Pattern mit "IBAN:" Prefix
        pattern = r'IBAN:\s*(DE\s?\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2})'
        match = re.search(pattern, text)

        if match:
            iban = match.group(1).replace(' ', '')
            logger.debug(f"IBAN gefunden: {iban}")
            return iban

        # Fallback: Normales IBAN-Pattern
        return self.extract_iban(text)

    def _extract_year(self, text: str) -> Optional[int]:
        """
        Extrahiert Jahr aus Dateinamen oder PDF-Text

        Versucht:
        1. Dateiname: "_2025_" Pattern
        2. PDF-Text: "erstellt am DD.MM.YYYY"
        """
        # Versuch 1: Dateiname
        filename = self.pdf_path.name
        year_match = re.search(r'_(\d{4})_', filename)
        if year_match:
            return int(year_match.group(1))

        # Versuch 2: "erstellt am" im PDF
        year_match = re.search(r'erstellt am \d{2}\.\d{2}\.(\d{4})', text)
        if year_match:
            return int(year_match.group(1))

        # Versuch 3: Suche beliebiges 4-stelliges Jahr im Text
        year_match = re.search(r'\b(202[0-9])\b', text)
        if year_match:
            return int(year_match.group(1))

        return None

    def _parse_transactions(self, full_text: str) -> List[Transaction]:
        """
        Parst Transaktionen aus dem Text

        VR-Bank Format:
            DD.MM. DD.MM. Vorgang... Betrag H/S

        Besonderheiten:
        - Zwei Datumsangaben (Buchung + Wert)
        - H = Haben (positiv), S = Soll (negativ)
        - Mehrzeiliger Verwendungszweck möglich
        """
        transactions = []
        lines = full_text.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # VR-Bank Transaktions-Pattern:
            # DD.MM. DD.MM. Vorgang... Betrag H/S
            tx_pattern = r'^(\d{2}\.\d{2}\.)[\s]+(\d{2}\.\d{2}\.)[\s]+(.+?)\s+([\d.,]+)\s+([HS])$'

            match = re.match(tx_pattern, line)

            if match:
                datum_str = match.group(1)          # Buchungsdatum
                wert_str = match.group(2)           # Valutadatum
                vorgang = match.group(3).strip()    # Verwendungszweck
                betrag_str = match.group(4)         # Betrag
                soll_haben = match.group(5)         # H oder S

                # Datum parsen (mit Jahr)
                buchungsdatum = self.parse_german_date(datum_str, year=self.year)
                valutadatum = self.parse_german_date(wert_str, year=self.year)

                if not buchungsdatum or not valutadatum:
                    logger.warning(f"⚠️ Ungültiges Datum: {datum_str} / {wert_str}")
                    i += 1
                    continue

                # Betrag parsen
                betrag = self.parse_german_amount(betrag_str)

                # H = Haben (positiv), S = Soll (negativ)
                if soll_haben == 'S':
                    betrag = -abs(betrag)
                else:
                    betrag = abs(betrag)

                # Sammle mehrzeiligen Verwendungszweck
                verwendungszweck_lines = [vorgang]

                j = i + 1
                while j < len(lines) and j < i + 10:  # Max 10 Zeilen
                    next_line = lines[j].strip()

                    # Stopp bei leerer Zeile
                    if not next_line:
                        break

                    # Stopp wenn nächste Transaktion beginnt
                    if re.match(r'^\d{2}\.\d{2}\.\s+\d{2}\.\d{2}\.', next_line):
                        break

                    # Stopp bei Footer
                    if 'Blatt' in next_line or 'VR GenoBank' in next_line:
                        break

                    verwendungszweck_lines.append(next_line)
                    j += 1

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
                logger.debug(f"✓ Transaktion: {datum_str} | {betrag:.2f} EUR ({soll_haben})")

                # Springe zu nächster möglichen Transaktion
                i = j
            else:
                i += 1

        return transactions


# Für Direktaufruf / Testing
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) < 2:
        print("Usage: python vrbank_parser.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    try:
        parser = VRBankParser(pdf_path)
        transactions = parser.parse()

        print(f"\n{'='*70}")
        print(f"ERGEBNIS")
        print(f"{'='*70}")
        print(f"Transaktionen: {len(transactions)}")
        print(f"Jahr: {parser.year}")
        print(f"Endsaldo: {parser.endsaldo} EUR")

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
