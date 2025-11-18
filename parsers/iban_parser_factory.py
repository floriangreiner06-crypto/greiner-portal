#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IBAN-Parser-Factory (Version 1.3 - mit GenobankOnlineParser)
==============================================================

Automatische Parser-Wahl basierend auf IBAN-Extraktion aus PDF.

ÄNDERUNGEN v1.3:
- GenobankOnlineParser für Genobank Online-Banking Format
- Verbesserte Fallback-Logik: "Genobank Auszug" → GenobankOnlineParser
- Unterscheidung: Tagesauszug vs Kontoauszug vs Online-Export

ÄNDERUNGEN v1.2:
- SparkasseOnlineParser integriert für Online-Banking Format
- Genobank-Kontonummern-Fallbacks

Autor: Claude (Tag 60)
Datum: 2025-11-18
"""

import re
import logging
from pathlib import Path
from typing import Optional, Type

# Import aller Parser
from .base_parser import BaseParser
from .genobank.genobank_tagesauszug_parser import GenobankTagesauszugParser
from .genobank.genobank_kontoauszug_parser import GenobankKontoauszugParser
from .genobank_online_parser import GenobankOnlineParser
from .hypovereinsbank_parser import HypoVereinsbankParser
from .sparkasse_online_parser import SparkasseOnlineParser
from .vrbank_landau_parser import VRBankLandauParser

logger = logging.getLogger(__name__)


# IBAN → Parser Mapping (11 Konten)
IBAN_PARSER_MAP = {
    # Genobank Tagesauszüge (Format 1)
    'DE27741900000000057908': GenobankTagesauszugParser,  # Konto-ID 5
    'DE70741900000000057903': GenobankTagesauszugParser,  # Konto-ID 10
    
    # Genobank Kontoauszüge (Format 2)
    'DE96741900001700057908': GenobankKontoauszugParser,  # Konto-ID 6
    'DE55741900001703057908': GenobankKontoauszugParser,  # Konto-ID 7
    'DE68741900001704057908': GenobankKontoauszugParser,  # Konto-ID 8
    'DE36741900001705057908': GenobankKontoauszugParser,  # Konto-ID 11
    'DE20741900001706057908': GenobankKontoauszugParser,  # Konto-ID 12
    'DE02741900001709057908': GenobankKontoauszugParser,  # Konto-ID 13
    
    # HypoVereinsbank
    'DE12700202700034612702': HypoVereinsbankParser,      # Konto-ID 9
    
    # Sparkasse Online-Banking (WICHTIG: Online-Format!)
    'DE63741500000760036467': SparkasseOnlineParser,      # Konto-ID 1
    
    # VR Bank Landau
    'DE39548625000007303030': VRBankLandauParser,         # Konto-ID 14
}


class IBANParserFactory:
    """
    Factory zur automatischen Parser-Auswahl basierend auf IBAN.
    
    Funktionsweise:
    1. Extrahiert IBAN aus PDF-Header (erste 1000 Zeichen)
    2. Matched IBAN gegen IBAN_PARSER_MAP
    3. Erstellt entsprechenden Parser
    4. Fallback über Dateiname wenn IBAN-Extraktion fehlschlägt
    """
    
    @staticmethod
    def extract_iban_from_pdf(pdf_path: Path) -> Optional[str]:
        """
        Extrahiert IBAN aus PDF-Header.
        
        Sucht nach Pattern:
        - DE + 20 Ziffern
        - Mit oder ohne Leerzeichen
        - In den ersten 1000 Zeichen
        
        Returns:
            IBAN ohne Leerzeichen oder None
        """
        try:
            import pdfplumber
            
            with pdfplumber.open(str(pdf_path)) as pdf:
                if not pdf.pages:
                    return None
                
                # Erste 1000 Zeichen der ersten Seite
                text = pdf.pages[0].extract_text()
                if not text:
                    return None
                
                text = text[:1000]
                
                # Pattern: DE + 20 Ziffern (mit optionalen Leerzeichen)
                # Beispiele:
                # - "IBAN DE27741900000000057908"
                # - "IBAN: DE96 7419 0000 1700 0579 08"
                # - "DE63 7415 0000 0760 0364 67"
                
                pattern = r'DE\d{2}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{2}'
                match = re.search(pattern, text)
                
                if match:
                    iban = match.group().replace(' ', '')
                    logger.debug(f"IBAN aus PDF extrahiert: {iban}")
                    return iban
                
                logger.debug(f"Keine IBAN in {pdf_path.name} gefunden")
                return None
                
        except Exception as e:
            logger.error(f"Fehler bei IBAN-Extraktion aus {pdf_path}: {e}")
            return None
    
    @staticmethod
    def get_parser_by_iban(iban: str) -> Optional[Type[BaseParser]]:
        """
        Ermittelt Parser-Klasse anhand IBAN.
        
        Args:
            iban: IBAN (mit oder ohne Leerzeichen)
        
        Returns:
            Parser-Klasse oder None
        """
        # Normalisiere IBAN (entferne Leerzeichen)
        iban_clean = iban.replace(' ', '').upper()
        
        parser_class = IBAN_PARSER_MAP.get(iban_clean)
        
        if parser_class:
            logger.debug(f"IBAN {iban_clean} → {parser_class.__name__}")
        else:
            logger.debug(f"Keine Parser-Zuordnung für IBAN {iban_clean}")
        
        return parser_class
    
    @staticmethod
    def get_parser_by_filename(pdf_path: Path) -> Optional[Type[BaseParser]]:
        """
        Fallback: Parser-Wahl über Dateinamen.
        
        Patterns:
        - 'genobank', '57908', '1501500', '1700057908', etc. → Genobank-Parser
        - 'sparkasse', 'spk' → SparkasseOnlineParser
        - 'hypovereinsbank', 'hvb', 'hv ' → HypoVereinsbankParser
        - 'vr bank', 'landau', '303585' → VRBankLandauParser
        """
        filename_lower = pdf_path.name.lower()
        
        # Genobank (verschiedene Kontonummern)
        genobank_patterns = ['genobank', '57908', '1501500', '22225', '1700057908', 
                             '1703057908', '1704057908', '1705057908', '1706057908', '1709057908']
        if any(x in filename_lower for x in genobank_patterns):
            # Unterscheide: Tagesauszug vs Kontoauszug vs Online-Export
            if 'tagesauszug' in filename_lower:
                logger.debug(f"Dateiname '{pdf_path.name}' → GenobankTagesauszugParser (Fallback)")
                return GenobankTagesauszugParser
            elif 'auszug' in filename_lower and 'nr.' not in filename_lower:
                # "Genobank Auszug Auto Greiner" → Online-Format
                logger.debug(f"Dateiname '{pdf_path.name}' → GenobankOnlineParser (Fallback)")
                return GenobankOnlineParser
            else:
                # "1501500_2025_Nr.010_Kontoauszug" → Klassischer Kontoauszug
                logger.debug(f"Dateiname '{pdf_path.name}' → GenobankKontoauszugParser (Fallback)")
                return GenobankKontoauszugParser
        
        # Sparkasse (auch Online-Format)
        if any(x in filename_lower for x in ['sparkasse', 'spk']):
            logger.debug(f"Dateiname '{pdf_path.name}' → SparkasseOnlineParser (Fallback)")
            return SparkasseOnlineParser
        
        # HypoVereinsbank
        if any(x in filename_lower for x in ['hypovereinsbank', 'hvb', 'hv ']):
            logger.debug(f"Dateiname '{pdf_path.name}' → HypoVereinsbankParser (Fallback)")
            return HypoVereinsbankParser
        
        # VR Bank Landau
        if any(x in filename_lower for x in ['vr bank', 'landau', '303585']):
            logger.debug(f"Dateiname '{pdf_path.name}' → VRBankLandauParser (Fallback)")
            return VRBankLandauParser
        
        logger.warning(f"Keine Parser-Zuordnung für '{pdf_path.name}' möglich")
        return None
    
    @classmethod
    def get_parser(cls, pdf_path: str) -> Optional[BaseParser]:
        """
        Hauptmethode: Erstellt passenden Parser für PDF.
        
        Strategie:
        1. IBAN aus PDF extrahieren
        2. Parser via IBAN_PARSER_MAP zuordnen
        3. Fallback über Dateinamen
        4. None wenn keine Zuordnung möglich
        
        Args:
            pdf_path: Pfad zur PDF-Datei
        
        Returns:
            Parser-Instanz oder None
        """
        pdf_path_obj = Path(pdf_path)
        
        if not pdf_path_obj.exists():
            logger.error(f"PDF nicht gefunden: {pdf_path}")
            return None
        
        # Strategie 1: IBAN-basiert
        iban = cls.extract_iban_from_pdf(pdf_path_obj)
        if iban:
            parser_class = cls.get_parser_by_iban(iban)
            if parser_class:
                logger.info(f"✅ {pdf_path_obj.name} → {parser_class.__name__} (IBAN)")
                return parser_class(str(pdf_path))
        
        # Strategie 2: Dateiname-basiert
        parser_class = cls.get_parser_by_filename(pdf_path_obj)
        if parser_class:
            logger.info(f"✅ {pdf_path_obj.name} → {parser_class.__name__} (Dateiname)")
            return parser_class(str(pdf_path))
        
        # Keine Zuordnung möglich
        logger.error(f"❌ Kein Parser für {pdf_path_obj.name} gefunden!")
        return None
    
    @classmethod
    def get_supported_ibans(cls):
        """Gibt Liste aller unterstützten IBANs zurück"""
        return list(IBAN_PARSER_MAP.keys())
    
    @classmethod
    def get_parser_info(cls):
        """Gibt Übersicht aller Parser und deren IBANs zurück"""
        from collections import defaultdict
        
        parser_ibans = defaultdict(list)
        for iban, parser_class in IBAN_PARSER_MAP.items():
            parser_ibans[parser_class.__name__].append(iban)
        
        return dict(parser_ibans)


# Convenience-Funktion
def get_parser_for_pdf(pdf_path: str) -> Optional[BaseParser]:
    """
    Convenience-Funktion für direkte Verwendung.
    
    Args:
        pdf_path: Pfad zur PDF-Datei
    
    Returns:
        Parser-Instanz oder None
    
    Example:
        >>> parser = get_parser_for_pdf("/path/to/kontoauszug.pdf")
        >>> if parser:
        ...     transactions = parser.parse()
    """
    return IBANParserFactory.get_parser(pdf_path)


# CLI für Testing
if __name__ == "__main__":
    import sys
    
    print("=" * 80)
    print("IBAN-PARSER-FACTORY - INFO")
    print("=" * 80)
    
    print("\nUnterstützte IBANs und Parser:")
    print("-" * 80)
    
    parser_info = IBANParserFactory.get_parser_info()
    for parser_name, ibans in sorted(parser_info.items()):
        print(f"\n{parser_name}:")
        for iban in ibans:
            print(f"  - {iban}")
    
    print("\n" + "=" * 80)
    print(f"Gesamt: {len(IBAN_PARSER_MAP)} Konten")
    print("=" * 80)
    
    # Test mit PDF wenn angegeben
    if len(sys.argv) > 1:
        test_pdf = sys.argv[1]
        print(f"\n🔍 Teste mit: {test_pdf}")
        print("-" * 80)
        
        parser = IBANParserFactory.get_parser(test_pdf)
        if parser:
            print(f"✅ Parser: {parser.__class__.__name__}")
            print(f"   IBAN: {parser.iban}")
        else:
            print("❌ Kein passender Parser gefunden")
