#!/usr/bin/env python3
"""
GlobalCube Excel Analyse - Gesamtbetrieb per 12/25
Analysiert F.03 BWA Vorjahres-Vergleich (8).xlsx für Gesamtbetrieb Dezember 2025

Erstellt: TAG 184
"""

import zipfile
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from collections import defaultdict
import re

EXCEL_PATH = '/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/globalcube_analyse/F.03 BWA Vorjahres-Vergleich (8).xlsx'

NS = {
    'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
}


def load_shared_strings(zip_file):
    """Lädt Shared Strings"""
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
    """Parst Zell-Wert"""
    cell_type = cell.get('t', '')
    v = cell.find('main:v', NS)
    
    if v is not None and v.text:
        if cell_type == 's':  # Shared String
            idx = int(v.text)
            if idx < len(shared_strings):
                return shared_strings[idx]
        else:  # Direkter Wert
            try:
                return float(v.text)
            except:
                return v.text
    
    return None


def extract_bwa_gesamtbetrieb(excel_path):
    """Extrahiert BWA-Werte für Gesamtbetrieb per 12/25"""
    print("=" * 80)
    print("GLOBALCUBE EXCEL ANALYSE - GESAMTBETRIEB PER 12/25")
    print("=" * 80)
    
    if not Path(excel_path).exists():
        print(f"❌ Datei nicht gefunden: {excel_path}")
        return None
    
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
                'bruttoertrag': ['Bruttoertrag', 'DB1'],
                'variable_kosten': ['Variable Kosten'],
                'direkte_kosten': ['Direkte Kosten'],
                'indirekte_kosten': ['Indirekte Kosten'],
                'betriebsergebnis': ['Betriebsergebnis', 'BE'],
                'deckungsbeitrag_2': ['Bruttoertrag II', 'DB2'],
                'deckungsbeitrag_3': ['Bruttoertrag III', 'DB3'],
            }
            
            bwa_data = {}
            header_row = None
            header_cols = {}
            
            # 1. Finde Header-Zeile (enthält "Monat", "Kumuliert", "12/25", etc.)
            print("\n=== Suche Header-Zeile ===")
            for row in rows[:20]:
                row_num = row.get('r', '')
                cells = row.findall('.//main:c', NS)
                
                row_values = []
                for cell in cells:
                    val = parse_cell_value(cell, shared_strings)
                    if val is not None:
                        row_values.append(val)
                
                row_text = ' '.join(str(v) for v in row_values).lower()
                
                # Prüfe ob Header (enthält "monat", "kumuliert", "12/25", "dez")
                if any(kw in row_text for kw in ['monat', 'kumuliert', '12/25', 'dez/25', 'dez/2025', 'gesamt']):
                    header_row = row_num
                    print(f"✅ Header in Zeile {row_num}")
                    
                    # Mappe Spalten
                    for col_idx, val in enumerate(row_values, 1):
                        val_str = str(val).lower()
                        if 'monat' in val_str or 'dez/25' in val_str or '12/25' in val_str:
                            header_cols['monat'] = col_idx
                        elif 'kumuliert' in val_str or 'ytd' in val_str:
                            header_cols['kumuliert'] = col_idx
                        elif 'vorjahr' in val_str or 'vj' in val_str:
                            header_cols['vorjahr'] = col_idx
                    
                    print(f"   Spalten-Mapping: {header_cols}")
                    break
            
            # 2. Extrahiere BWA-Werte
            print("\n=== Extrahiere BWA-Werte ===")
            
            for row in rows:
                row_num = row.get('r', '')
                cells = row.findall('.//main:c', NS)
                
                # Baue Zeile auf
                row_values = []
                cell_map = {}  # Spalten-Index -> Wert
                
                for cell in cells:
                    cell_ref = cell.get('r', '')
                    # Extrahiere Spalten-Index (z.B. "A1" -> 1, "B1" -> 2)
                    col_match = re.match(r'([A-Z]+)', cell_ref)
                    if col_match:
                        col_letters = col_match.group(1)
                        col_idx = 0
                        for char in col_letters:
                            col_idx = col_idx * 26 + (ord(char) - ord('A') + 1)
                        cell_map[col_idx] = parse_cell_value(cell, shared_strings)
                
                # Erste Spalte (meist Text)
                first_col = cell_map.get(1)
                if not first_col:
                    continue
                
                first_col_str = str(first_col).lower()
                
                # Prüfe ob BWA-Position
                for position_key, keywords in bwa_positions.items():
                    if any(kw.lower() in first_col_str for kw in keywords):
                        # Prüfe ob "Gesamt" oder "Gesamtbetrieb"
                        row_text = ' '.join(str(v) for v in cell_map.values() if v).lower()
                        
                        if 'gesamt' in row_text or 'gesamtbetrieb' in row_text or not any(kw in row_text for kw in ['landau', 'deggendorf', 'hyundai']):
                            # Extrahiere Werte aus relevanten Spalten
                            monat_value = cell_map.get(header_cols.get('monat'))
                            kumuliert_value = cell_map.get(header_cols.get('kumuliert'))
                            
                            # Konvertiere zu Float falls möglich
                            monat_float = None
                            kumuliert_float = None
                            
                            if monat_value is not None:
                                try:
                                    monat_float = float(monat_value)
                                except:
                                    pass
                            
                            if kumuliert_value is not None:
                                try:
                                    kumuliert_float = float(kumuliert_value)
                                except:
                                    pass
                            
                            if monat_float is not None or kumuliert_float is not None:
                                bwa_data[position_key] = {
                                    'position': str(first_col),
                                    'row': row_num,
                                    'monat': monat_float,
                                    'kumuliert': kumuliert_float,
                                    'raw_values': {k: v for k, v in cell_map.items() if v is not None}
                                }
                                
                                print(f"\n✅ {position_key}:")
                                print(f"   Position: {first_col}")
                                print(f"   Zeile: {row_num}")
                                if monat_float is not None:
                                    print(f"   Monat (12/25): {monat_float:,.2f}")
                                if kumuliert_float is not None:
                                    print(f"   Kumuliert: {kumuliert_float:,.2f}")
                                break
            
            return bwa_data


def compare_with_drive(bwa_data):
    """Vergleicht mit DRIVE BWA für Gesamtbetrieb"""
    print("\n=== Vergleich mit DRIVE (Gesamtbetrieb, Dez 2025) ===")
    
    try:
        import requests
        url = "http://localhost:5000/api/controlling/bwa/v2?monat=12&jahr=2025&firma=0&standort=0"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            drive_data = response.json()
            
            if drive_data.get('status') == 'ok':
                aktuell = drive_data.get('aktuell', {})
                ytd = drive_data.get('ytd', {})
                
                mapping = {
                    'umsatzerlöse': 'umsatz',
                    'einsatzwerte': 'einsatz',
                    'bruttoertrag': 'db1',
                    'variable_kosten': 'variable_kosten',
                    'direkte_kosten': 'direkte_kosten',
                    'indirekte_kosten': 'indirekte_kosten',
                    'betriebsergebnis': 'betriebsergebnis',
                }
                
                print(f"\n{'Position':<25} | {'Excel (Monat)':>18} | {'DRIVE (Monat)':>18} | {'Differenz':>18} | {'%':>10}")
                print("-" * 100)
                
                for excel_key, drive_key in mapping.items():
                    if excel_key in bwa_data:
                        excel_val = bwa_data[excel_key].get('monat')
                        drive_val = aktuell.get(drive_key, 0)
                        
                        if excel_val is not None and drive_val is not None:
                            diff = drive_val - excel_val
                            diff_pct = (diff / excel_val * 100) if excel_val != 0 else 0
                            
                            status = "✅" if abs(diff_pct) < 1 else "⚠️" if abs(diff_pct) < 5 else "❌"
                            
                            print(f"{excel_key:<25} | {excel_val:>18,.2f} | {drive_val:>18,.2f} | {diff:>18,.2f} | {diff_pct:>9.2f}% {status}")
                
                # YTD-Vergleich
                print(f"\n{'Position':<25} | {'Excel (YTD)':>18} | {'DRIVE (YTD)':>18} | {'Differenz':>18} | {'%':>10}")
                print("-" * 100)
                
                for excel_key, drive_key in mapping.items():
                    if excel_key in bwa_data:
                        excel_val = bwa_data[excel_key].get('kumuliert')
                        drive_val = ytd.get(drive_key, 0)
                        
                        if excel_val is not None and drive_val is not None:
                            diff = drive_val - excel_val
                            diff_pct = (diff / excel_val * 100) if excel_val != 0 else 0
                            
                            status = "✅" if abs(diff_pct) < 1 else "⚠️" if abs(diff_pct) < 5 else "❌"
                            
                            print(f"{excel_key:<25} | {excel_val:>18,.2f} | {drive_val:>18,.2f} | {diff:>18,.2f} | {diff_pct:>9.2f}% {status}")
        else:
            print(f"⚠️  API-Fehler: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Fehler beim API-Aufruf: {e}")


def main():
    """Hauptfunktion"""
    # Extrahiere BWA-Daten
    bwa_data = extract_bwa_gesamtbetrieb(EXCEL_PATH)
    
    if bwa_data:
        # Speichere Ergebnisse
        output_dir = Path("/opt/greiner-portal/docs/globalcube_analysis")
        output_dir.mkdir(exist_ok=True)
        
        json_path = output_dir / "excel_gesamtbetrieb_12_25_tag184.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(bwa_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Ergebnisse gespeichert: {json_path}")
        
        # Vergleiche mit DRIVE
        compare_with_drive(bwa_data)
    
    print("\n" + "=" * 80)
    print("✅ Analyse abgeschlossen")
    print("=" * 80)


if __name__ == '__main__':
    main()
