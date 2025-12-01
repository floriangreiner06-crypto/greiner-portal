#!/usr/bin/env python3
"""
Leasys Cache Update Script - SQLite Version
Holt PKW (Opel + Leapmotor) + E-Nutzfahrzeuge und speichert in SQLite
"""
import sys
import os
import json
import sqlite3
from datetime import datetime

sys.path.insert(0, '/opt/greiner-portal')
DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'

# Master Agreements aus leasys_programme.json
CACHE_CONFIG = [
    # Opel PKW - KM Leasing 36-60 (Standard)
    {'brand': 'OPEL', 'fuel': 'B', 'ma_id': '1000026115'},
    {'brand': 'OPEL', 'fuel': 'D', 'ma_id': '1000026115'},
    {'brand': 'OPEL', 'fuel': 'E', 'ma_id': '1000026115'},
    
    # Opel E-Nutzfahrzeuge - Doppelblitz
    {'brand': 'OPEL', 'fuel': 'E', 'ma_id': '1000023145'},
    
    # Leapmotor
    {'brand': 'LEAPMOTOR', 'fuel': None, 'ma_id': '1000014601'},
]

def save_to_cache(brand, fuel, ma_id, vehicles):
    """Speichert Fahrzeuge in SQLite-Cache."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    data_json = json.dumps(vehicles, ensure_ascii=False)
    
    cursor.execute('''
        INSERT OR REPLACE INTO leasys_vehicle_cache 
        (brand, fuel, ma_id, data, vehicle_count, created_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
    ''', (brand, fuel, ma_id, data_json, len(vehicles)))
    
    conn.commit()
    conn.close()

def update_cache():
    print(f"[{datetime.now()}] Starte Leasys Cache Update (SQLite)...")
    
    try:
        from tools.scrapers.leasys_full_api import LeasysAPI
        api = LeasysAPI()
        
        if not api.authenticate():
            print("FEHLER: Authentifizierung fehlgeschlagen")
            return False
        
        total_count = 0
        
        for config in CACHE_CONFIG:
            brand = config['brand']
            fuel = config['fuel']
            ma_id = config['ma_id']
            
            fuel_name = {'B': 'Benzin', 'D': 'Diesel', 'E': 'Elektro', None: 'Alle'}.get(fuel, fuel)
            print(f"\n{brand} {fuel_name} (MA: {ma_id})...")
            
            vehicles = api.get_vehicles(brand=brand, fuel=fuel, mast_ag_id=ma_id)
            
            save_to_cache(brand, fuel, ma_id, vehicles)
            print(f"  -> {len(vehicles)} Fahrzeuge gespeichert")
            total_count += len(vehicles)
        
        print(f"\n[{datetime.now()}] Cache Update erfolgreich!")
        print(f"Gesamt: {total_count} Fahrzeuge in {len(CACHE_CONFIG)} Cache-Einträgen")
        
        return True
        
    except Exception as e:
        print(f"FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = update_cache()
    sys.exit(0 if success else 1)
