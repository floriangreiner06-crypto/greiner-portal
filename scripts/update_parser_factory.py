#!/usr/bin/env python3
"""
Script zum sauberen Update der parser_factory.py
Fügt VRBankLandauParser hinzu
"""

import re
import shutil
from datetime import datetime

FACTORY_PATH = "/opt/greiner-portal/parsers/parser_factory.py"
BACKUP_PATH = f"{FACTORY_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

print("=" * 80)
print("🔧 PARSER FACTORY UPDATE - VRBankLandauParser hinzufügen")
print("=" * 80)

# 1. Backup erstellen
print(f"\n📦 Erstelle Backup: {BACKUP_PATH}")
shutil.copy2(FACTORY_PATH, BACKUP_PATH)

# 2. Datei lesen
with open(FACTORY_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# 3. Import hinzufügen
print("\n✅ Füge Import hinzu...")
if 'from .vrbank_landau_parser import VRBankLandauParser' not in content:
    content = content.replace(
        'from .vrbank_parser import VRBankParser',
        'from .vrbank_parser import VRBankParser\nfrom .vrbank_landau_parser import VRBankLandauParser'
    )
    print("   ✓ Import hinzugefügt")
else:
    print("   ⚠️  Import bereits vorhanden")

# 4. FILENAME_PATTERNS erweitern
print("\n✅ Erweitere FILENAME_PATTERNS...")
if "'landau': VRBankLandauParser," not in content:
    # Finde FILENAME_PATTERNS und füge nach 'vr bank' hinzu
    pattern = r"('vr bank': VRBankParser,)"
    replacement = r"\1\n        'vr bank landau': VRBankLandauParser,\n        'landau': VRBankLandauParser,"
    content = re.sub(pattern, replacement, content)
    print("   ✓ FILENAME_PATTERNS erweitert")
else:
    print("   ⚠️  Bereits vorhanden")

# 5. CONTENT_PATTERNS erweitern
print("\n✅ Erweitere CONTENT_PATTERNS...")
if "'VR-Bank Landau-Mengkofen': VRBankLandauParser," not in content:
    pattern = r"('VR GenoBank': VRBankParser,)"
    replacement = r"\1\n        'VR-Bank Landau-Mengkofen': VRBankLandauParser,\n        'Landau-Mengkofen': VRBankLandauParser,"
    content = re.sub(pattern, replacement, content)
    print("   ✓ CONTENT_PATTERNS erweitert")
else:
    print("   ⚠️  Bereits vorhanden")

# 6. parser_map erweitern
print("\n✅ Erweitere parser_map...")
if "'vrbank_landau': VRBankLandauParser," not in content:
    pattern = r"('vrbank': VRBankParser,)"
    replacement = r"\1\n            'vrbank_landau': VRBankLandauParser,"
    content = re.sub(pattern, replacement, content)
    print("   ✓ parser_map erweitert")
else:
    print("   ⚠️  Bereits vorhanden")

# 7. get_parser_info erweitern
print("\n✅ Erweitere get_parser_info...")
if "'vrbank_landau':" not in content:
    # Finde das Ende des hypovereinsbank Blocks
    pattern = r"('hypovereinsbank': \{[^}]+\})"
    
    vrbank_landau_info = """,
            'vrbank_landau': {
                'class': VRBankLandauParser,
                'name': 'VR Bank Landau-Mengkofen',
                'keywords': ['vr bank landau', 'landau-mengkofen', 'landau'],
                'format': 'Name + Betrag / IBAN + Datum / Verwendungszweck'
            }"""
    
    replacement = r"\1" + vrbank_landau_info
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    print("   ✓ get_parser_info erweitert")
else:
    print("   ⚠️  Bereits vorhanden")

# 8. Datei schreiben
print(f"\n💾 Schreibe aktualisierte Datei...")
with open(FACTORY_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n" + "=" * 80)
print("✅ PARSER FACTORY ERFOLGREICH AKTUALISIERT!")
print("=" * 80)

# 9. Verifizierung
print("\n🔍 Verifizierung:")
with open(FACTORY_PATH, 'r') as f:
    check_content = f.read()
    
checks = [
    ('Import', 'from .vrbank_landau_parser import VRBankLandauParser'),
    ('FILENAME_PATTERNS', "'landau': VRBankLandauParser"),
    ('CONTENT_PATTERNS', "'VR-Bank Landau-Mengkofen': VRBankLandauParser"),
    ('parser_map', "'vrbank_landau': VRBankLandauParser"),
    ('get_parser_info', "'vrbank_landau':")
]

all_ok = True
for name, check in checks:
    if check in check_content:
        print(f"   ✅ {name}")
    else:
        print(f"   ❌ {name} - FEHLT!")
        all_ok = False

if all_ok:
    print("\n🎉 Alle Checks erfolgreich!")
else:
    print("\n⚠️  Einige Checks fehlgeschlagen - bitte manuell prüfen!")

print(f"\n📦 Backup gespeichert unter: {BACKUP_PATH}")
