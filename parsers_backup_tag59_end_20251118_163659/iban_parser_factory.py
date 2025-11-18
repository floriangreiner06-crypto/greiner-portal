#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IBAN-basierte Parser Factory
=============================
Wählt automatisch den richtigen Parser basierend auf IBAN

Vorteile:
- IBAN aus PDF-Inhalt = zuverlässig (nicht aus Dateiname!)
- Kein User-Fehler möglich
- Einfach erweiterbar

Author: Claude AI
Version: 1.1
Date: 2025-11-18
"""

from typing import Optional, Type
from pathlib import Path
import re
import logging
import pdfplumber

from parsers.base_parser import BaseParser
from parsers.genobank.genobank_tagesauszug_parser import GenobankTagesauszugParser
from parsers.genobank.genobank_kontoauszug_parser import GenobankKontoauszugParser
from parsers.hypovereinsbank_parser import HypoVereinsbankParser
from parsers.sparkasse_parser import SparkasseParser
from parsers.vrbank_landau_parser import VRBankLandauParser
from parsers.vrbank_parser import VRBankParser

logger = logging.getLogger(__name__)


# ============================================================================
# IBAN → PARSER MAPPING
# ============================================================================
# WICHTIG: Alle 11 Konten hier eintragen!
# Format: 'IBAN': ParserClass

IBAN_PARSER_MAP = {
    # ========================================
    # GENOBANK - TAGESAUSZÜGE
    # ========================================
    # Format: "IBAN DE27741900000000057908"
    # Endsaldo: "(Endsaldo) +190.438,80 EUR"
    'DE27741900000000057908': GenobankTagesauszugParser,  # 57908 KK
    'DE68741900000001501500': GenobankTagesauszugParser,  # 1501500 HYU KK
    
    # ========================================
    # GENOBANK - KONTOAUSZÜGE
    # ========================================
    # Format: "IBAN: DE96 7419 0000 1700 0579 08"
    # Endsaldo: "neuer Kontostand vom 30.09.2024  14.854,72 H"
    'DE96741900001700057908': GenobankKontoauszugParser,  # 1700057908 Festgeld
    'DE58741900004700057908': GenobankKontoauszugParser,  # 4700057908 Darlehen
    'DE64741900000000022225': GenobankKontoauszugParser,  # 22225 Immo KK
    'DE06741900003700057908': GenobankKontoauszugParser,  # 3700057908 Darlehen
    'DE41741900000120057908': GenobankKontoauszugParser,  # KfW 120057908
    'DE94741900000020057908': GenobankKontoauszugParser,  # 20057908 Darlehen
    
    # ========================================
    # ANDERE BANKEN
    # ========================================
    'DE22741200710006407420': HypoVereinsbankParser,      # Hypovereinsbank KK
    'DE63741500000760036467': SparkasseParser,            # Sparkasse KK
    'DE76741910000000303585': VRBankLandauParser,         # VR Landau KK
}


class IBANParserFactory:
    """
    Factory zum Erstellen des richtigen Parsers basierend auf IBAN
    
    Workflow:
    1. IBAN aus PDF extrahieren (Header-Bereich!)
    2. IBAN in IBAN_PARSER_MAP nachschlagen
    3. Passenden Parser erstellen
    4. Fallback: Versuche alte Parser-Factory
    """
    
    @classmethod
    def get_parser(cls, pdf_path: str) -> Optional[BaseParser]:
        """
        Erstellt Parser basierend auf IBAN aus PDF
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            
        Returns:
            Parser-Instanz oder None bei Fehler
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            logger.error(f"❌ PDF nicht gefunden: {pdf_path}")
            return None
        
        logger.info(f"📄 Analysiere PDF: {pdf_path.name}")
        
        # 1. IBAN aus PDF extrahieren
        iban = cls._extract_iban_from_pdf(pdf_path)
        
        if not iban:
            logger.warning(f"⚠️ Keine IBAN in PDF gefunden: {pdf_path.name}")
            logger.info("💡 Versuche Fallback über Dateiname...")
            return cls._fallback_by_filename(pdf_path)
        
        logger.info(f"✓ IBAN gefunden: {iban}")
        
        # 2. Parser aus Map holen
        parser_class = IBAN_PARSER_MAP.get(iban)
        
        if parser_class:
            logger.info(f"✓ Parser gewählt: {parser_class.__name__}")
            return parser_class(str(pdf_path))
        
        # 3. IBAN nicht in Map -> Warnung
        logger.warning(f"⚠️ Keine Parser-Regel für IBAN: {iban}")
        logger.warning(f"💡 Bitte IBAN in IBAN_PARSER_MAP hinzufügen!")
        
        # 4. Fallback über Dateiname
        return cls._fallback_by_filename(pdf_path)
    
    @classmethod
    def _extract_iban_from_pdf(cls, pdf_path: Path) -> Optional[str]:
        """
        Extrahiert IBAN aus PDF-Inhalt
        
        Sucht nur im Header (erste 1000 Zeichen)!
        
        Unterstützt 2 Formate:
        1. "IBAN DE27741900000000057908"
        2. "IBAN: DE96 7419 0000 1700 0579 08"
        
        Args:
            pdf_path: Pfad zur PDF
            
        Returns:
            IBAN ohne Leerzeichen oder None
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    return None
                
                # Erste Seite, nur Header
                first_page_text = pdf.pages[0].extract_text() or ""
                header = first_page_text[:1000]
                
                # Suche IBAN-Zeile
                for line in header.split('\n'):
                    if 'IBAN' in line.upper():
                        # Format 1: IBAN DE27741900000000057908
                        match1 = re.search(r'IBAN\s+(DE\d{20})', line)
                        if match1:
                            return match1.group(1)
                        
                        # Format 2: IBAN: DE96 7419 0000 1700 0579 08
                        match2 = re.search(r'IBAN:\s+(DE\s*\d{2}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{2})', line)
                        if match2:
                            iban = match2.group(1)
                            # Entferne Leerzeichen
                            return re.sub(r'\s+', '', iban)
                
        except Exception as e:
            logger.error(f"❌ Fehler beim IBAN-Extrahieren: {e}")
        
        return None
    
    @classmethod
    def _fallback_by_filename(cls, pdf_path: Path) -> Optional[BaseParser]:
        """
        Fallback: Parser-Auswahl über Dateiname
        
        Nur wenn IBAN-Extraktion fehlschlägt!
        
        Args:
            pdf_path: Pfad zur PDF
            
        Returns:
            Parser-Instanz oder None
        """
        filename = pdf_path.name.lower()
        
        # Genobank (generisch)
        if 'genobank' in filename:
            logger.info("🔄 Fallback: GenobankTagesauszugParser (generisch)")
            return GenobankTagesauszugParser(str(pdf_path))
        
        # Sparkasse (auch Abkürzung "SPK")
        if 'sparkasse' in filename or 'spk' in filename:
            logger.info("🔄 Fallback: SparkasseParser")
            return SparkasseParser(str(pdf_path))
        
        # Hypovereinsbank (auch Abkürzungen "HV" und "HVB")
        if 'hypovereinsbank' in filename or 'hvb' in filename or filename.startswith('hv '):
            logger.info("🔄 Fallback: HypoVereinsbankParser")
            return HypoVereinsbankParser(str(pdf_path))
        
        # VR Bank Landau
        if 'vr bank' in filename or 'landau' in filename:
            logger.info("🔄 Fallback: VRBankLandauParser")
            return VRBankLandauParser(str(pdf_path))
        
        # VR Bank (generisch)
        if 'vrbank' in filename or 'vr-bank' in filename:
            logger.info("🔄 Fallback: VRBankParser")
            return VRBankParser(str(pdf_path))
        
        logger.error(f"❌ Kein Parser gefunden für: {filename}")
        return None
    
    @classmethod
    def get_supported_ibans(cls) -> list:
        """
        Gibt Liste aller unterstützten IBANs zurück
        
        Returns:
            Liste von IBANs
        """
        return list(IBAN_PARSER_MAP.keys())
    
    @classmethod
    def add_iban_mapping(cls, iban: str, parser_class: Type[BaseParser]) -> None:
        """
        Fügt neue IBAN → Parser Zuordnung hinzu
        
        Args:
            iban: IBAN ohne Leerzeichen
            parser_class: Parser-Klasse
        """
        IBAN_PARSER_MAP[iban] = parser_class
        logger.info(f"✓ Neue IBAN-Zuordnung: {iban} → {parser_class.__name__}")


# ============================================================================
# KOMPATIBILITÄTS-ALIAS
# ============================================================================
# Für bestehenden Code, der ParserFactory verwendet
class ParserFactory:
    """
    Alias für IBANParserFactory (Kompatibilität)
    """
    
    @staticmethod
    def create_parser(pdf_path: str) -> Optional[BaseParser]:
        return IBANParserFactory.get_parser(pdf_path)


# ============================================================================
# MAIN - TEST
# ============================================================================
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    print("=" * 60)
    print("IBAN-PARSER-FACTORY TEST")
    print("=" * 60)
    print()
    
    print(f"📋 Unterstützte IBANs: {len(IBANParserFactory.get_supported_ibans())}")
    print()
    
    for iban, parser_class in IBAN_PARSER_MAP.items():
        print(f"  {iban} → {parser_class.__name__}")
    
    print()
    print("=" * 60)
