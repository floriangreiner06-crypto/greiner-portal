#!/usr/bin/env python3
"""
GlobalCube Kontenrahmen Analyse
Analysiert Kontenrahmen.csv und extrahiert Konto-Mappings zu Struktur-IDs

Erstellt: TAG 184
Ziel: Vollständiges Mapping zwischen Konten und BWA-Positionen
"""

import zipfile
import csv
import xml.etree.ElementTree as ET
from collections import defaultdict
import json
from pathlib import Path

# GlobalCube Konfiguration
GLOBALCUBE_STRUCT_PATH = "/mnt/globalcube/GCStruct"
LATEST_ZIP = "AutohausGreiner_20250430_093310.zip"


def load_latest_structure():
    """Lädt die neueste Struktur-Datei"""
    zip_path = f"{GLOBALCUBE_STRUCT_PATH}/{LATEST_ZIP}"
    
    if not Path(zip_path).exists():
        print(f"❌ Datei nicht gefunden: {zip_path}")
        return None
    
    print(f"✅ Lade: {zip_path}")
    return zipfile.ZipFile(zip_path, 'r')


def parse_kontenrahmen_csv(zip_file):
    """
    Parst Kontenrahmen.csv und extrahiert Konto-Mappings
    
    Struktur:
    - Konto_Nr: Kontonummer (z.B. 810001)
    - Konto_Bezeichnung: Bezeichnung
    - Konto_Art: Art des Kontos
    - Kostenstelle: Kostenstelle
    - STK: ?
    - Ebene1-Ebene90: Struktur-IDs für verschiedene Ebenen
    """
    print("\n=== Parse Kontenrahmen.csv ===\n")
    
    with zip_file.open('Kontenrahmen/Kontenrahmen.csv') as f:
        content = f.read().decode('latin-1')
        reader = csv.DictReader(content.splitlines(), delimiter=';')
        
        konten = []
        bwa_relevant = []
        
        # Zähle Ebenen-Spalten
        ebene_columns = [col for col in reader.fieldnames if col.startswith('Ebene')]
        print(f"Gefundene Ebenen-Spalten: {len(ebene_columns)}")
        print(f"Erste 10: {ebene_columns[:10]}")
        
        for row_idx, row in enumerate(reader):
            konto_nr = row.get('Konto_Nr', '').strip()
            
            if not konto_nr or konto_nr.startswith('#'):
                continue
            
            # Extrahiere relevante Informationen
            konto_info = {
                'konto_nr': konto_nr,
                'bezeichnung': row.get('Konto_Bezeichnung', '').strip(),
                'konto_art': row.get('Konto_Art', '').strip(),
                'kostenstelle': row.get('Kostenstelle', '').strip(),
                'stk': row.get('STK', '').strip(),
            }
            
            # Extrahiere alle Ebenen-Mappings
            ebene_mappings = {}
            for ebene_col in ebene_columns:
                ebene_value = row.get(ebene_col, '').strip()
                if ebene_value:
                    ebene_mappings[ebene_col] = ebene_value
            
            konto_info['ebenen'] = ebene_mappings
            
            konten.append(konto_info)
            
            # Prüfe ob BWA-relevant (7xxxxx, 8xxxxx, 4xxxxx)
            konto_num = None
            try:
                # Entferne Suffixe wie "_H"
                konto_clean = konto_nr.split('_')[0]
                if konto_clean.isdigit():
                    konto_num = int(konto_clean)
            except:
                pass
            
            if konto_num:
                # BWA-relevante Bereiche
                if (700000 <= konto_num <= 899999) or (400000 <= konto_num <= 499999):
                    bwa_relevant.append(konto_info)
        
        print(f"Gesamt Konten: {len(konten)}")
        print(f"BWA-relevante Konten: {len(bwa_relevant)}")
        
        return {
            'all': konten,
            'bwa_relevant': bwa_relevant,
            'ebene_columns': ebene_columns
        }


def parse_struktur_guv_xml(zip_file):
    """
    Parst Struktur_GuV.xml und extrahiert BWA-Hierarchie
    """
    print("\n=== Parse Struktur_GuV.xml ===\n")
    
    with zip_file.open('Xml/Struktur_GuV.xml') as f:
        content = f.read().decode('utf-8')
        root = ET.fromstring(content)
        
        struktur = {}
        
        def parse_ebene(elem, parent_id=None, level=0):
            """Rekursiv parse Ebene-Elemente"""
            name = elem.get('Name', '')
            struktur_id = elem.get('StrukturId', '')
            
            indent = "  " * level
            print(f"{indent}{name} (ID: {struktur_id})")
            
            struktur[struktur_id] = {
                'name': name,
                'id': struktur_id,
                'parent_id': parent_id,
                'level': level,
                'children': []
            }
            
            # Parse Kinder
            for child in elem.findall('Ebene'):
                child_id = child.get('StrukturId', '')
                parse_ebene(child, struktur_id, level + 1)
                struktur[struktur_id]['children'].append(child_id)
        
        parse_ebene(root)
        
        print(f"\n✅ Struktur-IDs gefunden: {len(struktur)}")
        return struktur


def map_konten_to_struktur(konten_data, struktur_data):
    """
    Mappt Konten zu Struktur-IDs basierend auf Ebene-Spalten
    """
    print("\n=== Map Konten zu Struktur-IDs ===\n")
    
    # Finde die relevanteste Ebene (z.B. Ebene48 = Struktur_GuV)
    ebene_columns = konten_data['ebene_columns']
    
    # Suche nach Ebene48 (Struktur_GuV)
    guv_ebene = None
    for col in ebene_columns:
        if '48' in col or 'GuV' in col:
            guv_ebene = col
            break
    
    if not guv_ebene:
        # Versuche andere Ebenen
        print("⚠️  Ebene48 nicht gefunden, suche nach anderen Ebenen...")
        # Nehme die erste Ebene mit vielen Mappings
        ebene_counts = defaultdict(int)
        for konto in konten_data['bwa_relevant']:
            for ebene_col, ebene_value in konto['ebenen'].items():
                if ebene_value:
                    ebene_counts[ebene_col] += 1
        
        if ebene_counts:
            guv_ebene = max(ebene_counts.items(), key=lambda x: x[1])[0]
            print(f"✅ Verwende: {guv_ebene} ({ebene_counts[guv_ebene]} Mappings)")
    
    # Mappe Konten zu Struktur-IDs
    konto_to_struktur = defaultdict(list)
    struktur_to_konten = defaultdict(list)
    
    for konto in konten_data['bwa_relevant']:
        konto_nr = konto['konto_nr']
        struktur_id = konto['ebenen'].get(guv_ebene, '').strip()
        
        if struktur_id:
            konto_to_struktur[konto_nr].append(struktur_id)
            struktur_to_konten[struktur_id].append(konto_nr)
    
    print(f"✅ Konten mit Struktur-ID: {len(konto_to_struktur)}")
    print(f"✅ Struktur-IDs mit Konten: {len(struktur_to_konten)}")
    
    # Zeige Beispiele
    print("\n=== Beispiele ===")
    for struktur_id, konten_list in list(struktur_to_konten.items())[:10]:
        struktur_name = struktur_data.get(struktur_id, {}).get('name', 'Unbekannt')
        print(f"\nStruktur-ID {struktur_id} ({struktur_name}):")
        print(f"  Konten: {', '.join(konten_list[:10])}")
        if len(konten_list) > 10:
            print(f"  ... und {len(konten_list) - 10} weitere")
    
    return {
        'konto_to_struktur': dict(konto_to_struktur),
        'struktur_to_konten': dict(struktur_to_konten),
        'guv_ebene': guv_ebene
    }


def analyze_bwa_positions(mapping_data, struktur_data):
    """
    Analysiert BWA-Positionen und ihre Konten
    """
    print("\n=== Analysiere BWA-Positionen ===\n")
    
    struktur_to_konten = mapping_data['struktur_to_konten']
    
    # Wichtige BWA-Positionen
    wichtige_positionen = {
        '50': '1. Umsatzerlöse',
        '51': 'a) Neuwagen',
        '52': 'b) Gebrauchtwagen',
        '53': 'c) Teile & Zubehör',
        '54': 'd) Service',
        '60': '5. Materialaufwand',
        '62': 'aa) Neuwagen (Einsatz)',
        '63': 'ab) Gebrauchtwagen (Einsatz)',
        '70': '6. Personalaufwand',
        '75': 'ad) Ausbildung',
        '83': '8. Sonstige betriebliche Aufwendungen',
    }
    
    bwa_analyse = {}
    
    for struktur_id, name in wichtige_positionen.items():
        konten = struktur_to_konten.get(struktur_id, [])
        
        if konten:
            # Kategorisiere Konten
            umsatz_konten = [k for k in konten if k.startswith('8')]
            einsatz_konten = [k for k in konten if k.startswith('7')]
            kosten_konten = [k for k in konten if k.startswith('4')]
            
            bwa_analyse[struktur_id] = {
                'name': name,
                'konten': konten,
                'umsatz_konten': umsatz_konten,
                'einsatz_konten': einsatz_konten,
                'kosten_konten': kosten_konten,
                'anzahl': len(konten)
            }
            
            print(f"\n{name} (ID: {struktur_id}):")
            print(f"  Gesamt Konten: {len(konten)}")
            print(f"  Umsatz-Konten: {len(umsatz_konten)}")
            print(f"  Einsatz-Konten: {len(einsatz_konten)}")
            print(f"  Kosten-Konten: {len(kosten_konten)}")
            if umsatz_konten:
                print(f"  Beispiel Umsatz: {', '.join(umsatz_konten[:5])}")
            if einsatz_konten:
                print(f"  Beispiel Einsatz: {', '.join(einsatz_konten[:5])}")
            if kosten_konten:
                print(f"  Beispiel Kosten: {', '.join(kosten_konten[:5])}")
    
    return bwa_analyse


def save_results(konten_data, struktur_data, mapping_data, bwa_analyse):
    """Speichert Ergebnisse in JSON"""
    output_dir = Path("/opt/greiner-portal/docs/globalcube_analysis")
    output_dir.mkdir(exist_ok=True)
    
    results = {
        'konten_data': {
            'total': len(konten_data['all']),
            'bwa_relevant': len(konten_data['bwa_relevant']),
            'ebene_columns': konten_data['ebene_columns']
        },
        'struktur_data': struktur_data,
        'mapping_data': {
            'konto_to_struktur_count': len(mapping_data['konto_to_struktur']),
            'struktur_to_konten_count': len(mapping_data['struktur_to_konten']),
            'guv_ebene': mapping_data['guv_ebene']
        },
        'bwa_analyse': bwa_analyse
    }
    
    # Speichere als JSON
    json_path = output_dir / "kontenrahmen_analysis_tag184.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Ergebnisse gespeichert: {json_path}")
    
    # Speichere auch detaillierte Mappings
    mapping_path = output_dir / "konto_struktur_mapping_tag184.json"
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(mapping_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Mappings gespeichert: {mapping_path}")


def main():
    """Hauptfunktion"""
    print("=" * 80)
    print("GLOBALCUBE KONTENRAHMEN ANALYSE - TAG 184")
    print("=" * 80)
    
    # 1. Lade Struktur-Datei
    zip_file = load_latest_structure()
    if not zip_file:
        return
    
    # 2. Parse Kontenrahmen.csv
    konten_data = parse_kontenrahmen_csv(zip_file)
    
    # 3. Parse Struktur_GuV.xml
    struktur_data = parse_struktur_guv_xml(zip_file)
    
    # 4. Mappe Konten zu Struktur-IDs
    mapping_data = map_konten_to_struktur(konten_data, struktur_data)
    
    # 5. Analysiere BWA-Positionen
    bwa_analyse = analyze_bwa_positions(mapping_data, struktur_data)
    
    # 6. Speichere Ergebnisse
    save_results(konten_data, struktur_data, mapping_data, bwa_analyse)
    
    zip_file.close()
    
    print("\n" + "=" * 80)
    print("✅ Analyse abgeschlossen")
    print("=" * 80)


if __name__ == '__main__':
    main()
