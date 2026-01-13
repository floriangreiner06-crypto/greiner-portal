#!/usr/bin/env python3
"""
GlobalCube Excel Parser - Landau (Korrekt)
Korrekte Interpretation der Excel-Struktur für Landau

Erstellt: TAG 184
"""

import zipfile
import xml.etree.ElementTree as ET
import json
from pathlib import Path
import re

EXCEL_PATH = '/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/globalcube_analyse/F.03 BWA Vorjahres-Vergleich LAN.xlsx'

NS = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

# Spalten-Mapping
COL_MONAT = 3      # C - Monat Dez./2025
COL_YTD = 17       # Q - Kumuliert Dez./2025


def parse_landau_excel(excel_path):
    """Parst Landau Excel korrekt"""
    print("=" * 80)
    print("GLOBALCUBE EXCEL - LANDAU (KORREKT)")
    print("=" * 80)
    
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
            
            bwa_data = {}
            
            print("\n=== Extrahiere BWA-Werte ===\n")
            
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
                
                monat_val = row_data.get(COL_MONAT)
                ytd_val = row_data.get(COL_YTD)
                
                # Spezielle Mapping für Landau (aus Analyse bekannt)
                # Zeile 10: "1 - NW" = Umsatz
                if first_col == '1 - NW' and isinstance(monat_val, (int, float)) and abs(monat_val) > 100000:
                    bwa_data['umsatzerlöse'] = {
                        'position': first_col,
                        'row': row.get('r', ''),
                        'monat': float(monat_val),
                        'ytd': float(ytd_val) if isinstance(ytd_val, (int, float)) else None
                    }
                    print(f"✅ Umsatzerlöse: Monat={monat_val:,.2f} €, YTD={ytd_val:,.2f} €")
                
                # Zeile 11: "2 - GW" = Einsatz
                elif first_col == '2 - GW' and isinstance(monat_val, (int, float)) and abs(monat_val) > 100000:
                    bwa_data['einsatzwerte'] = {
                        'position': first_col,
                        'row': row.get('r', ''),
                        'monat': float(monat_val),
                        'ytd': float(ytd_val) if isinstance(ytd_val, (int, float)) else None
                    }
                    print(f"✅ Einsatzwerte: Monat={monat_val:,.2f} €, YTD={ytd_val:,.2f} €")
                
                # Zeile 20: "Provisionen" = DB1 (Bruttoertrag)
                elif first_col == 'Provisionen' and isinstance(monat_val, (int, float)) and abs(monat_val) > 10000:
                    bwa_data['bruttoertrag'] = {
                        'position': first_col,
                        'row': row.get('r', ''),
                        'monat': float(monat_val),
                        'ytd': float(ytd_val) if isinstance(ytd_val, (int, float)) else None
                    }
                    print(f"✅ Bruttoertrag (DB1): Monat={monat_val:,.2f} €, YTD={ytd_val:,.2f} €")
                
                # Zeile 22: "Fertigmachen" = Variable Kosten
                elif first_col == 'Fertigmachen' and isinstance(monat_val, (int, float)) and abs(monat_val) > 1000:
                    # Summiere alle Variable Kosten (Fertigmachen + andere)
                    if 'variable_kosten' not in bwa_data:
                        bwa_data['variable_kosten'] = {
                            'position': 'Variable Kosten',
                            'row': row.get('r', ''),
                            'monat': 0.0,
                            'ytd': 0.0
                        }
                    bwa_data['variable_kosten']['monat'] += float(monat_val)
                    if isinstance(ytd_val, (int, float)):
                        bwa_data['variable_kosten']['ytd'] += float(ytd_val)
                
                # Zeile 32: "Deckungsbeitrag" = Direkte Kosten
                elif first_col == 'Deckungsbeitrag' and isinstance(monat_val, (int, float)) and abs(monat_val) > 10000:
                    bwa_data['direkte_kosten'] = {
                        'position': first_col,
                        'row': row.get('r', ''),
                        'monat': float(monat_val),
                        'ytd': float(ytd_val) if isinstance(ytd_val, (int, float)) else None
                    }
                    print(f"✅ Direkte Kosten: Monat={monat_val:,.2f} €, YTD={ytd_val:,.2f} €")
                
                # Zeile 30: "Gemeinkosten" = könnte Indirekte Kosten sein
                elif first_col == 'Gemeinkosten' and isinstance(monat_val, (int, float)) and abs(monat_val) > 10000:
                    bwa_data['indirekte_kosten'] = {
                        'position': first_col,
                        'row': row.get('r', ''),
                        'monat': float(monat_val),
                        'ytd': float(ytd_val) if isinstance(ytd_val, (int, float)) else None
                    }
                    print(f"✅ Indirekte Kosten: Monat={monat_val:,.2f} €, YTD={ytd_val:,.2f} €")
            
            # Berechne Variable Kosten Summe
            if 'variable_kosten' in bwa_data:
                print(f"✅ Variable Kosten (Summe): Monat={bwa_data['variable_kosten']['monat']:,.2f} €, YTD={bwa_data['variable_kosten']['ytd']:,.2f} €")
            
            # Berechne Betriebsergebnis
            if all(k in bwa_data for k in ['bruttoertrag', 'variable_kosten', 'direkte_kosten', 'indirekte_kosten']):
                db1 = bwa_data['bruttoertrag']['monat']
                var = bwa_data['variable_kosten']['monat']
                direkt = bwa_data['direkte_kosten']['monat']
                indirekt = bwa_data['indirekte_kosten']['monat']
                be = db1 - var - direkt - indirekt
                
                bwa_data['betriebsergebnis'] = {
                    'position': 'Betriebsergebnis (berechnet)',
                    'row': 'berechnet',
                    'monat': be,
                    'ytd': None  # TODO: YTD berechnen
                }
                print(f"✅ Betriebsergebnis (berechnet): Monat={be:,.2f} €")
            
            return bwa_data


def compare_with_drive(bwa_data):
    """Vergleicht mit DRIVE"""
    print("\n=== Vergleich mit DRIVE (Landau, Dez 2025) ===\n")
    
    try:
        import requests
        url = "http://localhost:5000/api/controlling/bwa/v2?monat=12&jahr=2025&firma=1&standort=2"
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
    except Exception as e:
        print(f"⚠️  Fehler: {e}")


def main():
    """Hauptfunktion"""
    bwa_data = parse_landau_excel(EXCEL_PATH)
    
    if bwa_data:
        # Speichere Ergebnisse
        output_dir = Path("/opt/greiner-portal/docs/globalcube_analysis")
        output_dir.mkdir(exist_ok=True)
        
        json_path = output_dir / "excel_landau_korrekt_tag184.json"
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
