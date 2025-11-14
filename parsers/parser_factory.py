#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser Factory für Bankenspiegel 3.0
====================================
Automatische Erkennung des richtigen Parsers basierend auf IBAN, PDF-Inhalt oder Dateinamen

Priorität:
1. IBAN im PDF (höchste Priorität - eindeutig!)
2. Bank-Keywords im PDF-Inhalt
3. Keywords im Dateinamen (Fallback)

Author: Claude AI
Version: 4.0 (IBAN-basiert)
Date: 2025-11-13
"""

import logging
import re
from pathlib import Path
from typing import Optional
import pdfplumber

from .base_parser import BaseParser
from .sparkasse_parser import SparkasseParser
from .vrbank_parser import VRBankParser
from .vrbank_landau_parser import VRBankLandauParser
from .hypovereinsbank_parser import HypovereinsbankParser

logger = logging.getLogger(__name__)


class ParserFactory:
    """
    Factory-Klasse für automatische Parser-Auswahl
    
    Erkennt die Bank anhand von (in dieser Priorität):
    1. IBAN im PDF → Eindeutige Zuordnung
    2. Bank-Namen im PDF-Inhalt
    3. Keywords im Dateinamen
    """

    # IBAN → Parser Mapping (HÖCHSTE PRIORITÄT!)
    IBAN_TO_PARSER = {
        # Sparkasse
        'DE63741500000760036467': SparkasseParser,
        
        # HypoVereinsbank
        'DE22741200710006407420': HypovereinsbankParser,
        
        # VR Bank Landau (spezifisch!)
        'DE76741910000000303585': VRBankLandauParser,
        
        # VR Bank / Genobank (generisch)
        'DE27741900000000057908': VRBankParser,  # 57908 KK
        'DE68741900000001501500': VRBankParser,  # 1501500 HYU KK
        'DE96741900001700057908': VRBankParser,  # 1700057908 Festgeld
        'DE06741900003700057908': VRBankParser,  # 3700057908 Festgeld
        'DE94741900000020057908': VRBankParser,  # 20057908 Darlehen
        'DE58741900004700057908': VRBankParser,  # 4700057908 Darlehen
        'DE41741900000120057908': VRBankParser,  # KfW 120057908
        'DE64741900000000022225': VRBankParser,  # 22225 Immo KK
    }

    # Bank-Keywords im PDF-Inhalt
    CONTENT_PATTERNS = {
        'Sparkasse': SparkasseParser,
        'VR GenoBank': VRBankParser,
        'Volksbank': VRBankParser,
        'Raiffeisenbank': VRBankParser,
        'HypoVereinsbank': HypovereinsbankParser,
        'UniCredit Bank': HypovereinsbankParser,
    }

    # Bank-Keywords im Dateinamen (Fallback)
    FILENAME_PATTERNS = {
        'sparkasse': SparkasseParser,
        'sparkass': SparkasseParser,
        'genobank': VRBankParser,
        'vr bank': VRBankParser,
        'vr-bank': VRBankParser,
        'vrbank': VRBankParser,
        'volksbank': VRBankParser,
        'raiffeisenbank': VRBankParser,
        'hypovereinsbank': HypovereinsbankParser,
        'hypo': HypovereinsbankParser,
        'unicredit': HypovereinsbankParser,
    }

    @classmethod
    def create_parser(cls, pdf_path: str, force_parser: Optional[str] = None) -> BaseParser:
        """
        Erstellt den passenden Parser für eine PDF-Datei
        
        Detection-Reihenfolge:
        1. IBAN im PDF (eindeutig!)
        2. Bank-Keywords im PDF-Inhalt
        3. Keywords im Dateinamen
        4. Fallback: SparkasseParser

        Args:
            pdf_path: Pfad zur PDF-Datei
            force_parser: Optional - erzwinge Parser ('sparkasse', 'vrbank', 'hypovereinsbank')

        Returns:
            Parser-Instanz

        Raises:
            FileNotFoundError: Wenn PDF nicht existiert
        """
        pdf_path_obj = Path(pdf_path)

        if not pdf_path_obj.exists():
            raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")

        # Force-Parser wenn angegeben
        if force_parser:
            return cls._get_forced_parser(pdf_path, force_parser)

        # 1. PRIORITÄT: IBAN-basierte Erkennung (eindeutig!)
        parser_class = cls._detect_by_iban(pdf_path)
        if parser_class:
            logger.info(f"✅ Parser erkannt (IBAN): {parser_class.__name__}")
            return parser_class(pdf_path)

        # 2. PRIORITÄT: Inhalt-basierte Erkennung (Bank-Namen im PDF)
        parser_class = cls._detect_by_content(pdf_path)
        if parser_class:
            logger.info(f"✅ Parser erkannt (Inhalt): {parser_class.__name__}")
            return parser_class(pdf_path)

        # 3. PRIORITÄT: Dateinamen-basierte Erkennung (Fallback)
        parser_class = cls._detect_by_filename(pdf_path_obj)
        if parser_class:
            logger.info(f"✅ Parser erkannt (Dateiname): {parser_class.__name__}")
            return parser_class(pdf_path)

        # Letzter Fallback: SparkasseParser (universell)
        logger.warning(f"⚠️ Bank nicht erkannt - nutze SparkasseParser als Fallback")
        return SparkasseParser(pdf_path)

    @classmethod
    def _detect_by_iban(cls, pdf_path: str) -> Optional[type]:
        """
        Erkennt Parser anhand der IBAN im PDF
        
        Dies ist die PRÄZISESTE Methode - eine IBAN ist eindeutig!
        Sucht nach deutschem IBAN-Format: DE + 20 Ziffern
        
        Returns:
            Parser-Klasse oder None
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if not pdf.pages:
                    return None

                # Erste Seite extrahieren
                first_page_text = pdf.pages[0].extract_text()
                if not first_page_text:
                    return None

                # IBAN-Pattern: DE + 20 Ziffern
                # IBAN mit oder ohne Leerzeichen
                iban_pattern = r'DE\d{2}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{2}'
                found_ibans_raw = re.findall(iban_pattern, first_page_text)
                # Leerzeichen entfernen für Mapping-Lookup
                found_ibans = [iban.replace(' ', '') for iban in found_ibans_raw]

                if not found_ibans:
                    logger.debug("Keine IBAN im PDF gefunden")
                    return None

                # Prüfe jede gefundene IBAN gegen Mapping
                for iban in found_ibans:
                    if iban in cls.IBAN_TO_PARSER:
                        parser_class = cls.IBAN_TO_PARSER[iban]
                        logger.debug(f"IBAN-Match: {iban} → {parser_class.__name__}")
                        return parser_class

                logger.debug(f"Gefundene IBANs nicht im Mapping: {found_ibans}")
                return None

        except Exception as e:
            logger.error(f"Fehler bei IBAN-Detection: {e}")
            return None

    @classmethod
    def _detect_by_content(cls, pdf_path: str) -> Optional[type]:
        """
        Erkennt Parser anhand des PDF-Inhalts
        
        Sucht nach Bank-Keywords auf der ersten Seite
        
        Returns:
            Parser-Klasse oder None
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if not pdf.pages:
                    return None

                first_page_text = pdf.pages[0].extract_text()
                if not first_page_text:
                    return None

                # Nach Keywords suchen
                for keyword, parser_class in cls.CONTENT_PATTERNS.items():
                    if keyword in first_page_text:
                        logger.debug(f"Content-Match: '{keyword}' → {parser_class.__name__}")
                        return parser_class

                return None

        except Exception as e:
            logger.error(f"Fehler bei Content-Detection: {e}")
            return None

    @classmethod
    def _detect_by_filename(cls, pdf_path: Path) -> Optional[type]:
        """
        Erkennt Parser anhand des Dateinamens
        
        Fallback-Methode wenn IBAN und Inhalt nicht funktionieren
        
        Returns:
            Parser-Klasse oder None
        """
        filename_lower = pdf_path.name.lower()

        for keyword, parser_class in cls.FILENAME_PATTERNS.items():
            if keyword in filename_lower:
                logger.debug(f"Filename-Match: '{keyword}' → {parser_class.__name__}")
                return parser_class

        return None

    @classmethod
    def _get_forced_parser(cls, pdf_path: str, parser_type: str) -> BaseParser:
        """
        Gibt erzwungenen Parser zurück
        
        Args:
            parser_type: 'sparkasse', 'vrbank', oder 'hypovereinsbank'
        """
        parser_map = {
            'sparkasse': SparkasseParser,
            'vrbank': VRBankParser,
            'hypovereinsbank': HypovereinsbankParser,
        }

        parser_class = parser_map.get(parser_type.lower())
        if not parser_class:
            raise ValueError(f"Unbekannter Parser-Typ: {parser_type}")

        logger.info(f"✅ Erzwungener Parser: {parser_class.__name__}")
        return parser_class(pdf_path)

    @classmethod
    def get_supported_banks(cls) -> list:
        """Gibt Liste der unterstützten Banken zurück"""
        return [
            "Sparkasse",
            "VR-Bank / Genobank",
            "VR Bank Landau",
            "HypoVereinsbank"
        ]

    @classmethod
    def get_parser_info(cls) -> dict:
        """Gibt Informationen über verfügbare Parser zurück"""
        return {
            'sparkasse': {
                'class': SparkasseParser,
                'name': 'Sparkasse',
                'format': 'DD.MM.YYYY Text Betrag'
            },
            'vrbank': {
                'class': VRBankParser,
                'name': 'VR-Bank / Genobank',
                'format': 'DD.MM. DD.MM. Text Betrag H/S'
            },
            'vrbank_landau': {
                'class': VRBankLandauParser,
                'name': 'VR Bank Landau-Mengkofen',
                'format': '3-Zeilen Format'
            },
            'hypovereinsbank': {
                'class': HypovereinsbankParser,
                'name': 'HypoVereinsbank',
                'format': 'DD.MM.YYYY DD.MM.YYYY Text Betrag EUR'
            }
        }
