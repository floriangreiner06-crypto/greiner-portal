#!/usr/bin/env python3
"""
GlobalCube XML-Struktur vollständig analysieren
Extrahiert Filter-Logik aus Struktur_GuV.xml und Struktur_Controlling.xml

Erstellt: TAG 182
"""

import xml.etree.ElementTree as ET
import os
import json
from pathlib import Path
import re

# TAG182: Direkt vom Network Share analysieren (immer aktuell!)
GLOBALCUBE_STRUCT_PATH = "/mnt/globalcube/GCStruct"


def find_latest_structure():
    """
    Findet die neueste Struktur-Datei
    """
    struct_path = Path(GLOBALCUBE_STRUCT_PATH)
    
    if not struct_path.exists():
        print(f"❌ Pfad nicht gefunden: {GLOBALCUBE_STRUCT_PATH}")
        return None
    
    # Suche nach neuestem ZIP
    zip_files = list(struct_path.glob("*.zip"))
    if zip_files:
        latest = max(zip_files, key=lambda p: p.stat().st_mtime)
        print(f"✅ Neueste Struktur: {latest.name}")
        return latest
    
    return None


def extract_zip_structure(zip_path):
    """
    Extrahiert Struktur aus ZIP
    """
    import zipfile
    import tempfile
    
    print(f"\n=== Extrahiere ZIP: {zip_path.name} ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)
        
        # Suche nach XML-Dateien
        xml_files = {}
        for root, dirs, files in os.walk(tmpdir):
            for file in files:
                if file.endswith('.xml'):
                    file_path = os.path.join(root, file)
                    if 'GuV' in file or 'guv' in file.lower():
                        xml_files['guv'] = file_path
                    elif 'Controlling' in file or 'controlling' in file.lower():
                        xml_files['controlling'] = file_path
                    elif 'config' in file.lower():
                        xml_files['config'] = file_path
        
        return xml_files


def parse_guv_structure(xml_file):
    """
    Parst Struktur_GuV.xml vollständig
    """
    print(f"\n=== Parse GuV-Struktur ===")
    print(f"Datei: {xml_file}\n")
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        structure = {
            'name': root.get('Name', ''),
            'struktur_id': root.get('StrukturId', ''),
            'ebenen': []
        }
        
        def parse_ebene(element, level=0):
            """Rekursive Funktion zum Parsen von Ebenen"""
            ebene = {
                'name': element.get('Name', ''),
                'level': level,
                'attribute': dict(element.attrib),
                'kinder': []
            }
            
            # Suche nach Filter-Logik in Attributen
            for key, value in element.attrib.items():
                if any(kw in key.lower() for kw in ['filter', 'konto', 'account', 'bedingung', 'condition']):
                    ebene['filter'] = {key: value}
            
            # Parse Kinder
            for child in element:
                if child.tag == 'Ebene':
                    child_ebene = parse_ebene(child, level + 1)
                    ebene['kinder'].append(child_ebene)
            
            return ebene
        
        # Parse alle Ebenen
        for ebene in root.findall('.//Ebene'):
            parsed_ebene = parse_ebene(ebene)
            structure['ebenen'].append(parsed_ebene)
        
        # Suche nach BWA-relevanten Positionen
        print("=== BWA-RELEVANTE POSITIONEN ===")
        bwa_positions = []
        
        def find_bwa_positions(element, path=""):
            name = element.get('Name', '')
            full_path = f"{path}/{name}" if path else name
            
            # Prüfe ob BWA-relevant
            bwa_keywords = ['umsatz', 'einsatz', 'kosten', 'deckungsbeitrag', 'betriebsergebnis', 
                          'variable', 'direkte', 'indirekte', 'bruttoertrag']
            
            if any(kw in name.lower() for kw in bwa_keywords):
                bwa_positions.append({
                    'name': name,
                    'path': full_path,
                    'attribute': dict(element.attrib)
                })
            
            for child in element:
                if child.tag == 'Ebene':
                    find_bwa_positions(child, full_path)
        
        find_bwa_positions(root)
        
        print(f"Gefundene BWA-Positionen: {len(bwa_positions)}")
        for pos in bwa_positions[:20]:  # Erste 20
            print(f"  - {pos['name']} ({pos['path']})")
        
        structure['bwa_positions'] = bwa_positions
        
        return structure
        
    except Exception as e:
        print(f"❌ Fehler beim Parsen: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_filter_logic(xml_file):
    """
    Extrahiert Filter-Logik aus XML
    """
    print(f"\n=== Extrahiere Filter-Logik ===")
    
    try:
        with open(xml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Suche nach SQL-ähnlichen Ausdrücken
        sql_patterns = [
            r'(?:WHERE|AND|OR)\s+([^;]+)',
            r'(?:nominal_account_number|konto)\s*(?:BETWEEN|IN|>=|<=|>|<|=)\s*([^;,\s]+)',
            r'(?:411\d{3}|489\d{3}|410021|891\d{3})',
            r'(?:branch_number|subsidiary)[\s=]+([0-9]+)',
            r'(?:6\.\s*Ziffer|5\.\s*Ziffer)[\s=]+([\'"]?[0-9][\'"]?)',
        ]
        
        filters = {}
        
        for pattern in sql_patterns:
            matches = re.findall(pattern, content, re.I)
            if matches:
                filter_key = pattern[:50]
                filters[filter_key] = matches[:10]  # Erste 10 Matches
                print(f"\nGefunden ({pattern[:50]}):")
                for match in matches[:5]:
                    print(f"  {match[:200]}")
        
        return filters
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return {}


def main():
    """
    Hauptfunktion
    """
    print("=" * 80)
    print("GlobalCube XML-Struktur Analyse")
    print("=" * 80)
    
    # 1. Finde neueste Struktur
    latest_zip = find_latest_structure()
    
    if not latest_zip:
        # Versuche direkt XML-Dateien zu finden
        struct_path = Path(GLOBALCUBE_STRUCT_PATH)
        guv_xml = None
        controlling_xml = None
        
        # Suche rekursiv nach XML-Dateien
        for xml_file in struct_path.rglob("Struktur_GuV.xml"):
            guv_xml = xml_file
            break
        
        for xml_file in struct_path.rglob("Struktur_Controlling.xml"):
            controlling_xml = xml_file
            break
        
        if guv_xml:
            print(f"\n✅ GuV-XML gefunden: {guv_xml}")
            structure = parse_guv_structure(str(guv_xml))
            filters = extract_filter_logic(str(guv_xml))
            
            # Speichere Ergebnisse
            output_file = "/tmp/globalcube_guv_structure.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'structure': structure,
                    'filters': filters
                }, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Ergebnisse gespeichert: {output_file}")
        
        if controlling_xml:
            print(f"\n✅ Controlling-XML gefunden: {controlling_xml}")
            # TODO: Parse Controlling-XML
    else:
        # Extrahiere aus ZIP
        xml_files = extract_zip_structure(latest_zip)
        
        if 'guv' in xml_files:
            structure = parse_guv_structure(xml_files['guv'])
            filters = extract_filter_logic(xml_files['guv'])
            
            # Speichere Ergebnisse
            output_file = "/tmp/globalcube_guv_structure.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'structure': structure,
                    'filters': filters
                }, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Ergebnisse gespeichert: {output_file}")


if __name__ == '__main__':
    main()
