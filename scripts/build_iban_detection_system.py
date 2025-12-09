#!/usr/bin/env python3
"""
Baut IBAN-basiertes Parser-Detection-System
"""
import re

def build_iban_system():
    factory_path = '/opt/greiner-portal/parsers/parser_factory.py'
    
    with open(factory_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. IBAN_TO_PARSER Mapping hinzufügen (nach CONTENT_PATTERNS)
    iban_mapping = '''
    # IBAN → Parser Mapping (höchste Priorität!)
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
'''
    
    # Finde wo CONTENT_PATTERNS endet
    patterns_end = content.find('    @classmethod\n    def create_parser')
    if patterns_end == -1:
        print("❌ Einfügepunkt nicht gefunden!")
        return
    
    # Füge IBAN_TO_PARSER vor create_parser ein
    content = content[:patterns_end] + iban_mapping + '\n' + content[patterns_end:]
    
    # 2. Neue Methode _detect_by_iban hinzufügen (vor _detect_by_content)
    detect_by_iban_method = '''
    @classmethod
    def _detect_by_iban(cls, pdf_path: str) -> Optional[type]:
        """
        Erkennt Parser anhand der IBAN im PDF
        
        Dies ist die PRÄZISESTE Methode - eine IBAN ist eindeutig!
        
        Returns:
            Parser-Klasse oder None
        """
        try:
            import pdfplumber
            
            with pdfplumber.open(pdf_path) as pdf:
                if not pdf.pages:
                    return None
                
                # Erste Seite lesen
                first_page_text = pdf.pages[0].extract_text()
                if not first_page_text:
                    return None
                
                # Suche alle IBANs (DE + 20 Ziffern)
                iban_pattern = r'DE\d{20}'
                found_ibans = re.findall(iban_pattern, first_page_text)
                
                if not found_ibans:
                    return None
                
                # Prüfe jede gefundene IBAN gegen Mapping
                for iban in found_ibans:
                    if iban in cls.IBAN_TO_PARSER:
                        parser_class = cls.IBAN_TO_PARSER[iban]
                        logger.info(f"✅ IBAN-Match: {iban} → {parser_class.__name__}")
                        return parser_class
                
                return None
                
        except Exception as e:
            logger.error(f"Fehler bei IBAN-Detection: {e}")
            return None

'''
    
    # Füge Methode vor _detect_by_content ein
    content_detect_pos = content.find('    @classmethod\n    def _detect_by_content')
    if content_detect_pos == -1:
        print("❌ _detect_by_content nicht gefunden!")
        return
    
    content = content[:content_detect_pos] + detect_by_iban_method + content[content_detect_pos:]
    
    # 3. Ändere create_parser um zuerst IBAN zu prüfen
    old_detection_order = '''        # 1. Versuch: Dateinamen-basierte Erkennung
        parser_class = cls._detect_by_filename(pdf_path_obj)
        if parser_class:
            logger.info(f"✅ Parser erkannt (Dateiname): {parser_class.__name__}")
            return parser_class(pdf_path)

        # 2. Versuch: Inhalt-basierte Erkennung
        parser_class = cls._detect_by_content(pdf_path)
        if parser_class:
            logger.info(f"✅ Parser erkannt (Inhalt): {parser_class.__name__}")
            return parser_class(pdf_path)'''
    
    new_detection_order = '''        # 1. Versuch: IBAN-basierte Erkennung (HÖCHSTE PRIORITÄT!)
        parser_class = cls._detect_by_iban(pdf_path)
        if parser_class:
            logger.info(f"✅ Parser erkannt (IBAN): {parser_class.__name__}")
            return parser_class(pdf_path)

        # 2. Versuch: Inhalt-basierte Erkennung (Bank-Namen)
        parser_class = cls._detect_by_content(pdf_path)
        if parser_class:
            logger.info(f"✅ Parser erkannt (Inhalt): {parser_class.__name__}")
            return parser_class(pdf_path)

        # 3. Versuch: Dateinamen-basierte Erkennung (Fallback)
        parser_class = cls._detect_by_filename(pdf_path_obj)
        if parser_class:
            logger.info(f"✅ Parser erkannt (Dateiname): {parser_class.__name__}")
            return parser_class(pdf_path)'''
    
    content = content.replace(old_detection_order, new_detection_order)
    
    # Schreibe zurück
    with open(factory_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ IBAN-basiertes Detection-System implementiert!")
    print("✅ Priorität: IBAN → Inhalt → Dateiname")
    print("✅ 11 IBANs im System gemappt")

if __name__ == '__main__':
    build_iban_system()
