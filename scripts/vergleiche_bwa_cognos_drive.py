#!/usr/bin/env python3
"""
Vergleicht BWA-Werte aus Cognos (HAR) mit DRIVE
Extrahiert alle verfügbaren Werte und vergleicht sie

Erstellt: TAG 182
"""

import json
import sys
import requests
from typing import Dict, List
import re

# DRIVE API
DRIVE_API_URL = "http://localhost:5000/api/controlling/bwa/v2"

# HAR-Ergebnisse
HAR_RESULTS_FILE = "/tmp/cognos_bwa_har_results.json"


def get_drive_bwa(monat: int = 12, jahr: int = 2025, standort: str = None, firma: str = None) -> Dict:
    """
    Ruft BWA-Werte von DRIVE API ab
    """
    params = {
        'monat': monat,
        'jahr': jahr
    }
    
    if standort:
        params['standort'] = standort
    if firma:
        params['firma'] = firma
    
    try:
        response = requests.get(DRIVE_API_URL, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ DRIVE API Fehler: {response.status_code}")
            return {}
    except Exception as e:
        print(f"❌ Fehler beim Abrufen von DRIVE: {e}")
        return {}


def parse_cognos_value(value_str: str) -> float:
    """
    Parst Cognos-Wert (deutsches Format: Punkt = Tausender, Komma = Dezimal)
    Beispiel: "2.190.826" = 2190826.0, "1.234,56" = 1234.56
    """
    if not value_str:
        return 0.0
    
    # Entferne alles außer Zahlen, Komma, Punkt, Minus
    cleaned = re.sub(r'[^\d.,-]', '', value_str)
    
    # Prüfe ob Minus vorhanden
    is_negative = '-' in cleaned
    cleaned = cleaned.replace('-', '')
    
    # Deutsches Format: Punkt = Tausender, Komma = Dezimal
    # Wenn Komma vorhanden, dann ist es Dezimaltrennzeichen
    if ',' in cleaned:
        # Komma = Dezimaltrennzeichen
        # Entferne alle Punkte (Tausender-Trennzeichen)
        cleaned = cleaned.replace('.', '')
        # Ersetze Komma durch Punkt
        cleaned = cleaned.replace(',', '.')
    else:
        # Kein Komma = nur Tausender-Trennzeichen (Punkte)
        # Entferne alle Punkte
        cleaned = cleaned.replace('.', '')
    
    if is_negative:
        cleaned = '-' + cleaned
    
    try:
        return float(cleaned)
    except:
        return 0.0


def extract_cognos_bwa_values(har_results: Dict) -> Dict:
    """
    Extrahiert strukturierte BWA-Werte aus HAR-Ergebnissen
    """
    cognos_values = {}
    
    for key, data in har_results.items():
        bwa_values = data.get('bwa_values', {})
        
        for bwa_key, value_data in bwa_values.items():
            # Extrahiere Haupt-Position (ohne _tableX)
            main_key = bwa_key.split('_table')[0]
            
            if value_data.get('values'):
                # Nimm ersten Wert (sollte der Hauptwert sein)
                value_str = value_data['values'][0]
                parsed_value = parse_cognos_value(value_str)
                
                if main_key not in cognos_values or abs(parsed_value) > abs(cognos_values[main_key]):
                    cognos_values[main_key] = parsed_value
    
    return cognos_values


def compare_bwa_values(cognos_values: Dict, drive_values: Dict) -> Dict:
    """
    Vergleicht Cognos- und DRIVE-Werte
    """
    comparison = {}
    
    # Mapping zwischen Cognos- und DRIVE-Keys
    key_mapping = {
        'umsatzerlöse': 'umsatz',
        'einsatzwerte': 'einsatz',
        'variable_kosten': 'variable',
        'direkte_kosten': 'direkte',
        'indirekte_kosten': 'indirekte',
        'betriebsergebnis': 'betriebsergebnis',
        'unternehmensergebnis': 'unternehmensergebnis',
        'bruttoertrag': 'bruttoertrag',
        'deckungsbeitrag_1': 'db1',
        'deckungsbeitrag_2': 'db2',
        'deckungsbeitrag_3': 'db3',
    }
    
    for cognos_key, drive_key in key_mapping.items():
        cognos_val = cognos_values.get(cognos_key, 0)
        drive_val = drive_values.get(drive_key, 0)
        
        if cognos_val != 0 or drive_val != 0:
            diff = drive_val - cognos_val
            diff_percent = (diff / cognos_val * 100) if cognos_val != 0 else 0
            
            comparison[cognos_key] = {
                'cognos': cognos_val,
                'drive': drive_val,
                'differenz': diff,
                'differenz_percent': diff_percent
            }
    
    return comparison


def main():
    """
    Hauptfunktion
    """
    print("=" * 80)
    print("BWA-Vergleich: Cognos (HAR) vs. DRIVE")
    print("=" * 80)
    print()
    
    # Lade HAR-Ergebnisse
    try:
        with open(HAR_RESULTS_FILE, 'r', encoding='utf-8') as f:
            har_results = json.load(f)
        print(f"✅ HAR-Ergebnisse geladen: {len(har_results)} Responses\n")
    except Exception as e:
        print(f"❌ Fehler beim Laden der HAR-Ergebnisse: {e}")
        return
    
    # Extrahiere Cognos-Werte
    cognos_values = extract_cognos_bwa_values(har_results)
    
    print("=== COGNOS WERTE (aus HAR) ===\n")
    for key, value in cognos_values.items():
        print(f"{key}: {value:,.2f} €")
    
    # Hole DRIVE-Werte (Dezember 2025, alle Standorte)
    print("\n" + "=" * 80)
    print("Hole DRIVE-Werte...")
    print("=" * 80 + "\n")
    
    drive_values_all = get_drive_bwa(monat=12, jahr=2025)
    
    if drive_values_all:
        # DRIVE API-Struktur: aktuell, vorjahr, ytd, ytd_vorjahr
        aktuell = drive_values_all.get('aktuell', {})
        
        print(f"Aktuell Keys: {list(aktuell.keys())[:10]}\n")
        
        # Extrahiere Werte aus 'aktuell' (Monatswerte)
        drive_values = {
            'umsatz': aktuell.get('umsatz', 0),
            'einsatz': aktuell.get('einsatz', 0),
            'variable': aktuell.get('variable', 0),
            'direkte': aktuell.get('direkte', 0),
            'indirekte': aktuell.get('indirekte', 0),
            'betriebsergebnis': aktuell.get('betriebsergebnis', 0),
            'unternehmensergebnis': aktuell.get('unternehmensergebnis', 0),
            'bruttoertrag': aktuell.get('bruttoertrag', 0),
            'db1': aktuell.get('db1', 0),
            'db2': aktuell.get('db2', 0),
            'db3': aktuell.get('db3', 0),
        }
        
        print("=== DRIVE WERTE ===\n")
        for key, value in drive_values.items():
            print(f"{key}: {value:,.2f} €")
        
        # Vergleiche
        print("\n" + "=" * 80)
        print("VERGLEICH")
        print("=" * 80 + "\n")
        
        comparison = compare_bwa_values(cognos_values, drive_values)
        
        print(f"{'Position':<25} {'Cognos':>15} {'DRIVE':>15} {'Differenz':>15} {'%':>10}")
        print("-" * 80)
        
        for key, comp in comparison.items():
            print(f"{key:<25} {comp['cognos']:>15,.2f} {comp['drive']:>15,.2f} {comp['differenz']:>15,.2f} {comp['differenz_percent']:>9.2f}%")
        
        # Speichere Vergleich
        comparison_file = "/tmp/bwa_vergleich_cognos_drive.json"
        with open(comparison_file, 'w', encoding='utf-8') as f:
            json.dump({
                'cognos_values': cognos_values,
                'drive_values': drive_values,
                'comparison': comparison
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Vergleich gespeichert: {comparison_file}")
    else:
        print("❌ DRIVE-Werte konnten nicht abgerufen werden")


if __name__ == '__main__':
    main()
