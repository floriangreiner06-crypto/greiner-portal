#!/usr/bin/env python3
"""
GlobalCube Excel Analyse - Alle Standorte
Analysiert Excel-Dateien für DEG, DEG HYU, LAN und Gesamtbetrieb

Erstellt: TAG 184
"""

import zipfile
import xml.etree.ElementTree as ET
import json
from pathlib import Path
import re
from collections import defaultdict

EXCEL_DIR = '/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/globalcube_analyse/'

NS = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

# Spalten-Mapping (aus Analyse bekannt)
COL_MONAT = 3      # C - Monat Dez./2025
COL_VJ_MONAT = 7   # G - Monat Dez./2024
COL_YTD = 17       # Q - Kumuliert Dez./2025
COL_VJ_YTD = 21    # U - Kumuliert Dez./2024


def find_excel_files():
    """Findet alle Excel-Dateien im Verzeichnis"""
    excel_dir = Path(EXCEL_DIR)
    if not excel_dir.exists():
        print(f"❌ Verzeichnis nicht gefunden: {EXCEL_DIR}")
        return []
    
    excel_files = list(excel_dir.glob('*.xlsx'))
    print(f"✅ Gefundene Excel-Dateien: {len(excel_files)}")
    for f in excel_files:
        print(f"  - {f.name}")
    
    return excel_files


def parse_excel_file(excel_path):
    """Parst eine Excel-Datei und extrahiert BWA-Werte"""
    print(f"\n{'='*80}")
    print(f"Analysiere: {excel_path.name}")
    print(f"{'='*80}\n")
    
    with zipfile.ZipFile(excel_path, 'r') as z:
        # Lade Shared Strings
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            with z.open('xl/sharedStrings.xml') as f:
                content = f.read().decode('utf-8')
                root = ET.fromstring(content)
                for si in root.findall('.//main:si', NS):
                    t = si.find('main:t', NS)
                    if t is not None and t.text:
                        shared_strings.append(t.text)
        
        # Parse Sheet1
        if 'xl/worksheets/Sheet1.xml' not in z.namelist():
            print("❌ Sheet1.xml nicht gefunden")
            return None
        
        with z.open('xl/worksheets/Sheet1.xml') as f:
            content = f.read().decode('utf-8')
            root = ET.fromstring(content)
            sheet_data = root.find('.//main:sheetData', NS)
            rows = sheet_data.findall('.//main:row', NS)
            
            bwa_data = {}
            
            # BWA-Positionen
            bwa_keywords = {
                'umsatzerlöse': ['Umsatzerlöse', 'Umsatz'],
                'einsatzwerte': ['Einsatzwerte', 'Einsatz'],
                'bruttoertrag': ['Bruttoertrag', 'DB1', 'Deckungsbeitrag'],
                'variable_kosten': ['Variable Kosten', 'Provisionen', 'Fertigmachen', 'Kulanz'],
                'direkte_kosten': ['Direkte Kosten', 'Personalkosten', 'Gemeinkosten'],
                'indirekte_kosten': ['Indirekte Kosten'],
                'betriebsergebnis': ['Betriebsergebnis', 'BE'],
            }
            
            # Summen für Bereiche
            umsatz_bereiche_monat = 0
            umsatz_bereiche_ytd = 0
            
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
                first_col_lower = first_col.lower()
                
                # Summiere Umsatz-Bereiche (1-NW, 2-GW, etc.)
                if re.match(r'^\d+\s*-\s*[A-Z]+', first_col):
                    monat_val = row_data.get(COL_MONAT)
                    ytd_val = row_data.get(COL_YTD)
                    
                    if isinstance(monat_val, (int, float)) and abs(monat_val) > 100000:
                        umsatz_bereiche_monat += monat_val
                    if isinstance(ytd_val, (int, float)) and abs(ytd_val) > 100000:
                        umsatz_bereiche_ytd += ytd_val
                
                # Prüfe ob BWA-Position
                for position_key, keywords in bwa_keywords.items():
                    if any(kw.lower() in first_col_lower for kw in keywords):
                        monat_val = row_data.get(COL_MONAT)
                        ytd_val = row_data.get(COL_YTD)
                        
                        # Konvertiere zu Float
                        monat_float = None
                        ytd_float = None
                        
                        if monat_val is not None:
                            try:
                                monat_float = float(monat_val)
                            except:
                                pass
                        
                        if ytd_val is not None:
                            try:
                                ytd_float = float(ytd_val)
                            except:
                                pass
                        
                        # Nur speichern wenn Werte vorhanden und größer als 100 (Euro-Werte)
                        if (monat_float is not None and abs(monat_float) > 100) or (ytd_float is not None and abs(ytd_float) > 100):
                            if position_key not in bwa_data:
                                bwa_data[position_key] = {
                                    'position': first_col,
                                    'row': row.get('r', ''),
                                    'monat': monat_float,
                                    'ytd': ytd_float
                                }
                                
                                print(f"✅ {position_key}:")
                                print(f"   Position: {first_col}")
                                if monat_float is not None:
                                    print(f"   Monat: {monat_float:,.2f} €")
                                if ytd_float is not None:
                                    print(f"   YTD: {ytd_float:,.2f} €")
                                print()
                            break
            
            # Füge berechnete Umsatzerlöse hinzu falls nicht gefunden
            if 'umsatzerlöse' not in bwa_data and umsatz_bereiche_monat > 0:
                bwa_data['umsatzerlöse'] = {
                    'position': 'Umsatzerlöse (berechnet aus Bereichen)',
                    'row': 'berechnet',
                    'monat': umsatz_bereiche_monat,
                    'ytd': umsatz_bereiche_ytd
                }
                print(f"✅ Umsatzerlöse (berechnet): Monat={umsatz_bereiche_monat:,.2f} €, YTD={umsatz_bereiche_ytd:,.2f} €\n")
            
            return bwa_data


def identify_standort(filename):
    """Identifiziert Standort aus Dateinamen"""
    filename_lower = filename.lower()
    
    if 'gesamt' in filename_lower or 'alle' in filename_lower:
        return 'gesamt', '0', '0'
    elif 'landau' in filename_lower or 'lan' in filename_lower:
        return 'landau', '1', '2'
    elif 'hyundai' in filename_lower or 'hyu' in filename_lower:
        return 'hyundai', '2', '0'
    elif 'deggendorf' in filename_lower or 'deg' in filename_lower:
        # Prüfe ob Opel oder beide
        if 'opel' in filename_lower or 'stellantis' in filename_lower:
            return 'deggendorf_opel', '1', '1'
        else:
            # Deggendorf gesamt (beide)
            return 'deggendorf', '0', 'deg-both'
    
    return 'unbekannt', '0', '0'


def compare_with_drive(bwa_data, standort_name, firma, standort):
    """Vergleicht mit DRIVE"""
    print(f"\n=== Vergleich mit DRIVE ({standort_name}) ===\n")
    
    try:
        import requests
        url = f"http://localhost:5000/api/controlling/bwa/v2?monat=12&jahr=2025&firma={firma}&standort={standort}"
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
                
                return {
                    'standort': standort_name,
                    'excel': bwa_data,
                    'drive': {
                        'aktuell': aktuell,
                        'ytd': ytd
                    }
                }
        else:
            print(f"⚠️  API-Fehler: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Fehler beim API-Aufruf: {e}")
    
    return None


def main():
    """Hauptfunktion"""
    print("=" * 80)
    print("GLOBALCUBE EXCEL ANALYSE - ALLE STANDORTE")
    print("=" * 80)
    
    # Finde Excel-Dateien
    excel_files = find_excel_files()
    
    if not excel_files:
        return
    
    all_results = {}
    
    # Analysiere jede Datei
    for excel_file in excel_files:
        # Identifiziere Standort
        standort_name, firma, standort = identify_standort(excel_file.name)
        
        # Parse Excel
        bwa_data = parse_excel_file(excel_file)
        
        if bwa_data:
            # Vergleiche mit DRIVE
            comparison = compare_with_drive(bwa_data, standort_name, firma, standort)
            
            if comparison:
                all_results[standort_name] = comparison
            
            # Speichere einzelne Ergebnisse
            output_dir = Path("/opt/greiner-portal/docs/globalcube_analysis")
            output_dir.mkdir(exist_ok=True)
            
            json_path = output_dir / f"excel_{standort_name}_tag184.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(bwa_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Ergebnisse gespeichert: {json_path}\n")
    
    # Speichere alle Ergebnisse
    if all_results:
        output_dir = Path("/opt/greiner-portal/docs/globalcube_analysis")
        all_json_path = output_dir / "excel_alle_standorte_vergleich_tag184.json"
        with open(all_json_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Alle Ergebnisse gespeichert: {all_json_path}")
    
    print("\n" + "=" * 80)
    print("✅ Analyse abgeschlossen")
    print("=" * 80)


if __name__ == '__main__':
    main()
