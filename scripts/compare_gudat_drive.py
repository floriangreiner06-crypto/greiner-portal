#!/usr/bin/env python3
"""
Vergleich Gudat Frontend vs. DRIVE Portal
Vergleicht die Team-Kapazitätsdaten für Allgemeine Reparatur und Diagnosetechnik
"""

import requests
import json
from datetime import datetime, timedelta

# Screenshot-Daten (aus Bildbeschreibung)
SCREENSHOT_DATA = {
    "Allgemeine Reparatur": {
        "2026-01-20": 71,   # Di
        "2026-01-21": 120,  # Mi
        "2026-01-22": 117,  # Do
        "2026-01-23": 190,  # Fr
        "2026-01-24": 0,    # Sa
        "2026-01-25": 0,    # So
        "2026-01-26": 185,  # Mo
        "2026-01-27": 168,  # Di
        "2026-01-28": 210,  # Mi
        "2026-01-29": 221,  # Do
        "2026-01-30": 192,  # Fr
        "2026-01-31": 0,    # Sa
        "2026-02-01": 0,    # So
        "2026-02-02": 157,  # Mo
        "2026-02-03": 60,   # Di
    },
    "Diagnosetechnik": {
        "2026-01-20": -66,  # Di
        "2026-01-21": -12,  # Mi
        "2026-01-22": -35,  # Do
        "2026-01-23": 4,    # Fr
        "2026-01-24": 0,    # Sa
        "2026-01-25": 0,    # So
        "2026-01-26": -4,   # Mo
        "2026-01-27": 0,    # Di
        "2026-01-28": -15,  # Mi
        "2026-01-29": 9,    # Do
        "2026-01-30": 3,    # Fr
        "2026-01-31": 0,    # Sa
        "2026-02-01": 0,    # So
        "2026-02-02": 1,    # Mo
        "2026-02-03": 26,   # Di
    }
}

def get_drive_data():
    """Holt Daten aus DRIVE Portal"""
    try:
        # Aktuelle Team-Daten
        response = requests.get('http://localhost:5000/api/gudat/workload', timeout=10)
        if response.status_code != 200:
            return None, f"API Fehler: {response.status_code}"
        
        data = response.json()
        teams = data.get('teams', [])
        
        ar = [t for t in teams if 'Allgemeine Reparatur' in t.get('name', '')]
        dt = [t for t in teams if 'Diagnosetechnik' in t.get('name', '')]
        
        return {
            'Allgemeine Reparatur': ar[0] if ar else None,
            'Diagnosetechnik': dt[0] if dt else None
        }, None
        
    except Exception as e:
        return None, str(e)

def get_drive_week_data():
    """Holt Wochen-Daten aus DRIVE Portal (falls verfügbar)"""
    try:
        # Prüfe ob /api/gudat/workload/raw Team-Daten pro Tag liefert
        response = requests.get('http://localhost:5000/api/gudat/workload/raw?date=2026-01-20&days=15', timeout=10)
        if response.status_code != 200:
            return None, f"API Fehler: {response.status_code}"
        
        data = response.json()
        teams = data.get('teams', [])
        
        # Finde Teams
        ar_team = None
        dt_team = None
        for team in teams:
            name = team.get('name', '')
            if 'Allgemeine Reparatur' in name:
                ar_team = team
            if 'Diagnosetechnik' in name:
                dt_team = team
        
        if not ar_team or not dt_team:
            return None, "Teams nicht gefunden"
        
        # Extrahiere tägliche Daten
        result = {
            'Allgemeine Reparatur': {},
            'Diagnosetechnik': {}
        }
        
        if 'data' in ar_team:
            for date, day_data in ar_team['data'].items():
                result['Allgemeine Reparatur'][date] = day_data.get('free_workload', 0)
        
        if 'data' in dt_team:
            for date, day_data in dt_team['data'].items():
                result['Diagnosetechnik'][date] = day_data.get('free_workload', 0)
        
        return result, None
        
    except Exception as e:
        return None, str(e)

def compare_data():
    """Vergleicht Screenshot-Daten mit DRIVE-Daten"""
    print("=" * 80)
    print("VERGLEICH: Gudat Frontend Screenshot vs. DRIVE Portal")
    print("=" * 80)
    
    # Aktuelle Daten (heute)
    drive_data, error = get_drive_data()
    if error:
        print(f"❌ Fehler beim Abrufen der DRIVE-Daten: {error}")
        return
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\n📅 HEUTE ({today}):")
    print("-" * 80)
    
    for team_name in ["Allgemeine Reparatur", "Diagnosetechnik"]:
        screenshot_value = SCREENSHOT_DATA[team_name].get(today)
        drive_team = drive_data.get(team_name)
        
        if not drive_team:
            print(f"⚠️  {team_name}: Nicht in DRIVE gefunden")
            continue
        
        drive_value = drive_team.get('free', 0)
        
        print(f"\n🔧 {team_name}:")
        print(f"   Screenshot (Gudat): {screenshot_value} AW frei")
        print(f"   DRIVE Portal:       {drive_value} AW frei")
        
        if screenshot_value == drive_value:
            print(f"   ✅ ÜBEREINSTIMMUNG!")
        else:
            diff = abs(screenshot_value - drive_value)
            print(f"   ❌ DIFFERENZ: {diff} AW ({screenshot_value - drive_value:+d})")
    
    # Wochen-Vergleich
    print("\n" + "=" * 80)
    print("WOCHE-VERGLEICH (15 Tage):")
    print("=" * 80)
    
    week_data, week_error = get_drive_week_data()
    if week_error:
        print(f"⚠️  Wochen-Daten nicht verfügbar: {week_error}")
    else:
        print("\n📊 Vergleich Screenshot vs. DRIVE (freie AW pro Tag):")
        print("-" * 80)
        
        all_match = True
        for team_name in ["Allgemeine Reparatur", "Diagnosetechnik"]:
            print(f"\n🔧 {team_name}:")
            screenshot = SCREENSHOT_DATA[team_name]
            drive = week_data.get(team_name, {})
            
            matches = 0
            total = 0
            for date in sorted(screenshot.keys()):
                screenshot_val = screenshot[date]
                drive_val = drive.get(date, None)
                total += 1
                
                if drive_val is None:
                    print(f"   {date}: Screenshot={screenshot_val:4d} | DRIVE=N/A ⚠️")
                    all_match = False
                elif screenshot_val == drive_val:
                    print(f"   {date}: Screenshot={screenshot_val:4d} | DRIVE={drive_val:4d} ✅")
                    matches += 1
                else:
                    diff = screenshot_val - drive_val
                    print(f"   {date}: Screenshot={screenshot_val:4d} | DRIVE={drive_val:4d} ❌ (Diff: {diff:+d})")
                    all_match = False
            
            print(f"\n   Übereinstimmungen: {matches}/{total} ({matches*100//total if total > 0 else 0}%)")
        
        if all_match:
            print("\n✅ ALLE WERTE STIMMEN ÜBEREIN!")
        else:
            print("\n⚠️  Es gibt Abweichungen zwischen Screenshot und DRIVE-Daten.")
    
    print("=" * 80)

if __name__ == '__main__':
    compare_data()
