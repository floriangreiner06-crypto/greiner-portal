#!/usr/bin/env python3
"""
Patch parser_factory.py - Fügt VRBankLandauParser sauber ein
"""

def patch_parser_factory():
    factory_path = '/opt/greiner-portal/parsers/parser_factory.py'
    
    # Lese aktuelle Datei
    with open(factory_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check ob VRBankLandauParser bereits importiert ist
    if 'from .vrbank_landau_parser import VRBankLandauParser' in content:
        print("✅ VRBankLandauParser bereits importiert!")
        return
    
    # 1. Import hinzufügen (nach VRBankParser)
    old_import = 'from .vrbank_parser import VRBankParser'
    new_import = '''from .vrbank_parser import VRBankParser
from .vrbank_landau_parser import VRBankLandauParser'''
    
    content = content.replace(old_import, new_import)
    
    # 2. Parser-Mapping erweitern
    old_mapping = '''        self.parsers = {
            'sparkasse': SparkasseParser,
            'hypovereinsbank': HypoVereinsbankParser,
            'vrbank': VRBankParser,
        }'''
    
    new_mapping = '''        self.parsers = {
            'sparkasse': SparkasseParser,
            'hypovereinsbank': HypoVereinsbankParser,
            'vrbank': VRBankParser,
            'vrbank_landau': VRBankLandauParser,
        }'''
    
    content = content.replace(old_mapping, new_mapping)
    
    # 3. Detection-Regeln hinzufügen (nach vrbank)
    old_detection = '''            'vrbank': [
                'vr bank',
                'volksbank',
                'raiffeisenbank'
            ],'''
    
    new_detection = '''            'vrbank': [
                'vr bank',
                'volksbank',
                'raiffeisenbank'
            ],
            'vrbank_landau': [
                'vr bank landau',
                'vr-bank landau',
                'vrbank landau'
            ],'''
    
    content = content.replace(old_detection, new_detection)
    
    # Schreibe zurück
    with open(factory_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ parser_factory.py erfolgreich gepatcht!")
    print("✅ VRBankLandauParser hinzugefügt")

if __name__ == '__main__':
    patch_parser_factory()
