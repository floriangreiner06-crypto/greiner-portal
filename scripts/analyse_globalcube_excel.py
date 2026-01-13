#!/usr/bin/env python3
"""
GlobalCube Excel-Export Analyse
Analysiert Excel-Exports von GlobalCube und extrahiert BWA-Werte

Erstellt: TAG 184
Ziel: BWA-Werte aus Excel extrahieren und mit DRIVE vergleichen
"""

import json
from pathlib import Path
from collections import defaultdict
import re
import zipfile
import xml.etree.ElementTree as ET

# Versuche pandas mit openpyxl, sonst verwende zipfile/xml
try:
    import pandas as pd
    # Test ob openpyxl verfügbar ist
    pd.ExcelFile.__init__.__globals__.get('openpyxl', None)
    USE_PANDAS = True
except (ImportError, AttributeError):
    USE_PANDAS = False
    print("⚠️  pandas/openpyxl nicht verfügbar, verwende zipfile/xml")

# Mögliche Excel-Dateien
EXCEL_PATHS = [
    "/opt/greiner-portal/docs/F.03 BWA Vorjahres-Vergleich (7).xlsx",
    "/mnt/greiner-portal-sync/docs/F.03 BWA Vorjahres-Vergleich (7).xlsx",
    "/opt/greiner-portal/docs/F.03 BWA Vorjahres-Vergleich (17).xlsx",
    "/mnt/greiner-portal-sync/docs/F.03 BWA Vorjahres-Vergleich (17).xlsx",
]


def find_excel_file():
    """Findet die Excel-Datei"""
    print("=== Suche Excel-Datei ===\n")
    
    for path in EXCEL_PATHS:
        if Path(path).exists():
            print(f"✅ Gefunden: {path}")
            return path
    
    print("❌ Keine Excel-Datei gefunden")
    return None


def analyze_excel_structure(excel_path):
    """Analysiert die Struktur der Excel-Datei"""
    print("\n=== Analysiere Excel-Struktur ===\n")
    
    try:
        if USE_PANDAS:
            # Verwende pandas
            xls = pd.ExcelFile(excel_path)
            print(f"Sheet-Namen: {xls.sheet_names}")
            
            sheets_data = {}
            for sheet_name in xls.sheet_names:
                print(f"\n--- Sheet: {sheet_name} ---")
                df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None, nrows=50)
                print(f"Dimensionen: {df.shape[0]} Zeilen x {df.shape[1]} Spalten")
                
                # Suche nach BWA-relevanten Begriffen
                bwa_keywords = [
                    'Umsatzerlöse', 'Einsatzwerte', 'Variable Kosten', 'Direkte Kosten',
                    'Indirekte Kosten', 'Betriebsergebnis', 'Deckungsbeitrag', 'Bruttoertrag',
                    'Neuwagen', 'Gebrauchtwagen', 'Service', 'Teile', 'Landau', 'Deggendorf'
                ]
                
                found_keywords = []
                keyword_positions = {}
                
                for row_idx, row in df.iterrows():
                    for col_idx, cell_value in enumerate(row):
                        if pd.notna(cell_value):
                            cell_str = str(cell_value).strip()
                            for keyword in bwa_keywords:
                                if keyword.lower() in cell_str.lower():
                                    if keyword not in found_keywords:
                                        found_keywords.append(keyword)
                                    if keyword not in keyword_positions:
                                        keyword_positions[keyword] = []
                                    keyword_positions[keyword].append({
                                        'row': row_idx + 1,
                                        'col': col_idx + 1,
                                        'value': cell_str
                                    })
                
                print(f"Gefundene BWA-Keywords: {len(found_keywords)}")
                for keyword in found_keywords[:10]:
                    print(f"  - {keyword}: {len(keyword_positions[keyword])} Vorkommen")
                
                sheets_data[sheet_name] = {
                    'dimensions': f"{df.shape[0]}x{df.shape[1]}",
                    'found_keywords': found_keywords,
                    'keyword_positions': keyword_positions
                }
            
            return sheets_data
        else:
            # Verwende zipfile/xml (Excel ist ZIP)
            print("⚠️  pandas nicht verfügbar, verwende zipfile/xml")
            with zipfile.ZipFile(excel_path, 'r') as z:
                # Liste Dateien
                files = z.namelist()
                print(f"Dateien im ZIP: {len(files)}")
                
                # Suche nach sharedStrings.xml
                if 'xl/sharedStrings.xml' in files:
                    with z.open('xl/sharedStrings.xml') as f:
                        content = f.read().decode('utf-8')
                        root = ET.fromstring(content)
                        strings = [si.find('t').text if si.find('t') is not None else '' 
                                 for si in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si')]
                        
                        print(f"Shared Strings: {len(strings)}")
                        
                        # Suche nach BWA-Keywords
                        bwa_keywords = [
                            'Umsatzerlöse', 'Einsatzwerte', 'Variable Kosten', 'Direkte Kosten',
                            'Indirekte Kosten', 'Betriebsergebnis', 'Deckungsbeitrag', 'Bruttoertrag'
                        ]
                        
                        found = [s for s in strings if any(kw.lower() in s.lower() for kw in bwa_keywords)]
                        print(f"BWA-relevante Strings: {len(found)}")
                        for s in found[:10]:
                            print(f"  - {s[:60]}")
                
                return {'method': 'zipfile', 'files': files[:10]}
        
    except Exception as e:
        print(f"❌ Fehler beim Analysieren: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_bwa_values(excel_path, sheet_name=None):
    """Extrahiert BWA-Werte aus Excel"""
    print("\n=== Extrahiere BWA-Werte ===\n")
    
    try:
        if USE_PANDAS:
            # Verwende pandas
            xls = pd.ExcelFile(excel_path)
            if sheet_name is None:
                sheet_name = xls.sheet_names[0]
            
            print(f"Verwende Sheet: {sheet_name}")
            df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
            
            # BWA-Positionen die wir suchen
            bwa_positions = {
                'umsatzerlöse': ['Umsatzerlöse', 'Umsatz'],
                'einsatzwerte': ['Einsatzwerte', 'Einsatz'],
                'variable_kosten': ['Variable Kosten', 'Variable'],
                'direkte_kosten': ['Direkte Kosten', 'Direkte'],
                'indirekte_kosten': ['Indirekte Kosten', 'Indirekte'],
                'betriebsergebnis': ['Betriebsergebnis', 'BE'],
                'deckungsbeitrag_1': ['Deckungsbeitrag 1', 'DB1', 'Bruttoertrag'],
                'deckungsbeitrag_2': ['Deckungsbeitrag 2', 'DB2'],
                'deckungsbeitrag_3': ['Deckungsbeitrag 3', 'DB3'],
            }
            
            # Standorte
            standorte = {
                'landau': ['Landau', 'LAN'],
                'deggendorf': ['Deggendorf', 'DEG'],
                'hyundai': ['Hyundai', 'HYU'],
                'gesamt': ['Gesamt', 'Summe', 'Total']
            }
            
            bwa_values = {}
            
            # Durchsuche alle Zeilen
            for row_idx, row in df.iterrows():
                row_values = [str(val).strip() if pd.notna(val) else '' for val in row]
                row_text = ' '.join(row_values).lower()
                
                # Prüfe ob BWA-Position
                for position_key, keywords in bwa_positions.items():
                    if any(kw.lower() in row_text for kw in keywords):
                        # Prüfe Standort
                        standort = None
                        for standort_key, standort_keywords in standorte.items():
                            if any(kw.lower() in row_text for kw in standort_keywords):
                                standort = standort_key
                                break
                        
                        # Extrahiere Zahlen aus dieser Zeile
                        numbers = []
                        for val in row:
                            if pd.notna(val):
                                try:
                                    if isinstance(val, (int, float)):
                                        numbers.append(float(val))
                                    elif isinstance(val, str):
                                        # Versuche Zahl aus String zu extrahieren
                                        num_match = re.search(r'([\d.,\s-]+)', val.replace(' ', ''))
                                        if num_match:
                                            num_str = num_match.group(1).replace(',', '.')
                                            numbers.append(float(num_str))
                                except:
                                    pass
                        
                        if numbers:
                            key = f"{position_key}_{standort}" if standort else position_key
                            if key not in bwa_values:
                                bwa_values[key] = []
                            bwa_values[key].append({
                                'row': row_idx + 1,
                                'values': numbers,
                                'row_text': ' '.join(row_values)
                            })
            
            print(f"✅ Gefundene BWA-Positionen: {len(bwa_values)}")
            for key, entries in list(bwa_values.items())[:10]:
                print(f"  {key}: {len(entries)} Einträge")
                if entries:
                    print(f"    Zeile {entries[0]['row']}: {entries[0]['values'][:3]}")
            
            return bwa_values
        else:
            print("⚠️  pandas nicht verfügbar, kann Werte nicht extrahieren")
            return {}
        
    except Exception as e:
        print(f"❌ Fehler beim Extrahieren: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_with_drive(bwa_values):
    """Vergleicht Excel-Werte mit DRIVE BWA"""
    print("\n=== Vergleich mit DRIVE BWA ===\n")
    
    # TODO: Lade DRIVE BWA-Werte für Dezember 2025
    # Für jetzt: Zeige nur Excel-Werte
    
    print("Excel BWA-Werte (Dezember 2025):")
    for key, entries in sorted(bwa_values.items()):
        if entries:
            # Nehme erste Zahl (könnte Monat sein)
            first_value = entries[0]['values'][0] if entries[0]['values'] else None
            if first_value:
                print(f"  {key}: {first_value:,.2f} €")
    
    return bwa_values


def main():
    """Hauptfunktion"""
    print("=" * 80)
    print("GLOBALCUBE EXCEL-EXPORT ANALYSE - TAG 184")
    print("=" * 80)
    
    # 1. Finde Excel-Datei
    excel_path = find_excel_file()
    if not excel_path:
        return
    
    # 2. Analysiere Struktur
    structure = analyze_excel_structure(excel_path)
    
    # 3. Extrahiere BWA-Werte
    bwa_values = extract_bwa_values(excel_path)
    
    if bwa_values:
        # 4. Vergleiche mit DRIVE
        compare_with_drive(bwa_values)
        
        # 5. Speichere Ergebnisse
        output_dir = Path("/opt/greiner-portal/docs/globalcube_analysis")
        output_dir.mkdir(exist_ok=True)
        
        results = {
            'excel_path': excel_path,
            'structure': structure,
            'bwa_values': bwa_values
        }
        
        json_path = output_dir / "excel_analysis_tag184.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n✅ Ergebnisse gespeichert: {json_path}")
    
    print("\n" + "=" * 80)
    print("✅ Analyse abgeschlossen")
    print("=" * 80)


if __name__ == '__main__':
    main()
