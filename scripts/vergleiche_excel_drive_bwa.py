#!/usr/bin/env python3
"""
Vergleich Excel GlobalCube mit DRIVE BWA
Vergleicht extrahierte Excel-Werte mit DRIVE API-Werten

Erstellt: TAG 184
"""

import json
import requests
from pathlib import Path

EXCEL_JSON = "/opt/greiner-portal/docs/globalcube_analysis/excel_bwa_values_tag184.json"
DRIVE_API_URL = "http://localhost:5000/api/controlling/bwa/v2"


def load_excel_data():
    """Lädt Excel-Daten"""
    if not Path(EXCEL_JSON).exists():
        print(f"❌ Excel JSON nicht gefunden: {EXCEL_JSON}")
        return None
    
    with open(EXCEL_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_drive_bwa(monat=12, jahr=2025, firma='1', standort='2'):
    """Ruft DRIVE BWA-Werte ab"""
    try:
        url = f"{DRIVE_API_URL}?monat={monat}&jahr={jahr}&firma={firma}&standort={standort}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API-Fehler: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Fehler beim API-Aufruf: {e}")
        return None


def interpret_excel_values(excel_data):
    """
    Interpretiert Excel-Werte
    
    Excel-Struktur scheint zu sein:
    - Spalte 1: Position (Text)
    - Spalte 2: Monat Dez./2025 (Wert in Tausenden?)
    - Spalte 3: % (Prozent)
    - Spalte 4: Kumuliert Dez./2025 (Wert)
    - Spalte 5: % (Prozent)
    - Spalte 6: Dez./2024 (Vorjahr Monat)
    - Spalte 7: % (Prozent)
    - Spalte 8: Kumuliert Dez./2024 (Vorjahr)
    - Spalte 9: % (Prozent)
    - Spalte 10: Abw. (Differenz)
    - Spalte 11: % Abw. (Prozent-Differenz)
    """
    interpreted = {}
    
    for key, data in excel_data.items():
        values = data['values']
        
        # Die ersten größeren Zahlen sind wahrscheinlich die Werte
        # Sehr kleine Zahlen (e-05) sind Prozentwerte
        euro_values = [v for v in values if abs(v) > 0.01 and abs(v) < 1e10]
        
        if euro_values:
            # Erste größere Zahl = Monat
            # Zweite größere Zahl = Kumuliert (YTD)
            monat_value = euro_values[0] if len(euro_values) > 0 else None
            ytd_value = euro_values[1] if len(euro_values) > 1 else None
            
            interpreted[key] = {
                'position': data['position'],
                'monat': monat_value,
                'ytd': ytd_value,
                'raw_values': values[:5]  # Erste 5 für Debug
            }
    
    return interpreted


def compare_values(excel_interpreted, drive_data):
    """Vergleicht Excel- mit DRIVE-Werten"""
    print("\n=== Vergleich Excel vs. DRIVE ===\n")
    
    if not drive_data or drive_data.get('status') != 'ok':
        print("❌ DRIVE-Daten nicht verfügbar")
        return
    
    aktuell = drive_data.get('aktuell', {})
    
    # Mapping Excel -> DRIVE
    mapping = {
        'umsatzerlöse': 'umsatz',
        'einsatzwerte': 'einsatz',
        'bruttoertrag': 'db1',
        'variable_kosten': 'variable_kosten',
        'direkte_kosten': 'direkte_kosten',
        'indirekte_kosten': 'indirekte_kosten',
        'betriebsergebnis': 'betriebsergebnis',
    }
    
    print(f"{'Position':<25} | {'Excel (Monat)':>15} | {'DRIVE (Monat)':>15} | {'Differenz':>15} | {'%':>10}")
    print("-" * 90)
    
    for excel_key, drive_key in mapping.items():
        if excel_key in excel_interpreted:
            excel_val = excel_interpreted[excel_key].get('monat')
            drive_val = aktuell.get(drive_key, 0)
            
            if excel_val is not None and drive_val is not None:
                diff = drive_val - excel_val
                diff_pct = (diff / excel_val * 100) if excel_val != 0 else 0
                
                status = "✅" if abs(diff_pct) < 1 else "⚠️" if abs(diff_pct) < 5 else "❌"
                
                print(f"{excel_key:<25} | {excel_val:>15,.2f} | {drive_val:>15,.2f} | {diff:>15,.2f} | {diff_pct:>9.2f}% {status}")
    
    # YTD-Vergleich
    print("\n=== YTD-Vergleich (Kumuliert) ===\n")
    ytd = drive_data.get('ytd', {})
    
    print(f"{'Position':<25} | {'Excel (YTD)':>15} | {'DRIVE (YTD)':>15} | {'Differenz':>15} | {'%':>10}")
    print("-" * 90)
    
    for excel_key, drive_key in mapping.items():
        if excel_key in excel_interpreted:
            excel_val = excel_interpreted[excel_key].get('ytd')
            drive_val = ytd.get(drive_key, 0)
            
            if excel_val is not None and drive_val is not None:
                diff = drive_val - excel_val
                diff_pct = (diff / excel_val * 100) if excel_val != 0 else 0
                
                status = "✅" if abs(diff_pct) < 1 else "⚠️" if abs(diff_pct) < 5 else "❌"
                
                print(f"{excel_key:<25} | {excel_val:>15,.2f} | {drive_val:>15,.2f} | {diff:>15,.2f} | {diff_pct:>9.2f}% {status}")


def main():
    """Hauptfunktion"""
    print("=" * 80)
    print("VERGLEICH EXCEL GLOBALCUBE MIT DRIVE BWA - TAG 184")
    print("=" * 80)
    
    # 1. Lade Excel-Daten
    excel_data = load_excel_data()
    if not excel_data:
        return
    
    print(f"\n✅ Excel-Daten geladen: {len(excel_data)} Positionen")
    
    # 2. Interpretiere Excel-Werte
    excel_interpreted = interpret_excel_values(excel_data)
    print(f"\n✅ Excel-Werte interpretiert: {len(excel_interpreted)} Positionen")
    
    # Zeige interpretierte Werte
    print("\n=== Interpretierte Excel-Werte ===")
    for key, data in excel_interpreted.items():
        print(f"{key}: Monat={data.get('monat')}, YTD={data.get('ytd')}")
    
    # 3. Hole DRIVE-Daten für Landau Dezember 2025
    print("\n=== Hole DRIVE-Daten (Landau, Dez 2025) ===")
    drive_data = get_drive_bwa(monat=12, jahr=2025, firma='1', standort='2')
    
    if drive_data:
        print("✅ DRIVE-Daten geladen")
        
        # 4. Vergleiche
        compare_values(excel_interpreted, drive_data)
    
    print("\n" + "=" * 80)
    print("✅ Vergleich abgeschlossen")
    print("=" * 80)


if __name__ == '__main__':
    main()
