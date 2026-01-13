#!/usr/bin/env python3
"""
GlobalCube Excel Parser - Gesamtbetrieb per 12/25 (Final)
Extrahiert BWA-Werte für Gesamtbetrieb aus Excel

Erstellt: TAG 184
"""

import zipfile
import xml.etree.ElementTree as ET
import json
from pathlib import Path
import re

EXCEL_PATH = '/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/globalcube_analyse/F.03 BWA Vorjahres-Vergleich (8).xlsx'

NS = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def parse_excel_gesamtbetrieb(excel_path):
    """Parst Excel und extrahiert Gesamtbetrieb-Werte"""
    print("=" * 80)
    print("GLOBALCUBE EXCEL - GESAMTBETRIEB PER 12/25")
    print("=" * 80)
    
    if not Path(excel_path).exists():
        print(f"❌ Datei nicht gefunden: {excel_path}")
        return None
    
    with zipfile.ZipFile(excel_path, 'r') as z:
        # Lade Shared Strings
        shared_strings = []
        with z.open('xl/sharedStrings.xml') as f:
            content = f.read().decode('utf-8')
            root = ET.fromstring(content)
            for si in root.findall('.//main:si', NS):
                t = si.find('main:t', NS)
                if t is not None and t.text:
                    shared_strings.append(t.text)
        
        # Parse Sheet1
        with z.open('xl/worksheets/Sheet1.xml') as f:
            content = f.read().decode('utf-8')
            root = ET.fromstring(content)
            sheet_data = root.find('.//main:sheetData', NS)
            rows = sheet_data.findall('.//main:row', NS)
            
            # Spalten-Mapping (aus Analyse bekannt):
            # Spalte C (3): Monat Dez./2025
            # Spalte G (7): Monat Dez./2024 (Vorjahr)
            # Spalte Q (17): Kumuliert Dez./2025 (YTD)
            # Spalte U (21): Kumuliert Dez./2024 (Vorjahr YTD)
            
            COL_MONAT = 3      # C
            COL_VJ_MONAT = 7   # G
            COL_YTD = 17       # Q
            COL_VJ_YTD = 21    # U
            
            bwa_data = {}
            
            # BWA-Positionen die wir suchen
            bwa_keywords = {
                'umsatzerlöse': ['Umsatzerlöse', 'Umsatz'],
                'einsatzwerte': ['Einsatzwerte', 'Einsatz'],
                'bruttoertrag': ['Bruttoertrag', 'DB1', 'Deckungsbeitrag'],
                'variable_kosten': ['Variable Kosten', 'Provisionen', 'Fertigmachen', 'Kulanz'],
                'direkte_kosten': ['Direkte Kosten', 'Personalkosten', 'Gemeinkosten'],
                'indirekte_kosten': ['Indirekte Kosten'],
                'betriebsergebnis': ['Betriebsergebnis', 'BE'],
                'deckungsbeitrag_2': ['Bruttoertrag II', 'DB2'],
                'deckungsbeitrag_3': ['Bruttoertrag III', 'DB3'],
            }
            
            print("\n=== Extrahiere BWA-Werte ===\n")
            
            for row in rows:
                row_num = row.get('r', '')
                cells = row.findall('.//main:c', NS)
                
                # Baue Zeile auf
                row_data = {}
                for cell in cells:
                    cell_ref = cell.get('r', '')
                    col_match = re.match(r'([A-Z]+)', cell_ref)
                    if col_match:
                        col_letters = col_match.group(1)
                        col_idx = 0
                        for char in col_letters:
                            col_idx = col_idx * 26 + (ord(char) - ord('A') + 1)
                        
                        cell_type = cell.get('t', '')
                        v = cell.find('main:v', NS)
                        
                        if v is not None and v.text:
                            if cell_type == 's':
                                idx = int(v.text)
                                if idx < len(shared_strings):
                                    row_data[col_idx] = shared_strings[idx]
                            else:
                                try:
                                    row_data[col_idx] = float(v.text)
                                except:
                                    row_data[col_idx] = v.text
                
                first_col = str(row_data.get(1, '')).strip()
                first_col_lower = first_col.lower()
                
                # Prüfe ob BWA-Position
                for position_key, keywords in bwa_keywords.items():
                    if any(kw.lower() in first_col_lower for kw in keywords):
                        # Extrahiere Werte
                        monat = row_data.get(COL_MONAT)
                        ytd = row_data.get(COL_YTD)
                        
                        # Konvertiere zu Float
                        monat_float = None
                        ytd_float = None
                        
                        if monat is not None:
                            try:
                                monat_float = float(monat)
                            except:
                                pass
                        
                        if ytd is not None:
                            try:
                                ytd_float = float(ytd)
                            except:
                                pass
                        
                        # Nur speichern wenn Werte vorhanden und größer als 100 (Euro-Werte)
                        if (monat_float is not None and abs(monat_float) > 100) or (ytd_float is not None and abs(ytd_float) > 100):
                            if position_key not in bwa_data:
                                bwa_data[position_key] = {
                                    'position': first_col,
                                    'row': row_num,
                                    'monat': monat_float,
                                    'ytd': ytd_float
                                }
                                
                                print(f"✅ {position_key}:")
                                print(f"   Position: {first_col}")
                                print(f"   Zeile: {row_num}")
                                if monat_float is not None:
                                    print(f"   Monat (12/25): {monat_float:,.2f} €")
                                if ytd_float is not None:
                                    print(f"   YTD: {ytd_float:,.2f} €")
                                print()
                            break
            
            # Berechne Gesamtwerte aus Bereichen falls nötig
            # Umsatzerlöse = Summe von 1-NW, 2-GW, etc.
            if 'umsatzerlöse' not in bwa_data:
                print("⚠️  Umsatzerlöse nicht gefunden, berechne aus Bereichen...")
                umsatz_monat = 0
                umsatz_ytd = 0
                
                for row in rows:
                    cells = row.findall('.//main:c', NS)
                    row_data = {}
                    for cell in cells:
                        cell_ref = cell.get('r', '')
                        col_match = re.match(r'([A-Z]+)', cell_ref)
                        if col_match:
                            col_letters = col_match.group(1)
                            col_idx = 0
                            for char in col_letters:
                                col_idx = col_idx * 26 + (ord(char) - ord('A') + 1)
                            
                            cell_type = cell.get('t', '')
                            v = cell.find('main:v', NS)
                            
                            if v is not None and v.text:
                                if cell_type == 's':
                                    idx = int(v.text)
                                    if idx < len(shared_strings):
                                        row_data[col_idx] = shared_strings[idx]
                                else:
                                    try:
                                        row_data[col_idx] = float(v.text)
                                    except:
                                        pass
                    
                    first_col = str(row_data.get(1, '')).strip()
                    # Prüfe ob Bereich (1-NW, 2-GW, etc.)
                    if re.match(r'^\d+\s*-\s*[A-Z]+', first_col):
                        monat_val = row_data.get(3)
                        ytd_val = row_data.get(17)
                        
                        if isinstance(monat_val, (int, float)) and abs(monat_val) > 100000:
                            umsatz_monat += monat_val
                        if isinstance(ytd_val, (int, float)) and abs(ytd_val) > 100000:
                            umsatz_ytd += ytd_val
                
                if umsatz_monat > 0 or umsatz_ytd > 0:
                    bwa_data['umsatzerlöse'] = {
                        'position': 'Umsatzerlöse (berechnet)',
                        'row': 'berechnet',
                        'monat': umsatz_monat,
                        'ytd': umsatz_ytd
                    }
                    print(f"✅ Umsatzerlöse (berechnet): Monat={umsatz_monat:,.2f} €, YTD={umsatz_ytd:,.2f} €\n")
            
            return bwa_data


def compare_with_drive(bwa_data):
    """Vergleicht mit DRIVE"""
    print("\n=== Vergleich mit DRIVE (Gesamtbetrieb, Dez 2025) ===\n")
    
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
                
                print(f"{'Position':<25} | {'Excel (Monat)':>18} | {'DRIVE (Monat)':>18} | {'Differenz':>18} | {'%':>10}")
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
                
                print(f"\n{'Position':<25} | {'Excel (YTD)':>18} | {'DRIVE (YTD)':>18} | {'Differenz':>18} | {'%':>10}")
                print("-" * 100)
                
                for excel_key, drive_key in mapping.items():
                    if excel_key in bwa_data:
                        excel_val = bwa_data[excel_key].get('ytd')
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
    bwa_data = parse_excel_gesamtbetrieb(EXCEL_PATH)
    
    if bwa_data:
        # Speichere Ergebnisse
        output_dir = Path("/opt/greiner-portal/docs/globalcube_analysis")
        output_dir.mkdir(exist_ok=True)
        
        json_path = output_dir / "excel_gesamtbetrieb_12_25_final_tag184.json"
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
