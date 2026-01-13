#!/usr/bin/env python3
"""
GlobalCube Excel Parser - Vollständig
Parst Excel-Export und extrahiert BWA-Werte für Vergleich mit DRIVE

Erstellt: TAG 184
"""

import zipfile
import xml.etree.ElementTree as ET
import re
import json
from pathlib import Path
from collections import defaultdict

EXCEL_PATH = '/mnt/greiner-portal-sync/docs/F.03 BWA Vorjahres-Vergleich (7).xlsx'

NS = {
    'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
}


def load_shared_strings(zip_file):
    """Lädt Shared Strings aus Excel"""
    shared_strings = []
    if 'xl/sharedStrings.xml' in zip_file.namelist():
        with zip_file.open('xl/sharedStrings.xml') as f:
            content = f.read().decode('utf-8')
            root = ET.fromstring(content)
            for si in root.findall('.//main:si', NS):
                t = si.find('main:t', NS)
                if t is not None and t.text:
                    shared_strings.append(t.text)
    return shared_strings


def parse_cell_value(cell, shared_strings):
    """Parst einen Zell-Wert"""
    cell_type = cell.get('t', '')
    v = cell.find('main:v', NS)
    
    if v is not None and v.text:
        if cell_type == 's':  # Shared String
            idx = int(v.text)
            if idx < len(shared_strings):
                return shared_strings[idx]
        else:  # Direkter Wert (Zahl)
            try:
                return float(v.text)
            except:
                return v.text
    
    return None


def extract_bwa_data(excel_path):
    """Extrahiert BWA-Daten aus Excel"""
    print("=" * 80)
    print("GLOBALCUBE EXCEL PARSER - TAG 184")
    print("=" * 80)
    
    with zipfile.ZipFile(excel_path, 'r') as z:
        # Lade Shared Strings
        shared_strings = load_shared_strings(z)
        print(f"\n✅ Shared Strings geladen: {len(shared_strings)}")
        
        # Parse Sheet1
        if 'xl/worksheets/Sheet1.xml' not in z.namelist():
            print("❌ Sheet1.xml nicht gefunden")
            return None
        
        with z.open('xl/worksheets/Sheet1.xml') as f:
            content = f.read().decode('utf-8')
            root = ET.fromstring(content)
            
            sheet_data = root.find('.//main:sheetData', NS)
            if sheet_data is None:
                print("❌ sheetData nicht gefunden")
                return None
            
            rows = sheet_data.findall('.//main:row', NS)
            print(f"✅ Zeilen gefunden: {len(rows)}")
            
            # BWA-Positionen
            bwa_positions = {
                'umsatzerlöse': ['Umsatzerlöse', 'Umsatz'],
                'einsatzwerte': ['Einsatzwerte', 'Einsatz'],
                'bruttoertrag': ['Bruttoertrag'],
                'variable_kosten': ['Variable Kosten'],
                'direkte_kosten': ['Direkte Kosten'],
                'indirekte_kosten': ['Indirekte Kosten'],
                'betriebsergebnis': ['Betriebsergebnis'],
                'bruttoertrag_2': ['Bruttoertrag II', 'DB2'],
                'bruttoertrag_3': ['Bruttoertrag III', 'DB3'],
            }
            
            # Standorte
            standorte = {
                'landau': ['Landau', 'LAN'],
                'deggendorf': ['Deggendorf', 'DEG'],
                'hyundai': ['Hyundai', 'HYU'],
                'gesamt': ['Gesamt', 'Summe', 'Total']
            }
            
            bwa_data = defaultdict(dict)
            
            # Parse alle Zeilen
            for row in rows:
                row_num = row.get('r', '')
                cells = row.findall('.//main:c', NS)
                
                # Baue Zeile auf
                row_values = []
                for cell in cells:
                    val = parse_cell_value(cell, shared_strings)
                    if val is not None:
                        row_values.append(val)
                
                if not row_values:
                    continue
                
                # Erste Spalte ist meist Text (Position)
                first_col = str(row_values[0]) if row_values else ''
                row_text = ' '.join(str(v) for v in row_values).lower()
                
                # Prüfe ob BWA-Position
                for position_key, keywords in bwa_positions.items():
                    if any(kw.lower() in first_col.lower() for kw in keywords):
                        # Prüfe Standort
                        standort = None
                        for standort_key, standort_keywords in standorte.items():
                            if any(kw.lower() in row_text for kw in standort_keywords):
                                standort = standort_key
                                break
                        
                        # Extrahiere Zahlen (überspringe erste Spalte)
                        numbers = []
                        for val in row_values[1:]:
                            if isinstance(val, (int, float)):
                                numbers.append(float(val))
                            elif isinstance(val, str):
                                # Versuche Zahl zu extrahieren
                                num_match = re.search(r'([\d.,\s-]+)', val.replace(' ', ''))
                                if num_match:
                                    try:
                                        num_str = num_match.group(1).replace(',', '.')
                                        numbers.append(float(num_str))
                                    except:
                                        pass
                        
                        if numbers:
                            key = f"{position_key}_{standort}" if standort else position_key
                            bwa_data[key] = {
                                'position': first_col,
                                'row': row_num,
                                'values': numbers,
                                'row_text': ' '.join(str(v) for v in row_values[:10])
                            }
                            print(f"\n✅ {key}:")
                            print(f"   Position: {first_col}")
                            print(f"   Zeile: {row_num}")
                            print(f"   Werte: {numbers[:5]}")
                            break
            
            return dict(bwa_data)


def main():
    """Hauptfunktion"""
    if not Path(EXCEL_PATH).exists():
        print(f"❌ Excel-Datei nicht gefunden: {EXCEL_PATH}")
        return
    
    # Extrahiere BWA-Daten
    bwa_data = extract_bwa_data(EXCEL_PATH)
    
    if bwa_data:
        # Speichere Ergebnisse
        output_dir = Path("/opt/greiner-portal/docs/globalcube_analysis")
        output_dir.mkdir(exist_ok=True)
        
        json_path = output_dir / "excel_bwa_values_tag184.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(bwa_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Ergebnisse gespeichert: {json_path}")
        print(f"\n✅ Gefundene BWA-Positionen: {len(bwa_data)}")
    
    print("\n" + "=" * 80)
    print("✅ Analyse abgeschlossen")
    print("=" * 80)


if __name__ == '__main__':
    main()
