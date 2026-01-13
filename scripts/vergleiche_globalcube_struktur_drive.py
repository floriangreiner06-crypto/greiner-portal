#!/usr/bin/env python3
"""
Vergleich GlobalCube Struktur mit DRIVE BWA-Logik
Analysiert XML-Strukturen und vergleicht mit DRIVE-Implementierung

Erstellt: TAG 184
Ziel: Identifikation von Differenzen zwischen GlobalCube und DRIVE
"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import json

# GlobalCube Konfiguration
GLOBALCUBE_STRUCT_PATH = "/mnt/globalcube/GCStruct"
LATEST_ZIP = "AutohausGreiner_20250430_093310.zip"


def parse_xml_structure(zip_file, xml_path):
    """Parst eine XML-Struktur-Datei"""
    with zip_file.open(xml_path) as f:
        content = f.read().decode('utf-8')
        root = ET.fromstring(content)
        return root


def extract_struktur_hierarchy(root, struktur_dict=None, level=0):
    """Extrahiert vollständige Hierarchie aus XML"""
    if struktur_dict is None:
        struktur_dict = {}
    
    name = root.get('Name', '')
    struktur_id = root.get('StrukturId', '')
    
    struktur_dict[struktur_id] = {
        'name': name,
        'id': struktur_id,
        'level': level,
        'parent_id': None,  # Wird später gesetzt
        'children': []
    }
    
    # Parse Kinder
    for child in root.findall('Ebene'):
        child_id = child.get('StrukturId', '')
        struktur_dict[struktur_id]['children'].append(child_id)
        extract_struktur_hierarchy(child, struktur_dict, level + 1)
        struktur_dict[child_id]['parent_id'] = struktur_id
    
    return struktur_dict


def analyze_guv_structure(zip_file):
    """Analysiert Struktur_GuV.xml"""
    print("\n=== Analysiere Struktur_GuV.xml ===\n")
    
    root = parse_xml_structure(zip_file, 'Xml/Struktur_GuV.xml')
    struktur = extract_struktur_hierarchy(root)
    
    # Wichtige BWA-Positionen
    wichtige_positionen = {
        '50': '1. Umsatzerlöse',
        '51': 'a) Neuwagen',
        '52': 'b) Gebrauchtwagen',
        '60': '5. Materialaufwand',
        '70': '6. Personalaufwand',
        '75': 'ad) Ausbildung',
        '83': '8. Sonstige betriebliche Aufwendungen',
    }
    
    print("Wichtige BWA-Positionen:")
    for struktur_id, name in wichtige_positionen.items():
        if struktur_id in struktur:
            info = struktur[struktur_id]
            print(f"  {name} (ID: {struktur_id})")
            if info['children']:
                print(f"    Kinder: {len(info['children'])}")
    
    return struktur


def analyze_controlling_structure(zip_file):
    """Analysiert Struktur_Controlling.xml"""
    print("\n=== Analysiere Struktur_Controlling.xml ===\n")
    
    root = parse_xml_structure(zip_file, 'Xml/Struktur_Controlling.xml')
    struktur = extract_struktur_hierarchy(root)
    
    # Wichtige Controlling-Positionen
    wichtige_positionen = {
        '9': 'Umsatz Opel',
        '11': 'EW NW Opel',
        '12': 'Umsatz GW',
        '13': 'EW GW',
        '16': 'Umsatz Service',
        '22': 'EW Serv. ges.',
        '25': 'Umsatz Teile gesamt',
        '30': 'EW OT/ATZ/VW/Honda Teile',
        '37': 'Personalaufwand',
        '38': 'Summe betriebl. Aufwand',
    }
    
    print("Wichtige Controlling-Positionen:")
    for struktur_id, name in wichtige_positionen.items():
        if struktur_id in struktur:
            info = struktur[struktur_id]
            print(f"  {name} (ID: {struktur_id})")
            if info['children']:
                print(f"    Kinder: {len(info['children'])}")
                for child_id in info['children'][:5]:
                    if child_id in struktur:
                        print(f"      - {struktur[child_id]['name']} (ID: {child_id})")
    
    return struktur


def compare_with_drive_logic():
    """Vergleicht GlobalCube-Struktur mit DRIVE BWA-Logik"""
    print("\n=== Vergleich mit DRIVE BWA-Logik ===\n")
    
    # DRIVE BWA-Bereiche (aus controlling_api.py)
    drive_bereiche = {
        'NW': {
            'erlos_prefix': '81',
            'einsatz_prefix': '71',
        },
        'GW': {
            'erlos_prefix': '82',
            'einsatz_prefix': '72',
        },
        'Teile': {
            'erlos_prefix': '83',
            'einsatz_prefix': '73',
        },
        'Service': {
            'erlos_prefix': '84',
            'einsatz_prefix': '74',
        },
    }
    
    print("DRIVE BWA-Bereiche:")
    for bereich, config in drive_bereiche.items():
        print(f"  {bereich}:")
        print(f"    Umsatz: {config['erlos_prefix']}xxxx")
        print(f"    Einsatz: {config['einsatz_prefix']}xxxx")
    
    print("\n✅ Vergleich:")
    print("  - DRIVE verwendet Kontonummer-Präfixe (81xxxx, 82xxxx, etc.)")
    print("  - GlobalCube verwendet Struktur-IDs (50, 51, 52, etc.)")
    print("  - Mapping zwischen Konten und Struktur-IDs fehlt in CSV")
    print("  - Mögliche Lösung: Analyse von Excel-Exports oder Portal-Reports")
    
    return drive_bereiche


def generate_recommendations(guv_struktur, controlling_struktur):
    """Generiert Empfehlungen basierend auf Analyse"""
    print("\n=== Empfehlungen ===\n")
    
    recommendations = []
    
    # 1. Ausbildung-Position
    if '75' in guv_struktur:
        recommendations.append({
            'position': 'Ausbildung (ID: 75)',
            'finding': 'Separate Position in GuV-Struktur gefunden',
            'recommendation': '411xxx sollte NICHT in direkten Kosten sein (bereits korrekt in DRIVE)',
            'status': '✅ Bestätigt'
        })
    
    # 2. Struktur-IDs vs. Konten
    recommendations.append({
        'position': 'Konto-Mappings',
        'finding': 'Kontenrahmen.csv enthält keine direkten BWA-Konten (7xxxxx/8xxxxx/4xxxxx)',
        'recommendation': 'Alternative Quellen nutzen: Excel-Exports, Portal-Reports, oder f_belege Cube',
        'status': '⏳ Offen'
    })
    
    # 3. Controlling-Struktur
    if '37' in controlling_struktur:
        recommendations.append({
            'position': 'Personalaufwand (ID: 37)',
            'finding': 'Separate Position in Controlling-Struktur',
            'recommendation': 'Prüfe ob Personalaufwand-Konten korrekt zugeordnet sind',
            'status': '⏳ Zu prüfen'
        })
    
    for rec in recommendations:
        print(f"{rec['status']} {rec['position']}:")
        print(f"  Finding: {rec['finding']}")
        print(f"  Recommendation: {rec['recommendation']}")
        print()
    
    return recommendations


def main():
    """Hauptfunktion"""
    print("=" * 80)
    print("VERGLEICH GLOBALCUBE STRUKTUR MIT DRIVE BWA-LOGIK - TAG 184")
    print("=" * 80)
    
    # 1. Lade Struktur-Datei
    zip_path = f"{GLOBALCUBE_STRUCT_PATH}/{LATEST_ZIP}"
    if not Path(zip_path).exists():
        print(f"❌ Datei nicht gefunden: {zip_path}")
        return
    
    zip_file = zipfile.ZipFile(zip_path, 'r')
    
    # 2. Analysiere GuV-Struktur
    guv_struktur = analyze_guv_structure(zip_file)
    
    # 3. Analysiere Controlling-Struktur
    controlling_struktur = analyze_controlling_structure(zip_file)
    
    # 4. Vergleiche mit DRIVE
    drive_bereiche = compare_with_drive_logic()
    
    # 5. Generiere Empfehlungen
    recommendations = generate_recommendations(guv_struktur, controlling_struktur)
    
    # 6. Speichere Ergebnisse
    output_dir = Path("/opt/greiner-portal/docs/globalcube_analysis")
    output_dir.mkdir(exist_ok=True)
    
    results = {
        'guv_struktur': guv_struktur,
        'controlling_struktur': controlling_struktur,
        'drive_bereiche': drive_bereiche,
        'recommendations': recommendations
    }
    
    json_path = output_dir / "struktur_vergleich_tag184.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Ergebnisse gespeichert: {json_path}")
    
    zip_file.close()
    
    print("\n" + "=" * 80)
    print("✅ Analyse abgeschlossen")
    print("=" * 80)


if __name__ == '__main__':
    main()
